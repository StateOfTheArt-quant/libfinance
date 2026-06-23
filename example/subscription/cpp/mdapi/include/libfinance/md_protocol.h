#pragma once
// ============================================================
// md_protocol.h — 二进制帧协议（服务端 & 客户端共用）
//
// 设计原则：
//   此文件被服务端和客户端同时 include，不得引用任何功夫 SDK
//   头文件（longfist、kungfu 等）。
//
//   to_wire() 在此只提供 Quote → Quote 的恒等重载。
//   真实功夫的 longfist::types::Quote → Quote 转换
//   定义在 server/quote_converter.h，仅服务端 include。
// ============================================================

#include <cstdint>
#include <cstring>
#include <vector>
#include <memory>

namespace md_proto {

static constexpr uint32_t MAGIC   = 0x4B463235; // "KF25"
static constexpr uint8_t  VERSION = 1;

enum class MsgType : uint16_t {
    REQ_LOGIN          = 0x0001,
    RSP_LOGIN          = 0x0002,
    REQ_SUBSCRIBE      = 0x0003,
    RSP_SUBSCRIBE      = 0x0004,
    REQ_UNSUBSCRIBE    = 0x0005,
    RSP_UNSUBSCRIBE    = 0x0006,
    MD_QUOTE           = 0x0010,
    HEARTBEAT          = 0x00FF,
};

#pragma pack(push, 1)

struct FrameHeader {
    uint32_t magic;
    uint8_t  version;
    uint8_t  _pad;
    uint16_t msg_type;
    uint32_t seq_no;
    uint16_t body_len;
    uint16_t _pad2;
};
static_assert(sizeof(FrameHeader) == 16, "FrameHeader size mismatch");

struct LoginReq {
    char user_id  [16];
    char password [32];
    char client_id[32];
};

struct LoginRsp {
    int32_t  error_id;
    char     error_msg[64];
    uint64_t session_id;
    int8_t   user_level;        // 用户等级（对应 UserLevel 枚举）
    int8_t   _rsp_pad[3];
    int32_t  max_subscriptions;  // 最大订阅数，-1 表示无限制
};

struct SubReq {
    char exchange_id  [8];
    char instrument_id[32];
};

struct SubRsp {
    char    exchange_id  [8];
    char    instrument_id[32];
    int32_t error_id;
    char    error_msg[64];
    int32_t current_subs;       // 当前订阅数
    int32_t max_subs;           // 最大订阅数，-1 无限制
};

// ------------------------------------------------------------
// Quote — 网络传输行情，严格 POD
//
// 字段完整对齐 longfist::types::Quote：
//   kungfu::array<char,N>     → char[N]
//   kungfu::array<double,10>  → double[10]
//   kungfu::array<int64_t,10> → int64_t[10]
//   enums::InstrumentType     → int32_t
// ------------------------------------------------------------
struct Quote {
    char    trading_day        [9];
    char    instrument_id      [32];
    char    exchange_id        [8];
    int32_t instrument_type;
    double  pre_close_price;
    double  pre_settlement_price;
    double  last_price;
    int64_t volume;
    double  turnover;
    double  pre_open_interest;
    double  open_interest;
    double  open_price;
    double  high_price;
    double  low_price;
    double  upper_limit_price;
    double  lower_limit_price;
    double  close_price;
    double  settlement_price;
    double  iopv;
    double  bid_price          [10];
    double  ask_price          [10];
    int64_t bid_volume         [10];
    int64_t ask_volume         [10];
    char    trading_phase_code [8];
    int64_t data_time;
};

#pragma pack(pop)

static_assert(std::is_trivially_copyable<Quote>::value,
              "Quote must be trivially copyable");

// ------------------------------------------------------------
// to_wire() — 恒等重载（Stub 模式 & 客户端可见）
//
// 真实功夫重载：见 server/quote_converter.h
// ------------------------------------------------------------
inline const Quote& to_wire(const Quote& q) { return q; }

// ------------------------------------------------------------
// make_frame() — by-value，控制帧（低频）
// ------------------------------------------------------------
template<typename Body>
inline std::vector<uint8_t> make_frame(MsgType type, uint32_t seq, const Body& body) {
    std::vector<uint8_t> buf(sizeof(FrameHeader) + sizeof(Body));
    FrameHeader hdr{};
    hdr.magic    = MAGIC;
    hdr.version  = VERSION;
    hdr.msg_type = static_cast<uint16_t>(type);
    hdr.seq_no   = seq;
    hdr.body_len = static_cast<uint16_t>(sizeof(Body));
    std::memcpy(buf.data(),               &hdr,  sizeof(hdr));
    std::memcpy(buf.data() + sizeof(hdr), &body, sizeof(Body));
    return buf;
}

// ------------------------------------------------------------
// make_shared_frame() — 行情帧（高频）
//
// 序列化一次，返回 shared_ptr<const vector>。
// N 个连接共享同一块内存，引用计数归零时自动释放。
// seq_no 置 0（广播帧无需 per-client 序号）。
// ------------------------------------------------------------
inline std::shared_ptr<const std::vector<uint8_t>>
make_shared_frame(const Quote& body) {
    auto buf = std::make_shared<std::vector<uint8_t>>(
        sizeof(FrameHeader) + sizeof(Quote));
    FrameHeader hdr{};
    hdr.magic    = MAGIC;
    hdr.version  = VERSION;
    hdr.msg_type = static_cast<uint16_t>(MsgType::MD_QUOTE);
    hdr.seq_no   = 0;
    hdr.body_len = static_cast<uint16_t>(sizeof(Quote));
    std::memcpy(buf->data(),               &hdr,  sizeof(hdr));
    std::memcpy(buf->data() + sizeof(hdr), &body, sizeof(Quote));
    return buf;
}

inline std::vector<uint8_t> make_heartbeat(uint32_t seq) {
    std::vector<uint8_t> buf(sizeof(FrameHeader));
    FrameHeader hdr{};
    hdr.magic    = MAGIC;
    hdr.version  = VERSION;
    hdr.msg_type = static_cast<uint16_t>(MsgType::HEARTBEAT);
    hdr.seq_no   = seq;
    hdr.body_len = 0;
    std::memcpy(buf.data(), &hdr, sizeof(hdr));
    return buf;
}

} // namespace md_proto
