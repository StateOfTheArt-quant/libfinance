#pragma once
// ============================================================
// quote_api.h — 客户端 SDK（XTP 风格）
// 改动：OnDepthMarketData 回调参数改为 Quote*
// ============================================================

#include <string>
#include <vector>
#include <functional>
#include <thread>
#include <mutex>
#include <deque>
#include <condition_variable>
#include <atomic>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <chrono>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#include "md_protocol.h"

namespace client {

// ── QuoteSpi ──────────────────────────────────────────────────
class QuoteSpi {
public:
    virtual ~QuoteSpi() = default;
    virtual void OnConnected() {}
    virtual void OnDisconnected(int reason) {}
    virtual void OnRspLogin(const md_proto::LoginRsp* rsp,
                            int request_id, bool is_last) {}
    virtual void OnRspSubscribeMarketData(const md_proto::SubRsp* rsp,
                                          int request_id, bool is_last) {}
    virtual void OnRspUnsubscribeMarketData(const md_proto::SubRsp* rsp,
                                            int request_id, bool is_last) {}
    // 行情回调：Quote 是严格 POD，客户端直接 memcpy 接收
    virtual void OnDepthMarketData(const md_proto::Quote* quote) {}
    virtual void OnHeartbeat() {}
};

// ── QuoteApi ──────────────────────────────────────────────────
class QuoteApi {
public:
    static QuoteApi* CreateQuoteApi(const std::string& log_path = ".") {
        return new QuoteApi(log_path);
    }
    void Release() { delete this; }
    void RegisterSpi(QuoteSpi* spi) { spi_ = spi; }

    int Connect(const std::string& ip, uint16_t port,
                uint32_t timeout_ms = 3000) {
        fd_ = ::socket(AF_INET, SOCK_STREAM, 0);
        if (fd_ < 0) return -1;

        struct timeval tv;
        tv.tv_sec  = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        ::setsockopt(fd_, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port   = htons(port);
        if (::inet_pton(AF_INET, ip.c_str(), &addr.sin_addr) <= 0) {
            ::close(fd_); fd_ = -1; return -1;
        }
        if (::connect(fd_, (sockaddr*)&addr, sizeof(addr)) < 0) {
            std::cerr << "[QuoteApi] connect failed: " << strerror(errno) << "\n";
            ::close(fd_); fd_ = -1; return -1;
        }

        tv.tv_sec = 60; tv.tv_usec = 0;
        ::setsockopt(fd_, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

        std::cout << "[QuoteApi] connected to " << ip << ":" << port << "\n";
        connected_ = true;

        read_thread_  = std::thread([this]{ read_loop(); });
        write_thread_ = std::thread([this]{ write_loop(); });
        hb_thread_    = std::thread([this]{ heartbeat_loop(); });

        if (spi_) spi_->OnConnected();
        return 0;
    }

    int Login(const std::string& user_id, const std::string& password) {
        md_proto::LoginReq req{};
        std::strncpy(req.user_id,   user_id.c_str(),  sizeof(req.user_id)-1);
        std::strncpy(req.password,  password.c_str(), sizeof(req.password)-1);
        std::strncpy(req.client_id, "kf_cpp_client",  sizeof(req.client_id)-1);
        uint32_t seq = next_seq_++;
        enqueue(md_proto::make_frame(md_proto::MsgType::REQ_LOGIN, seq, req));
        return (int)seq;
    }

    int SubscribeMarketData(const std::vector<std::string>& instruments,
                            const std::string& exchange_id) {
        int last = 0;
        for (const auto& inst : instruments) {
            md_proto::SubReq req{};
            std::strncpy(req.exchange_id,   exchange_id.c_str(), sizeof(req.exchange_id)-1);
            std::strncpy(req.instrument_id, inst.c_str(),         sizeof(req.instrument_id)-1);
            uint32_t seq = next_seq_++;
            enqueue(md_proto::make_frame(md_proto::MsgType::REQ_SUBSCRIBE, seq, req));
            last = (int)seq;
        }
        return last;
    }

    int UnsubscribeMarketData(const std::vector<std::string>& instruments,
                              const std::string& exchange_id) {
        int last = 0;
        for (const auto& inst : instruments) {
            md_proto::SubReq req{};
            std::strncpy(req.exchange_id,   exchange_id.c_str(), sizeof(req.exchange_id)-1);
            std::strncpy(req.instrument_id, inst.c_str(),         sizeof(req.instrument_id)-1);
            uint32_t seq = next_seq_++;
            enqueue(md_proto::make_frame(md_proto::MsgType::REQ_UNSUBSCRIBE, seq, req));
            last = (int)seq;
        }
        return last;
    }

    void Disconnect() {
        connected_ = false;
        write_stop_ = true;
        wcv_.notify_all();
        if (fd_ >= 0) { ::shutdown(fd_, SHUT_RDWR); ::close(fd_); fd_ = -1; }
        if (read_thread_.joinable())  read_thread_.join();
        if (write_thread_.joinable()) write_thread_.join();
        if (hb_thread_.joinable())    hb_thread_.join();
    }

private:
    explicit QuoteApi(const std::string& lp)
        : log_path_(lp), fd_(-1), connected_(false)
        , next_seq_(1), write_stop_(false) {}
    ~QuoteApi() { Disconnect(); }

    void read_loop() {
        while (connected_) {
            md_proto::FrameHeader hdr{};
            if (!recv_exact(&hdr, sizeof(hdr))) break;
            if (hdr.magic != md_proto::MAGIC) {
                std::cerr << "[QuoteApi] bad magic\n"; break;
            }
            std::vector<uint8_t> body;
            if (hdr.body_len > 0) {
                body.resize(hdr.body_len);
                if (!recv_exact(body.data(), hdr.body_len)) break;
            }
            dispatch(hdr, body);
        }
        if (spi_) spi_->OnDisconnected(0);
    }

    void write_loop() {
        while (true) {
            std::unique_lock<std::mutex> lk(wmu_);
            wcv_.wait(lk, [this]{ return !wqueue_.empty() || write_stop_; });
            if (write_stop_ && wqueue_.empty()) break;
            while (!wqueue_.empty()) {
                auto buf = std::move(wqueue_.front());
                wqueue_.pop_front();
                lk.unlock();
                send_exact(buf.data(), buf.size());
                lk.lock();
            }
        }
    }

    void heartbeat_loop() {
        while (connected_) {
            std::this_thread::sleep_for(std::chrono::seconds(10));
            if (!connected_) break;
            enqueue(md_proto::make_heartbeat(next_seq_++));
        }
    }

    void dispatch(const md_proto::FrameHeader& hdr,
                  const std::vector<uint8_t>& body) {
        auto t = static_cast<md_proto::MsgType>(hdr.msg_type);
        switch (t) {
        case md_proto::MsgType::RSP_LOGIN:
            if (body.size() >= sizeof(md_proto::LoginRsp) && spi_)
                spi_->OnRspLogin(
                    reinterpret_cast<const md_proto::LoginRsp*>(body.data()),
                    hdr.seq_no, true);
            break;
        case md_proto::MsgType::RSP_SUBSCRIBE:
            if (body.size() >= sizeof(md_proto::SubRsp) && spi_)
                spi_->OnRspSubscribeMarketData(
                    reinterpret_cast<const md_proto::SubRsp*>(body.data()),
                    hdr.seq_no, true);
            break;
        case md_proto::MsgType::RSP_UNSUBSCRIBE:
            if (body.size() >= sizeof(md_proto::SubRsp) && spi_)
                spi_->OnRspUnsubscribeMarketData(
                    reinterpret_cast<const md_proto::SubRsp*>(body.data()),
                    hdr.seq_no, true);
            break;
        case md_proto::MsgType::MD_QUOTE:
            // Quote 是 POD，body 里的内存直接转换，无需拷贝
            if (body.size() >= sizeof(md_proto::Quote) && spi_)
                spi_->OnDepthMarketData(
                    reinterpret_cast<const md_proto::Quote*>(body.data()));
            break;
        case md_proto::MsgType::HEARTBEAT:
            if (spi_) spi_->OnHeartbeat();
            break;
        default:
            std::cerr << "[QuoteApi] unknown msg_type=" << hdr.msg_type << "\n";
        }
    }

    bool recv_exact(void* buf, std::size_t n) {
        char* p = static_cast<char*>(buf);
        std::size_t got = 0;
        while (got < n) {
            ssize_t r = ::recv(fd_, p + got, n - got, 0);
            if (r <= 0) return false;
            got += r;
        }
        return true;
    }
    bool send_exact(const void* buf, std::size_t n) {
        const char* p = static_cast<const char*>(buf);
        std::size_t sent = 0;
        while (sent < n) {
            ssize_t r = ::send(fd_, p + sent, n - sent, MSG_NOSIGNAL);
            if (r <= 0) return false;
            sent += r;
        }
        return true;
    }
    void enqueue(std::vector<uint8_t> buf) {
        std::lock_guard<std::mutex> lk(wmu_);
        wqueue_.push_back(std::move(buf));
        wcv_.notify_one();
    }

    std::string       log_path_;
    QuoteSpi*         spi_ = nullptr;
    int               fd_;
    std::atomic<bool> connected_;
    std::atomic<uint32_t> next_seq_;

    std::thread read_thread_;
    std::thread hb_thread_;

    std::mutex wmu_;
    std::condition_variable wcv_;
    std::deque<std::vector<uint8_t>> wqueue_;
    std::thread write_thread_;
    std::atomic<bool> write_stop_;
};

} // namespace client
