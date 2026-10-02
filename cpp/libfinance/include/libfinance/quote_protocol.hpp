// The quote gateway's wire protocol (dynamics, v3): Python's libfinance.subscribe.md_protocol.
//
// Frames are a 16-byte FrameHeader and a body: control frames (0xF0xx) carry the structs below,
// data comes only as RECORD_BATCH = RecordBatchHeader + N x (RecordEnvelope + record + padding to 8).
// Every layout is the server's #pragma pack(1) struct, little-endian; the sizes are checked by
// test_quote_protocol against what the Python client packs.
#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace libfinance {


// ---------------------------------------------------------------- enums (dynamics schema/enums.h)

//: Response error_id (md_protocol.ErrorCode).
enum class QuoteError : int32_t {
  Ok = 0,
  Malformed = 1,
  NotAuthenticated = 3,
  NoSource = 4,                // no healthy source / none can take the whole market
  SourceUnavailable = 5,       // the named source is unavailable, or the route conflicts
  SubscriptionLimit = 6,       // the ticket's subscription limit is reached
  MarketNotGranted = 7,
  WholeMarketNotGranted = 8,
  GrantShrunk = 9,             // revoked by the gateway after a renewal narrowed the grant
  TokenInvalid = 20,
  TokenExpired = 21,
  TokenUnknownKey = 22,
  TokenRevoked = 23,
  TooManyConnections = 24,
  SubjectMismatch = 25,
  AlreadyAuthenticated = 26,
};

enum class MarketType : int8_t { All = 0, BSE = 1, SHFE = 2, CFFEX = 3, DCE = 4, CZCE = 5, INE = 6, SSE = 7, SZE = 8 };

//: Bits of subscribe_all's instrument_type (0 = every kind).
namespace SubscribeInstrumentType {
constexpr uint64_t All = 0x00, Stock = 0x01, Future = 0x02, Bond = 0x04, StockOption = 0x08, FutureOption = 0x10,
                   Fund = 0x20, Index = 0x40, HKT = 0x80;
}
//: Bits of subscribe_all's data_type (0 = every kind).
namespace SubscribeDataType {
constexpr uint64_t All = 0x00, Snapshot = 0x01, Entrust = 0x02, Transaction = 0x04, Tree = 0x08, Tick = 0x16,
                   Depth = 0x32;
}

enum class RecordTag : uint16_t { Quote = 401, Entrust = 402, Transaction = 403, Depth = 405, Tick = 406 };

// ---------------------------------------------------------------- responses

//: RSP_LOGIN / RSP_REAUTH: the grant the ticket carries (resource numbers, no levels).
struct LoginRsp {
  int32_t error_id = 0;
  std::string error_msg;
  uint64_t session_id = 0;
  int64_t expires_at_ms = 0;      // the ticket's expiry (renewed before it, automatically)
  int32_t max_subscriptions = 0;  // -1 = unlimited
  int32_t max_conns = 0;
  int32_t max_msgs_per_sec = 0;
  bool sub_all = false;           // may subscribe the whole market
  uint64_t market_mask = 0;       // bit(MarketType)
  int64_t sequence_epoch_ns = 0;  // a change means the gateway rebuilt its log: resume positions are void
};

//: A code (instrument_id) and its exchange as one order_book_id: 600519 + XSHG -> 600519.XSHG.
struct Coded {
  std::string instrument_id;
  std::string exchange_id;
  std::string order_book_id() const { return instrument_id.empty() ? "" : instrument_id + "." + exchange_id; }
};

//: RSP_SUBSCRIBE / RSP_UNSUBSCRIBE, one per order_book_id.
struct SubRsp : Coded {
  std::string source;             // echoed: the source the gateway chose for a subscription without one
  int32_t error_id = 0;
  std::string error_msg;
  int32_t current_subs = 0;
  int32_t max_subs = 0;
};

//: RSP_SUBSCRIBE_ALL / RSP_UNSUBSCRIBE_ALL.
struct SubAllRsp {
  std::string source;             // the source carrying the whole market (empty on failure or unsubscribe)
  int32_t error_id = 0;
  std::string error_msg;
};

//: One entry of the source directory (query_sources).
struct SourceDirEntry {
  std::string source;
  int32_t priority = 0;           // the larger is preferred
  bool whole_market = false;
  bool health = false;            // true = ready to be chosen
  bool directed_only = false;     // only for directed subscriptions: never chosen automatically
  uint64_t market_mask = 0;       // 0 = any
  uint64_t instrument_mask = 0;
  uint64_t data_type_mask = 0;
};

struct StreamStatus {
  uint32_t stream_id = 0;
  bool stale = false;             // true = the source has no new data within trading hours
  std::string source;
  int64_t last_received_ns = 0;
};

struct SessionClosed {
  int32_t reason = 0;             // 1 = expired, 2 = revoked (no automatic login afterwards)
  std::string message;
};

// ---------------------------------------------------------------- records

//: The gateway's sequencing envelope; every record has one.
struct RecordEnvelope {
  uint32_t stream_id = 0;         // one per source
  uint16_t tag = 0;               // RecordTag
  uint32_t flags = 0;
  uint64_t seq = 0;               // consecutive within the stream (the resume position)
  uint64_t inst_seq = 0;          // consecutive within (stream, instrument, kind) (gap detection)
  uint64_t instrument_key = 0;    // instrument_hash(exchange, code)
  int64_t received_ns = 0;
  int64_t sequenced_ns = 0;
  //: The latest value sent on subscribing (or merged for a slow consumer), not a new event.
  bool snapshot() const { return flags & 1u; }
};

//: Tag 401: snapshot with 10 levels.
struct Quote : Coded {
  int64_t data_time = 0;
  int8_t instrument_type = 0;
  double pre_close_price = 0, pre_settlement_price = 0, last_price = 0, volume = 0, turnover = 0;
  double pre_open_interest = 0, open_interest = 0;
  double open_price = 0, high_price = 0, low_price = 0, upper_limit_price = 0, lower_limit_price = 0;
  double close_price = 0, settlement_price = 0, iopv = 0;
  double total_bid_volume = 0, total_ask_volume = 0;
  int64_t total_trade_num = 0;
  std::array<double, 10> bid_price{}, ask_price{}, bid_volume{}, ask_volume{};
  std::string trading_phase_code;
};

struct Entrust : Coded {
  int64_t data_time = 0;
  int8_t instrument_type = 0;
  double price = 0, volume = 0;
  int8_t side = 0, price_type = 0;
  int64_t main_seq = 0, seq = 0, orig_order_no = 0, biz_index = 0;
};

struct Transaction : Coded {
  int64_t data_time = 0;
  int8_t instrument_type = 0;
  double price = 0, volume = 0;
  int64_t bid_no = 0, ask_no = 0;
  int8_t exec_type = 0, side = 0;
  int64_t main_seq = 0, seq = 0, biz_index = 0;
};

struct Tick : Coded {
  int64_t data_time = 0;
  int8_t instrument_type = 0;
  double bid_price = 0, bid_volume = 0, ask_price = 0, ask_volume = 0;
};

struct Depth : Coded {
  int64_t data_time = 0;
  int8_t instrument_type = 0;
  double price = 0, volume = 0;
  int8_t side = 0;
};

//: Records the client found missing: received_inst_seq - expected_inst_seq never arrived.
struct SequenceGap : Coded {
  uint32_t stream_id = 0;
  uint16_t tag = 0;
  uint64_t expected_inst_seq = 0;
  uint64_t received_inst_seq = 0;
};

//: md_protocol.instrument_hash: FNV-1a 64 of exchange, 0x1f, code (= RecordEnvelope::instrument_key).
uint64_t instrument_hash(const std::string& exchange_id, const std::string& instrument_id);

// ---------------------------------------------------------------- codes

//: The exchanges the gateway serves (order_book_id suffixes): XSHG, XSHE, XBSE and the futures exchanges.
const std::vector<std::string>& quote_exchanges();
//: 600519.XSHG -> {XSHG, 600519}: the wire's (exchange_id, instrument_id). std::invalid_argument when
//: the code is not <code>.<exchange> or names an exchange the gateway does not serve.
std::pair<std::string, std::string> split_order_book_id(const std::string& order_book_id);

// ---------------------------------------------------------------- frames

namespace quote_protocol {

constexpr uint32_t kMagic = 0x44594E31;  // "DYN1"
constexpr uint16_t kVersion = 3;
constexpr size_t kHeaderSize = 16;
constexpr uint32_t kMaxBodyLen = 16u * 1024 * 1024;
constexpr double kHeartbeatInterval = 5.0;  // seconds: send at least one frame this often
constexpr double kHeartbeatTimeout = 15.0;  // seconds: nothing from the peer this long = the link is dead
constexpr size_t kMaxTokenBytes = 2048;

enum MsgType : uint16_t {
  REQ_LOGIN = 0xF001, RSP_LOGIN = 0xF002, REQ_SUBSCRIBE = 0xF003, RSP_SUBSCRIBE = 0xF004,
  REQ_UNSUBSCRIBE = 0xF005, RSP_UNSUBSCRIBE = 0xF006, REQ_SUBSCRIBE_ALL = 0xF007, RSP_SUBSCRIBE_ALL = 0xF008,
  QUERY_SOURCES = 0xF012, RSP_QUERY_SOURCES = 0xF013, REQ_UNSUBSCRIBE_ALL = 0xF014, RSP_UNSUBSCRIBE_ALL = 0xF015,
  RECORD_BATCH = 0xF020, STREAM_STATUS = 0xF021, REQ_RESUME = 0xF022, REQ_RESUME_START = 0xF023,
  REQ_REAUTH = 0xF030, RSP_REAUTH = 0xF031, NOTIFY_SESSION_EXPIRING = 0xF032, NOTIFY_SESSION_CLOSED = 0xF033,
  HEARTBEAT = 0xF0FF,
};

struct FrameHeader {
  uint32_t magic = 0;
  uint16_t version = 0;
  uint16_t msg_type = 0;
  uint32_t seq_no = 0;
  uint32_t body_len = 0;
};

std::string make_frame(uint16_t msg_type, uint32_t seq_no, const std::string& body = "");
FrameHeader unpack_header(const std::string& data);

std::string pack_login_req(const std::string& token, const std::string& client_id = "libfinance");
std::string pack_reauth_req(const std::string& token);
std::string pack_sub_req(const std::string& exchange_id, const std::string& instrument_id,
                         const std::string& source = "");
std::string pack_sub_all_req(MarketType market, uint64_t instrument_type, uint64_t data_type);
//: REQ_RESUME: {stream_id: last seq}.
std::string pack_resume_positions(const std::vector<std::pair<uint32_t, uint64_t>>& positions);

LoginRsp unpack_login_rsp(const std::string& body);
SessionClosed unpack_session_closed(const std::string& body);
SubRsp unpack_sub_rsp(const std::string& body);
SubAllRsp unpack_sub_all_rsp(const std::string& body);
std::vector<SourceDirEntry> unpack_source_dir_list(const std::string& body);
StreamStatus unpack_stream_status(const std::string& body);

//: One record of a batch: its envelope and its bytes.
struct BatchRecord {
  RecordEnvelope envelope;
  std::string pod;
};
//: RECORD_BATCH body -> records; a malformed tail ends the list (no exception).
std::vector<BatchRecord> iter_batch(const std::string& body);

//: A record's size on the wire by tag; 0 for a tag this client does not know.
size_t record_size(uint16_t tag);
Quote unpack_quote(const std::string& pod);
Entrust unpack_entrust(const std::string& pod);
Transaction unpack_transaction(const std::string& pod);
Tick unpack_tick(const std::string& pod);
Depth unpack_depth(const std::string& pod);

}  // namespace quote_protocol
}  // namespace libfinance
