// Python: libfinance/subscribe/md_protocol.py. Each layout below is that module's struct format,
// field for field; little-endian, packed.
#include "libfinance/quote_protocol.hpp"

#include <cstring>
#include <stdexcept>

namespace libfinance {

namespace {

constexpr size_t kSourceLen = 16;
constexpr size_t kOrderBookIdLen = 48;  // protocol v4: <code>.<exchange>, with its terminating '\0'

//: Little-endian writer (the host is little-endian, as the server is: x86-64 / aarch64).
class Writer {
 public:
  template <typename T>
  Writer& put(T value) {
    char raw[sizeof(T)];
    std::memcpy(raw, &value, sizeof(T));
    out_.append(raw, sizeof(T));
    return *this;
  }
  //: A fixed char[n]: truncated to n - 1 bytes, zero-padded (md_protocol._fix).
  Writer& fixed(const std::string& text, size_t n) {
    const size_t used = std::min(text.size(), n - 1);
    out_.append(text, 0, used);
    out_.append(n - used, '\0');
    return *this;
  }
  Writer& pad(size_t n) {
    out_.append(n, '\0');
    return *this;
  }
  Writer& bytes(const std::string& raw) {
    out_ += raw;
    return *this;
  }
  const std::string& str() const { return out_; }

 private:
  std::string out_;
};

//: Little-endian reader over a body; reading past the end throws std::out_of_range.
class Reader {
 public:
  explicit Reader(const std::string& data, size_t offset = 0) : data_(data), at_(offset) {}
  template <typename T>
  T get() {
    need(sizeof(T));
    T value;
    std::memcpy(&value, data_.data() + at_, sizeof(T));
    at_ += sizeof(T);
    return value;
  }
  //: A fixed char[n], cut at the first '\0' (md_protocol._s).
  std::string fixed(size_t n) {
    need(n);
    const char* begin = data_.data() + at_;
    at_ += n;
    return std::string(begin, strnlen(begin, n));
  }
  void skip(size_t n) {
    need(n);
    at_ += n;
  }
  size_t at() const { return at_; }

 private:
  void need(size_t n) const {
    if (at_ + n > data_.size()) throw std::out_of_range("quote frame shorter than its layout");
  }
  const std::string& data_;
  size_t at_;
};

//: The common head of every record: data_time, order_book_id[48].
template <typename Record>
void head(Reader& in, Record& record) {
  record.data_time = in.get<int64_t>();
  record.order_book_id = in.fixed(kOrderBookIdLen);
}

}  // namespace

// ---------------------------------------------------------------- codes

const std::vector<std::string>& quote_exchanges() {
  // md_protocol.EXCHANGE_OF_MARKET's values
  static const std::vector<std::string> exchanges = {"CCFX", "XBSE", "XDCE", "XINE", "XSGE", "XSHE", "XSHG", "XZCE"};
  return exchanges;
}

const std::string& check_order_book_id(const std::string& order_book_id) {
  const auto dot = order_book_id.rfind('.');
  if (dot == std::string::npos || dot == 0 || dot + 1 == order_book_id.size())
    throw std::invalid_argument("'" + order_book_id + "' is not <code>.<exchange>, e.g. 600519.XSHG");
  const std::string code = order_book_id.substr(0, dot), exchange = order_book_id.substr(dot + 1);
  bool served = false;
  for (const auto& known : quote_exchanges()) served = served || known == exchange;
  if (!served) {
    std::string list;
    for (const auto& known : quote_exchanges()) list += (list.empty() ? "'" : ", '") + known + "'";
    throw std::invalid_argument("'" + order_book_id + "': the quote gateway serves [" + list + "] only");
  }
  if (order_book_id.size() >= kOrderBookIdLen)
    throw std::invalid_argument("'" + order_book_id + "': longer than the gateway takes");
  return order_book_id;
}

uint64_t instrument_hash(const std::string& order_book_id) {
  uint64_t hash = 14695981039346656037ull;
  for (unsigned char c : order_book_id) {
    hash ^= c;
    hash *= 1099511628211ull;
  }
  return hash;
}

namespace quote_protocol {

// ---------------------------------------------------------------- frames

std::string make_frame(uint16_t msg_type, uint32_t seq_no, const std::string& body) {
  // "<IHHII"
  return Writer()
      .put<uint32_t>(kMagic)
      .put<uint16_t>(kVersion)
      .put<uint16_t>(msg_type)
      .put<uint32_t>(seq_no)
      .put<uint32_t>(static_cast<uint32_t>(body.size()))
      .bytes(body)
      .str();
}

FrameHeader unpack_header(const std::string& data) {
  Reader in(data);
  FrameHeader header;
  header.magic = in.get<uint32_t>();
  header.version = in.get<uint16_t>();
  header.msg_type = in.get<uint16_t>();
  header.seq_no = in.get<uint32_t>();
  header.body_len = in.get<uint32_t>();
  return header;
}

std::string pack_login_req(const std::string& token, const std::string& client_id) {
  // "<32sII" + token
  return Writer().fixed(client_id, 32).put<uint32_t>(static_cast<uint32_t>(token.size())).put<uint32_t>(0).bytes(token).str();
}

std::string pack_reauth_req(const std::string& token) {
  // "<II" + token
  return Writer().put<uint32_t>(static_cast<uint32_t>(token.size())).put<uint32_t>(0).bytes(token).str();
}

std::string pack_sub_req(const std::string& order_book_id, const std::string& source) {
  // "<16s48s": source, order_book_id
  return Writer().fixed(source, kSourceLen).fixed(order_book_id, kOrderBookIdLen).str();
}

std::string pack_sub_all_req(MarketType market, uint64_t instrument_type, uint64_t data_type) {
  // "<b7xQQ"
  return Writer().put<int8_t>(static_cast<int8_t>(market)).pad(7).put<uint64_t>(instrument_type).put<uint64_t>(data_type).str();
}

std::string pack_resume_positions(const std::vector<std::pair<uint32_t, uint64_t>>& positions) {
  // uint32 count + count x "<IIQ"
  Writer out;
  out.put<uint32_t>(static_cast<uint32_t>(positions.size()));
  for (const auto& [stream_id, seq] : positions) out.put<uint32_t>(stream_id).put<uint32_t>(0).put<uint64_t>(seq);
  return out.str();
}

// ---------------------------------------------------------------- responses

LoginRsp unpack_login_rsp(const std::string& body) {
  // "<i64sQqiiiB3xQq"
  Reader in(body);
  LoginRsp rsp;
  rsp.error_id = in.get<int32_t>();
  rsp.error_msg = in.fixed(64);
  rsp.session_id = in.get<uint64_t>();
  rsp.expires_at_ms = in.get<int64_t>();
  rsp.max_subscriptions = in.get<int32_t>();
  rsp.max_conns = in.get<int32_t>();
  rsp.max_msgs_per_sec = in.get<int32_t>();
  rsp.sub_all = in.get<uint8_t>() != 0;
  in.skip(3);
  rsp.market_mask = in.get<uint64_t>();
  rsp.sequence_epoch_ns = in.get<int64_t>();
  return rsp;
}

SessionClosed unpack_session_closed(const std::string& body) {
  // "<i64s"
  Reader in(body);
  SessionClosed notice;
  notice.reason = in.get<int32_t>();
  notice.message = in.fixed(64);
  return notice;
}

SubRsp unpack_sub_rsp(const std::string& body) {
  // "<16s48si64sii"
  Reader in(body);
  SubRsp rsp;
  rsp.source = in.fixed(kSourceLen);
  rsp.order_book_id = in.fixed(kOrderBookIdLen);
  rsp.error_id = in.get<int32_t>();
  rsp.error_msg = in.fixed(64);
  rsp.current_subs = in.get<int32_t>();
  rsp.max_subs = in.get<int32_t>();
  return rsp;
}

SubAllRsp unpack_sub_all_rsp(const std::string& body) {
  // "<16si64s"
  Reader in(body);
  SubAllRsp rsp;
  rsp.source = in.fixed(kSourceLen);
  rsp.error_id = in.get<int32_t>();
  rsp.error_msg = in.fixed(64);
  return rsp;
}

std::vector<SourceDirEntry> unpack_source_dir_list(const std::string& body) {
  // uint32 count + count x "<16siBBBxQQQ" (48 bytes); an incomplete frame is dropped
  std::vector<SourceDirEntry> out;
  if (body.size() < 4) return out;
  Reader in(body);
  const auto count = in.get<uint32_t>();
  if (body.size() < 4 + static_cast<size_t>(count) * 48) return out;
  for (uint32_t i = 0; i < count; ++i) {
    SourceDirEntry entry;
    entry.source = in.fixed(kSourceLen);
    entry.priority = in.get<int32_t>();
    entry.whole_market = in.get<uint8_t>() != 0;
    entry.health = in.get<uint8_t>() != 0;
    entry.directed_only = in.get<uint8_t>() != 0;
    in.skip(1);
    entry.market_mask = in.get<uint64_t>();
    entry.instrument_mask = in.get<uint64_t>();
    entry.data_type_mask = in.get<uint64_t>();
    out.push_back(std::move(entry));
  }
  return out;
}

StreamStatus unpack_stream_status(const std::string& body) {
  // "<IB3x16sq": the byte is 1 when the source is stale
  Reader in(body);
  StreamStatus status;
  status.stream_id = in.get<uint32_t>();
  status.stale = in.get<uint8_t>() == 1;
  in.skip(3);
  status.source = in.fixed(kSourceLen);
  status.last_received_ns = in.get<int64_t>();
  return status;
}

// ---------------------------------------------------------------- records

std::vector<BatchRecord> iter_batch(const std::string& body) {
  // "<II" count, pad; then count x (envelope "<IHHIIQQQqq" (56) + record + padding to 8)
  std::vector<BatchRecord> out;
  if (body.size() < 8) return out;
  Reader batch(body);
  const auto count = batch.get<uint32_t>();
  size_t at = 8;
  for (uint32_t i = 0; i < count; ++i) {
    if (body.size() - at < 56) break;
    Reader in(body, at);
    BatchRecord record;
    auto& env = record.envelope;
    env.stream_id = in.get<uint32_t>();
    env.tag = in.get<uint16_t>();
    const auto length = in.get<uint16_t>();
    env.flags = in.get<uint32_t>();
    in.skip(4);
    env.seq = in.get<uint64_t>();
    env.inst_seq = in.get<uint64_t>();
    env.instrument_key = in.get<uint64_t>();
    env.received_ns = in.get<int64_t>();
    env.sequenced_ns = in.get<int64_t>();
    const size_t entry = (56 + static_cast<size_t>(length) + 7) & ~static_cast<size_t>(7);
    if (body.size() - at < entry) break;
    record.pod = body.substr(at + 56, length);
    out.push_back(std::move(record));
    at += entry;
  }
  return out;
}

size_t record_size(uint16_t tag) {
  switch (static_cast<RecordTag>(tag)) {
    case RecordTag::Quote: return 528;
    case RecordTag::Entrust: return 106;
    case RecordTag::Transaction: return 114;
    case RecordTag::Tick: return 88;
    case RecordTag::Depth: return 73;
  }
  return 0;
}

Quote unpack_quote(const std::string& pod) {
  // "<q32s16sb" + 17d + q + 40d + 8s
  Reader in(pod);
  Quote q;
  head(in, q);
  for (double* field : {&q.pre_close_price, &q.pre_settlement_price, &q.last_price, &q.volume, &q.turnover,
                        &q.pre_open_interest, &q.open_interest, &q.open_price, &q.high_price, &q.low_price,
                        &q.upper_limit_price, &q.lower_limit_price, &q.close_price, &q.settlement_price, &q.iopv,
                        &q.total_bid_volume, &q.total_ask_volume})
    *field = in.get<double>();
  q.total_trade_num = in.get<int64_t>();
  for (auto* levels : {&q.bid_price, &q.ask_price, &q.bid_volume, &q.ask_volume})
    for (double& level : *levels) level = in.get<double>();
  q.trading_phase_code = in.fixed(8);
  return q;
}

Entrust unpack_entrust(const std::string& pod) {
  // "<q32s16sbddbbqqqq"
  Reader in(pod);
  Entrust e;
  head(in, e);
  e.price = in.get<double>();
  e.volume = in.get<double>();
  e.side = in.get<int8_t>();
  e.price_type = in.get<int8_t>();
  e.main_seq = in.get<int64_t>();
  e.seq = in.get<int64_t>();
  e.orig_order_no = in.get<int64_t>();
  e.biz_index = in.get<int64_t>();
  return e;
}

Transaction unpack_transaction(const std::string& pod) {
  // "<q32s16sbddqqbbqqq"
  Reader in(pod);
  Transaction t;
  head(in, t);
  t.price = in.get<double>();
  t.volume = in.get<double>();
  t.bid_no = in.get<int64_t>();
  t.ask_no = in.get<int64_t>();
  t.exec_type = in.get<int8_t>();
  t.side = in.get<int8_t>();
  t.main_seq = in.get<int64_t>();
  t.seq = in.get<int64_t>();
  t.biz_index = in.get<int64_t>();
  return t;
}

Tick unpack_tick(const std::string& pod) {
  // "<q32s16sbdddd"
  Reader in(pod);
  Tick t;
  head(in, t);
  t.bid_price = in.get<double>();
  t.bid_volume = in.get<double>();
  t.ask_price = in.get<double>();
  t.ask_volume = in.get<double>();
  return t;
}

Depth unpack_depth(const std::string& pod) {
  // "<q32s16sbddb"
  Reader in(pod);
  Depth d;
  head(in, d);
  d.price = in.get<double>();
  d.volume = in.get<double>();
  d.side = in.get<int8_t>();
  return d;
}

}  // namespace quote_protocol
}  // namespace libfinance
