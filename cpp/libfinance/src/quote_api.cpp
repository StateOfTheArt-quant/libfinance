// Python: libfinance/subscribe/quote_api.py -- the same threads, states and recovery: a supervisor
// thread connects, logs in and reads; a heartbeat thread keeps the link alive and drops a silent one.
#include "libfinance/quote_api.hpp"

#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <iostream>
#include <map>
#include <mutex>
#include <set>
#include <stdexcept>
#include <thread>
#include <tuple>

#include "internal.hpp"

namespace libfinance {

namespace qp = quote_protocol;

namespace {

using Clock = std::chrono::steady_clock;

double seconds_since(Clock::time_point then) {
  return std::chrono::duration<double>(Clock::now() - then).count();
}

//: "host:port,host:port" (a port defaults to 9001).
std::vector<std::pair<std::string, int>> parse_addresses(const std::string& addresses) {
  std::vector<std::pair<std::string, int>> out;
  size_t start = 0;
  while (start <= addresses.size()) {
    size_t end = addresses.find(',', start);
    if (end == std::string::npos) end = addresses.size();
    std::string item = addresses.substr(start, end - start);
    item.erase(0, item.find_first_not_of(" \t"));
    item.erase(item.find_last_not_of(" \t") + 1);
    if (!item.empty()) {
      const auto colon = item.rfind(':');
      const std::string port = colon == std::string::npos ? "" : item.substr(colon + 1);
      const bool numeric = !port.empty() && std::all_of(port.begin(), port.end(), ::isdigit);
      out.emplace_back(numeric ? item.substr(0, colon) : item, numeric ? std::stoi(port) : 9001);
    }
    start = end + 1;
  }
  return out;
}

//: Every code checked before anything is sent; duplicates once, in the order given.
std::vector<std::string> checked_all(const Codes& order_book_ids) {
  const auto& codes = order_book_ids.values();
  if (codes.empty()) throw std::invalid_argument("order_book_ids: at least one order book id expected");
  std::vector<std::string> out;
  std::set<std::string> seen;
  for (const auto& code : codes)
    if (seen.insert(code).second) out.push_back(check_order_book_id(code));
  return out;
}

template <typename F>
void safe(const char* name, F&& callback) {
  try {
    callback();
  } catch (const std::exception& error) {
    std::cerr << "[QuoteApi] callback " << name << " raised " << error.what() << "\n";
  } catch (...) {
    std::cerr << "[QuoteApi] callback " << name << " raised\n";
  }
}

}  // namespace

struct QuoteApi::Impl {
  explicit Impl(bool reconnect, std::string id) : auto_reconnect(reconnect), client_id(std::move(id)) {}

  const bool auto_reconnect;
  const std::string client_id;
  std::atomic<QuoteSpi*> spi{nullptr};

  std::vector<std::pair<std::string, int>> endpoints;
  size_t current = 0;
  std::atomic<int> sock{-1};
  std::mutex send_lock;
  std::mutex state_lock;
  std::atomic<bool> stopping{false};
  std::atomic<bool> is_connected{false};
  std::mutex wait_lock;
  std::condition_variable changed;  // connected / stopping
  std::thread supervisor, heartbeat;
  std::atomic<int64_t> last_received{0}, last_sent{0};  // steady-clock ns
  uint32_t seq = 1;

  // login state (state_lock)
  TokenProvider provider;
  bool from_libfinance = false;  // the provider is the libfinance server's issue_quote_ticket
  std::string token;
  bool login_sent = false, login_retried = false, login_blocked = false;

  // resume and gap detection (seq_lock)
  std::mutex seq_lock;
  int64_t epoch = 0;
  std::map<uint32_t, uint64_t> last_seq_by_stream;
  std::map<std::pair<uint64_t, uint16_t>, std::pair<uint32_t, uint64_t>> baselines;  // (key, tag) -> (stream, inst_seq)

  static int64_t now_ns() { return Clock::now().time_since_epoch().count(); }

  // ------------------------------------------------------------ tickets

  //: issue_quote_ticket: {token, gateways}.
  static std::pair<std::string, std::string> libfinance_ticket() {
    const Json ticket = detail::call("issue_quote_ticket", Json::object());
    return {ticket.value("token", std::string()), ticket.value("gateways", std::string())};
  }

  //: A fresh ticket from the provider, kept for the next login; returns the gateways the libfinance server named.
  std::string refresh_token() {
    TokenProvider fixed;
    bool libfinance = false;
    {
      std::lock_guard<std::mutex> lock(state_lock);
      if (!provider && !from_libfinance) return "";
      fixed = provider;
      libfinance = from_libfinance;
    }
    std::string fresh, gateways;
    try {
      if (libfinance) std::tie(fresh, gateways) = libfinance_ticket();
      else fresh = fixed();
    } catch (const RpcError& error) {
      if (error.kind() == "PermissionError") {
        // the server refuses this caller tickets (banned / level too low): no automatic retry, until
        // login() / connect() again
        std::lock_guard<std::mutex> lock(state_lock);
        login_blocked = true;
        std::cerr << "[QuoteApi] quote tickets refused for this caller: " << error.what() << "\n";
      } else {  // not available now (server unreachable...): no login this time, the next reconnect tries again
        std::cerr << "[QuoteApi] cannot obtain a quote ticket: " << error.what() << "\n";
      }
      return "";
    } catch (const std::exception& error) {
      std::cerr << "[QuoteApi] cannot obtain a quote ticket: " << error.what() << "\n";
      return "";
    }
    if (fresh.size() > qp::kMaxTokenBytes) {
      std::cerr << "[QuoteApi] ticket too long, ignored\n";
      return gateways;
    }
    std::lock_guard<std::mutex> lock(state_lock);
    token = std::move(fresh);
    return gateways;
  }

  int send_login() {
    std::string ticket;
    {
      std::lock_guard<std::mutex> lock(state_lock);
      if ((!provider && !from_libfinance) || login_blocked || login_sent || !is_connected) return 0;
      if (token.empty()) return 0;  // no usable ticket (revoked, no new one yet): never log in with an empty one
      login_sent = true;
      ticket = token;
    }
    return send(qp::REQ_LOGIN, qp::pack_login_req(ticket, client_id));
  }

  // ------------------------------------------------------------ the link

  bool open_socket(const std::string& host, int port) {
    addrinfo hints{}, *found = nullptr;
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &found) != 0) return false;
    int fd = -1;
    for (addrinfo* at = found; at && fd < 0; at = at->ai_next) {
      fd = ::socket(at->ai_family, at->ai_socktype, at->ai_protocol);
      if (fd < 0) continue;
      timeval connect_timeout{3, 0};
      setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &connect_timeout, sizeof(connect_timeout));
      if (::connect(fd, at->ai_addr, at->ai_addrlen) != 0) {
        ::close(fd);
        fd = -1;
      }
    }
    freeaddrinfo(found);
    if (fd < 0) return false;
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    timeval read_timeout{1, 0};  // the read loop wakes every second to see whether it should stop
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &read_timeout, sizeof(read_timeout));
    sock = fd;
    last_received = last_sent = now_ns();
    {
      std::lock_guard<std::mutex> lock(wait_lock);
      is_connected = true;
    }
    changed.notify_all();
    return true;
  }

  //: Close the link: only the supervisor, once its read loop has ended (or nobody reads any more).
  //: Under send_lock, so a send never writes to a descriptor number the system has handed out again.
  void close_socket() {
    is_connected = false;
    std::lock_guard<std::mutex> lock(send_lock);
    const int fd = sock.exchange(-1);
    if (fd >= 0) {
      ::shutdown(fd, SHUT_RDWR);
      ::close(fd);
    }
  }

  //: Drop the link from another thread: shutdown wakes the reader, which ends its loop; the supervisor
  //: then closes the descriptor (closing it here could hand its number to another socket mid-read).
  void interrupt() {
    is_connected = false;
    std::lock_guard<std::mutex> lock(send_lock);
    const int fd = sock;
    if (fd >= 0) ::shutdown(fd, SHUT_RDWR);
  }

  uint32_t next_seq() {
    std::lock_guard<std::mutex> lock(state_lock);
    return seq++;
  }

  int send(uint16_t msg_type, const std::string& body = "") {
    const uint32_t number = next_seq();
    const std::string frame = qp::make_frame(msg_type, number, body);
    std::lock_guard<std::mutex> lock(send_lock);
    const int fd = sock;
    if (fd < 0) return 0;  // between connections: dropped; on_rsp_login replays subscriptions
    size_t done = 0;
    while (done < frame.size()) {
      const ssize_t n = ::send(fd, frame.data() + done, frame.size() - done, MSG_NOSIGNAL);
      if (n <= 0) return 0;
      done += static_cast<size_t>(n);
    }
    last_sent = now_ns();
    return static_cast<int>(number);
  }

  //: n bytes, or nullopt when the link closed or stopping.
  std::optional<std::string> recv_exact(size_t n) {
    std::string buffer(n, '\0');
    size_t got = 0;
    while (got < n) {
      const int fd = sock;
      if (fd < 0 || stopping) return std::nullopt;
      const ssize_t r = ::recv(fd, &buffer[got], n - got, 0);
      if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) continue;
      if (r <= 0) return std::nullopt;
      got += static_cast<size_t>(r);
    }
    return buffer;
  }

  void read_loop() {
    while (!stopping) {
      const auto head = recv_exact(qp::kHeaderSize);
      if (!head) return;
      const auto header = qp::unpack_header(*head);
      if (header.magic != qp::kMagic || header.version != qp::kVersion || header.body_len > qp::kMaxBodyLen) {
        std::cerr << "[QuoteApi] bad frame: magic=0x" << std::hex << header.magic << std::dec
                  << " version=" << header.version << " body_len=" << header.body_len << "\n";
        return;
      }
      std::string body;
      if (header.body_len) {
        auto read = recv_exact(header.body_len);
        if (!read) return;
        body = std::move(*read);
      }
      last_received = now_ns();
      try {
        dispatch(header.msg_type, header.seq_no, body);
      } catch (const std::out_of_range& error) {  // a frame shorter than its layout: skip it, keep the link
        std::cerr << "[QuoteApi] malformed frame 0x" << std::hex << header.msg_type << std::dec << ": "
                  << error.what() << "\n";
      }
    }
  }

  void wait_stop(double seconds) {
    std::unique_lock<std::mutex> lock(wait_lock);
    changed.wait_for(lock, std::chrono::duration<double>(seconds), [this] { return stopping.load(); });
  }

  void supervise() {
    double backoff = 0.2;
    size_t failures = 0;
    while (!stopping) {
      const auto& [host, port] = endpoints[current % endpoints.size()];
      if (!open_socket(host, port)) {
        ++current;
        if (++failures >= endpoints.size()) {  // only a whole round that fails backs off
          failures = 0;
          wait_stop(backoff);
          backoff = std::min(backoff * 2, endpoints.size() > 1 ? 1.0 : 5.0);
        }
        continue;
      }
      failures = 0;
      const auto connected_at = Clock::now();
      bool blocked;
      {
        std::lock_guard<std::mutex> lock(state_lock);
        login_sent = login_retried = false;
        blocked = login_blocked;
      }
      if (QuoteSpi* s = spi) safe("on_connected", [&] { s->on_connected(); });
      if (!blocked) {
        refresh_token();
        send_login();
      }
      read_loop();
      close_socket();
      if (stopping) return;
      if (QuoteSpi* s = spi) safe("on_disconnected", [&] { s->on_disconnected(0); });
      if (!auto_reconnect) return;
      if (seconds_since(connected_at) >= 10) backoff = 0.2;
      if (endpoints.size() > 1) {
        ++current;  // another address: switch at once
      } else {
        wait_stop(backoff);
        backoff = std::min(backoff * 2, 5.0);
      }
    }
  }

  void keep_alive() {
    while (!stopping) {
      wait_stop(1.0);
      if (stopping) return;
      if (!is_connected) continue;
      const double silent = (now_ns() - last_received) / 1e9, idle = (now_ns() - last_sent) / 1e9;
      if (silent > qp::kHeartbeatTimeout) {
        std::cerr << "[QuoteApi] no frame from the gateway for " << qp::kHeartbeatTimeout << "s, reconnecting\n";
        interrupt();  // the read loop ends, the supervisor closes and reconnects
      } else if (idle >= qp::kHeartbeatInterval) {
        send(qp::HEARTBEAT);
      }
    }
  }

  // ------------------------------------------------------------ frames in

  void dispatch(uint16_t msg_type, uint32_t seq_no, const std::string& body) {
    QuoteSpi* s = spi;
    const int request = static_cast<int>(seq_no);
    switch (msg_type) {
      case qp::RECORD_BATCH:
        if (s) dispatch_batch(body, *s);
        return;
      case qp::RSP_LOGIN:
        on_login(qp::unpack_login_rsp(body), request, s);
        return;
      case qp::RSP_REAUTH:
        if (s) safe("on_rsp_reauth", [&] { s->on_rsp_reauth(qp::unpack_login_rsp(body)); });
        return;
      case qp::NOTIFY_SESSION_EXPIRING: {  // a new ticket renews the session; subscriptions stay
        refresh_token();
        std::string ticket;
        {
          std::lock_guard<std::mutex> lock(state_lock);
          ticket = token;
        }
        send(qp::REQ_REAUTH, qp::pack_reauth_req(ticket));
        return;
      }
      case qp::NOTIFY_SESSION_CLOSED: {
        const auto notice = qp::unpack_session_closed(body);
        if (notice.reason == 2) {
          // the ticket was revoked (a ban, or a changed grant the client should pick up): drop it; the gateway
          // disconnects, the reconnect takes a new ticket, logs in and replays the subscriptions in
          // on_rsp_login. A banned caller is refused a ticket (PermissionError) and stops there; a fixed
          // ticket of the caller's own is refused as revoked by the gateway and stops too.
          std::lock_guard<std::mutex> lock(state_lock);
          token.clear();
        }
        if (s) safe("on_session_closed", [&] { s->on_session_closed(notice); });
        return;
      }
      default:
        break;
    }
    if (!s) return;
    switch (msg_type) {
      case qp::RSP_SUBSCRIBE:
        safe("on_rsp_subscribe", [&] { s->on_rsp_subscribe(qp::unpack_sub_rsp(body), request); });
        break;
      case qp::RSP_UNSUBSCRIBE: {
        const auto rsp = qp::unpack_sub_rsp(body);
        if (rsp.error_id == static_cast<int32_t>(QuoteError::GrantShrunk))  // revoked by the gateway: no more records
          forget_baseline(instrument_hash(rsp.order_book_id));
        safe("on_rsp_unsubscribe", [&] { s->on_rsp_unsubscribe(rsp, request); });
        break;
      }
      case qp::RSP_SUBSCRIBE_ALL:
        safe("on_rsp_subscribe_all", [&] { s->on_rsp_subscribe_all(qp::unpack_sub_all_rsp(body), request); });
        break;
      case qp::RSP_UNSUBSCRIBE_ALL:
        safe("on_rsp_unsubscribe_all", [&] { s->on_rsp_unsubscribe_all(qp::unpack_sub_all_rsp(body), request); });
        break;
      case qp::RSP_QUERY_SOURCES:
        safe("on_rsp_query_sources", [&] { s->on_rsp_query_sources(qp::unpack_source_dir_list(body), request); });
        break;
      case qp::STREAM_STATUS:
        safe("on_stream_status", [&] { s->on_stream_status(qp::unpack_stream_status(body)); });
        break;
      case qp::HEARTBEAT:
        safe("on_heartbeat", [&] { s->on_heartbeat(); });
        break;
      default:
        break;  // frames a newer gateway may add: skipped, not a reason to disconnect
    }
  }

  void on_login(const LoginRsp& rsp, int request, QuoteSpi* s) {
    if (rsp.error_id != 0) {
      bool retry = false;
      {
        std::lock_guard<std::mutex> lock(state_lock);
        const auto error = static_cast<QuoteError>(rsp.error_id);
        if ((error == QuoteError::TokenExpired || error == QuoteError::TokenUnknownKey) && !login_retried) {
          login_retried = true;
          login_sent = false;
          retry = true;
        } else if (error != QuoteError::AlreadyAuthenticated) {
          login_blocked = true;  // no automatic retry: until login() / connect() again
        }
      }
      if (retry) {
        refresh_token();
        send_login();
        return;
      }
    }
    bool resuming = false;
    if (rsp.error_id == 0) {
      std::vector<std::pair<uint32_t, uint64_t>> positions;
      {
        std::lock_guard<std::mutex> lock(seq_lock);
        if (epoch != rsp.sequence_epoch_ns) {  // the gateway rebuilt its log: positions and baselines are void
          epoch = rsp.sequence_epoch_ns;
          last_seq_by_stream.clear();
          baselines.clear();
        }
        positions.assign(last_seq_by_stream.begin(), last_seq_by_stream.end());
      }
      if (!positions.empty()) {
        send(qp::REQ_RESUME, qp::pack_resume_positions(positions));
        resuming = true;
      }
    }
    if (s) safe("on_rsp_login", [&] { s->on_rsp_login(rsp, request); });  // where callers subscribe again
    if (resuming) send(qp::REQ_RESUME_START);
  }

  void forget_baseline(uint64_t instrument_key) {
    std::lock_guard<std::mutex> lock(seq_lock);
    for (auto it = baselines.begin(); it != baselines.end();)
      it = it->first.first == instrument_key ? baselines.erase(it) : std::next(it);
  }

  template <typename Record>
  std::optional<SequenceGap> check_sequence(const RecordEnvelope& env, const Record& record) {
    std::lock_guard<std::mutex> lock(seq_lock);
    if (!env.snapshot()) {  // a snapshot does not mean everything before it arrived: no resume position
      auto& last = last_seq_by_stream[env.stream_id];
      last = std::max(last, env.seq);
    }
    const auto key = std::make_pair(env.instrument_key, env.tag);
    const auto previous = baselines.find(key);
    std::optional<std::pair<uint32_t, uint64_t>> before;
    if (previous != baselines.end()) before = previous->second;
    baselines[key] = {env.stream_id, env.inst_seq};
    if (!before || env.snapshot()) return std::nullopt;
    if (before->first == env.stream_id && env.inst_seq > before->second + 1) {
      SequenceGap gap;
      gap.stream_id = env.stream_id;
      gap.tag = env.tag;
      gap.order_book_id = record.order_book_id;
      gap.expected_inst_seq = before->second + 1;
      gap.received_inst_seq = env.inst_seq;
      return gap;
    }
    return std::nullopt;
  }

  template <typename Record, typename Callback>
  void deliver(QuoteSpi& s, const RecordEnvelope& env, const Record& record, const char* name, Callback&& callback) {
    if (const auto gap = check_sequence(env, record)) safe("on_sequence_gap", [&] { s.on_sequence_gap(*gap); });
    safe(name, [&] { callback(record, env); });
  }

  void dispatch_batch(const std::string& body, QuoteSpi& s) {
    for (const auto& [env, pod] : qp::iter_batch(body)) {
      const size_t size = qp::record_size(env.tag);
      if (size == 0 || pod.size() < size) continue;  // a kind a newer gateway added
      switch (static_cast<RecordTag>(env.tag)) {
        case RecordTag::Quote:
          deliver(s, env, qp::unpack_quote(pod), "on_depth_market_data",
                  [&](const Quote& r, const RecordEnvelope& e) { s.on_depth_market_data(r, e); });
          break;
        case RecordTag::Transaction:
          deliver(s, env, qp::unpack_transaction(pod), "on_transaction",
                  [&](const Transaction& r, const RecordEnvelope& e) { s.on_transaction(r, e); });
          break;
        case RecordTag::Entrust:
          deliver(s, env, qp::unpack_entrust(pod), "on_entrust",
                  [&](const Entrust& r, const RecordEnvelope& e) { s.on_entrust(r, e); });
          break;
        case RecordTag::Tick:
          deliver(s, env, qp::unpack_tick(pod), "on_tick",
                  [&](const Tick& r, const RecordEnvelope& e) { s.on_tick(r, e); });
          break;
        case RecordTag::Depth:
          deliver(s, env, qp::unpack_depth(pod), "on_depth",
                  [&](const Depth& r, const RecordEnvelope& e) { s.on_depth(r, e); });
          break;
      }
    }
  }
};

// ---------------------------------------------------------------- QuoteApi

QuoteApi::QuoteApi(bool auto_reconnect, std::string client_id)
    : impl_(std::make_unique<Impl>(auto_reconnect, std::move(client_id))) {}

QuoteApi::~QuoteApi() { disconnect(); }

void QuoteApi::register_spi(QuoteSpi* spi) { impl_->spi = spi; }

int QuoteApi::connect(const std::string& addresses, double timeout_seconds) {
  Impl& d = *impl_;
  {
    std::lock_guard<std::mutex> lock(d.state_lock);
    if (!d.provider && !d.from_libfinance) {
      d.from_libfinance = true;
      d.login_blocked = false;
    }
  }
  std::string where = addresses;
  if (where.empty()) where = d.refresh_token();
  d.endpoints = parse_addresses(where);
  if (d.endpoints.empty()) {
    std::cerr << "[QuoteApi] no gateway address (pass connect(\"host:port\") or configure live_quote.gateways)\n";
    return -2;
  }
  if (!d.supervisor.joinable()) {
    d.stopping = false;
    d.supervisor = std::thread([&d] { d.supervise(); });
    d.heartbeat = std::thread([&d] { d.keep_alive(); });
  }
  std::unique_lock<std::mutex> lock(d.wait_lock);
  return d.changed.wait_for(lock, std::chrono::duration<double>(timeout_seconds),
                            [&d] { return d.is_connected.load(); })
             ? 0
             : -1;
}

int QuoteApi::login(const std::string& token) {
  return login(TokenProvider([token] { return token; }));
}

int QuoteApi::login(TokenProvider provider) {
  Impl& d = *impl_;
  {
    std::lock_guard<std::mutex> lock(d.state_lock);
    d.provider = std::move(provider);
    d.from_libfinance = !d.provider;  // an empty provider: the libfinance server's tickets
    d.login_blocked = false;
    d.login_sent = false;
  }
  d.refresh_token();
  return d.send_login();
}

int QuoteApi::subscribe(const Codes& order_book_ids, const std::string& source) {
  int last = 0;
  for (const auto& order_book_id : checked_all(order_book_ids))
    last = impl_->send(qp::REQ_SUBSCRIBE, qp::pack_sub_req(order_book_id, source));
  return last;
}

int QuoteApi::unsubscribe(const Codes& order_book_ids, const std::string& source) {
  int last = 0;
  for (const auto& order_book_id : checked_all(order_book_ids)) {
    impl_->forget_baseline(instrument_hash(order_book_id));
    last = impl_->send(qp::REQ_UNSUBSCRIBE, qp::pack_sub_req(order_book_id, source));
  }
  return last;
}

int QuoteApi::subscribe_all(MarketType market, uint64_t instrument_type, uint64_t data_type) {
  return impl_->send(qp::REQ_SUBSCRIBE_ALL, qp::pack_sub_all_req(market, instrument_type, data_type));
}

int QuoteApi::unsubscribe_all() {
  {
    std::lock_guard<std::mutex> lock(impl_->seq_lock);
    impl_->baselines.clear();
  }
  return impl_->send(qp::REQ_UNSUBSCRIBE_ALL);
}

int QuoteApi::query_sources() { return impl_->send(qp::QUERY_SOURCES); }

bool QuoteApi::connected() const { return impl_->is_connected; }

void QuoteApi::disconnect() {
  Impl& d = *impl_;
  {
    std::lock_guard<std::mutex> lock(d.wait_lock);
    d.stopping = true;
  }
  d.changed.notify_all();
  d.interrupt();
  for (auto* thread : {&d.supervisor, &d.heartbeat}) {
    if (!thread->joinable()) continue;
    if (thread->get_id() == std::this_thread::get_id()) thread->detach();  // called from a callback: it ends on its own
    else thread->join();
  }
  if (!d.supervisor.joinable()) d.close_socket();  // nobody reads any more
}

}  // namespace libfinance
