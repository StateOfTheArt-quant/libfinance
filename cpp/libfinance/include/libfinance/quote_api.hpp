// Live quote subscription: the quote gateway (dynamics, protocol v3), as Python's
// libfinance.subscribe.quote_api gives it -- the same QuoteApi / QuoteSpi, methods, callbacks and
// records, codes as everywhere else in libfinance (order_book_id, 600519.XSHG).
//
//   struct Spi : lf::QuoteSpi {
//     lf::QuoteApi* api;
//     void on_rsp_login(const lf::LoginRsp& rsp, int) override {
//       if (rsp.error_id == 0) api->subscribe({"600519.XSHG", "000001.XSHE"});  // replayed after a reconnect
//     }
//     void on_depth_market_data(const lf::Quote& q, const lf::RecordEnvelope&) override {
//       std::cout << q.order_book_id() << " " << q.last_price << "\n";
//     }
//   };
//   lf::QuoteApi api;  Spi spi;  spi.api = &api;
//   api.register_spi(&spi);
//   api.connect();     // no login needed: a ticket from the libfinance server, which also names the gateways
//
// No login is needed: the gateway takes short-lived tickets the libfinance server issues
// (issue_quote_ticket); the client fetches one on connect, on every reconnect and before it expires.
// Not logged in, the caller gets the IP-based quota; logged in (lf::login), the account's.
//
// A lost connection is reopened (the next address when several are given), logged in again and
// resumed from the last record seen, so nothing is lost or repeated; subscribe in on_rsp_login and the
// subscriptions are replayed. Every record carries the gateway's envelope; an inst_seq that skips is
// reported through on_sequence_gap. Callbacks run on the client's reader thread: keep them short.
#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "libfinance/quote_protocol.hpp"
#include "libfinance/types.hpp"

namespace libfinance {

// ---------------------------------------------------------------- the API

//: The callbacks; override what you need. They run on the reader thread; an exception thrown by one
//: is printed, not propagated.
class QuoteSpi {
 public:
  virtual ~QuoteSpi() = default;
  virtual void on_connected() {}
  virtual void on_disconnected(int /*reason*/) {}
  virtual void on_rsp_login(const LoginRsp& /*rsp*/, int /*request_id*/) {}
  virtual void on_rsp_reauth(const LoginRsp& /*rsp*/) {}
  virtual void on_session_closed(const SessionClosed& /*notice*/) {}
  virtual void on_rsp_subscribe(const SubRsp& /*rsp*/, int /*request_id*/) {}
  virtual void on_rsp_unsubscribe(const SubRsp& /*rsp*/, int /*request_id*/) {}
  virtual void on_rsp_subscribe_all(const SubAllRsp& /*rsp*/, int /*request_id*/) {}
  virtual void on_rsp_unsubscribe_all(const SubAllRsp& /*rsp*/, int /*request_id*/) {}
  virtual void on_rsp_query_sources(const std::vector<SourceDirEntry>& /*sources*/, int /*request_id*/) {}
  virtual void on_depth_market_data(const Quote& /*quote*/, const RecordEnvelope& /*envelope*/) {}
  virtual void on_transaction(const Transaction& /*transaction*/, const RecordEnvelope& /*envelope*/) {}
  virtual void on_entrust(const Entrust& /*entrust*/, const RecordEnvelope& /*envelope*/) {}
  virtual void on_tick(const Tick& /*tick*/, const RecordEnvelope& /*envelope*/) {}
  virtual void on_depth(const Depth& /*depth*/, const RecordEnvelope& /*envelope*/) {}
  virtual void on_sequence_gap(const SequenceGap& /*gap*/) {}
  virtual void on_stream_status(const StreamStatus& /*status*/) {}
  virtual void on_heartbeat() {}
};

//: Where a ticket comes from: called on the first login, on every reconnect and before expiry.
using TokenProvider = std::function<std::string()>;

class QuoteApi {
 public:
  explicit QuoteApi(bool auto_reconnect = true, std::string client_id = "libfinance");
  ~QuoteApi();  // disconnects
  QuoteApi(const QuoteApi&) = delete;
  QuoteApi& operator=(const QuoteApi&) = delete;

  //: The callbacks (not owned; must outlive the connection).
  void register_spi(QuoteSpi* spi);

  //: Connect to the gateway: 0 = connected, -1 = not yet (it keeps trying in the background),
  //: -2 = no gateway address (none given, and no ticket naming one): nothing is retried.
  //: `addresses` is "host:port,host:port"; empty = the gateways the libfinance server names with the ticket.
  //: Without login(), tickets come from the libfinance server.
  int connect(const std::string& addresses = "", double timeout_seconds = 3.0);
  //: Your own ticket: a fixed one, or a provider. Without it, the libfinance server issues them.
  int login(const std::string& token);
  int login(TokenProvider provider);

  //: Subscribe these order_book_ids (600519.XSHG; exchanges may be mixed); one on_rsp_subscribe each.
  //: An empty `source` lets the gateway pick by health and priority and fail over; a named one is
  //: directed (that source only). Every code is checked before anything is sent (std::invalid_argument).
  //: Returns the last request's number (0 = between connections; replay in on_rsp_login).
  int subscribe(const Codes& order_book_ids, const std::string& source = "");
  int unsubscribe(const Codes& order_book_ids, const std::string& source = "");
  //: Everything of market x instrument_type x data_type (0 = any); the ticket must grant it (error 8).
  int subscribe_all(MarketType market = MarketType::All, uint64_t instrument_type = SubscribeInstrumentType::All,
                    uint64_t data_type = SubscribeDataType::All);
  //: Drop the whole-market subscriptions (per-code ones stay).
  int unsubscribe_all();
  //: The source directory, through on_rsp_query_sources.
  int query_sources();

  bool connected() const;
  void disconnect();

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace libfinance
