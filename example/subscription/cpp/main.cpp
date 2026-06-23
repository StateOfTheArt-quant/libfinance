// ============================================================
// main.cpp —— libfinance C++ 订阅 demo（对齐 Python live_subscribe_example.py）
// ============================================================
#include <atomic>
#include <chrono>
#include <csignal>
#include <iomanip>
#include <iostream>
#include <string>
#include <thread>

#include "libfinance/quote_api.h"

static std::atomic<bool> g_running{true};
static void sig_handler(int) { g_running = false; }

class MyQuoteSpi : public client::QuoteSpi {
public:
    void OnConnected() override {
        std::cout << "[SPI] connected\n";
    }

    void OnDisconnected(int reason) override {
        std::cout << "[SPI] disconnected reason=" << reason << "\n";
        g_running = false;
    }

    void OnRspLogin(const md_proto::LoginRsp* rsp, int /*request_id*/, bool /*is_last*/) override {
        if (rsp->error_id == 0) {
            std::string max_str = rsp->max_subscriptions < 0
                ? "unlimited" : std::to_string(rsp->max_subscriptions);
            std::cout << "[SPI] login OK  session_id=" << rsp->session_id
                      << "  user_level=" << static_cast<int>(rsp->user_level)
                      << "  max_subs=" << max_str << "\n";
        } else {
            std::cout << "[SPI] login FAIL: " << rsp->error_msg << "\n";
            g_running = false;
        }
    }

    void OnRspSubscribeMarketData(const md_proto::SubRsp* rsp, int /*request_id*/, bool /*is_last*/) override {
        if (rsp->error_id == 0) {
            std::string max_str = rsp->max_subs < 0
                ? "unlimited" : std::to_string(rsp->max_subs);
            std::cout << "[SPI] subscribed " << rsp->exchange_id << "." << rsp->instrument_id
                      << "  [" << rsp->current_subs << "/" << max_str << "]\n";
        } else if (rsp->error_id == 3) {
            std::cout << "[SPI] subscribe QUOTA EXCEEDED: " << rsp->error_msg
                      << "  [" << rsp->current_subs << "/" << rsp->max_subs << "]\n";
        } else {
            std::cout << "[SPI] subscribe fail: " << rsp->error_msg << "\n";
        }
    }

    void OnRspUnsubscribeMarketData(const md_proto::SubRsp* rsp, int /*request_id*/, bool /*is_last*/) override {
        std::cout << "[SPI] unsubscribed " << rsp->exchange_id << "." << rsp->instrument_id << "\n";
    }

    void OnDepthMarketData(const md_proto::Quote* q) override {
        uint64_t n = ++count_;
        std::cout << std::fixed << std::setprecision(3)
                  << "[QUOTE #" << std::setw(5) << n << "] "
                  << q->exchange_id << "." << q->instrument_id
                  << "  last=" << std::setw(10) << q->last_price
                  << "  bid1=" << std::setw(10) << q->bid_price[0]
                  << "  ask1=" << std::setw(10) << q->ask_price[0]
                  << "  bid_volume[0]="  << q->bid_volume[0] << "\n";
    }

    void OnHeartbeat() override {}

    uint64_t count() const { return count_; }

private:
    std::atomic<uint64_t> count_{0};
};

int main(int argc, char* argv[]) {
    std::signal(SIGINT,  sig_handler);
    std::signal(SIGTERM, sig_handler);

    std::string host = "127.0.0.1";
    uint16_t    port = 9001;
    if (argc > 1) host = argv[1];
    if (argc > 2) port = static_cast<uint16_t>(std::stoi(argv[2]));

    auto* spi = new MyQuoteSpi();
    auto* api = client::QuoteApi::CreateQuoteApi(".");
    api->RegisterSpi(spi);

    if (api->Connect(host, port) != 0) {
        std::cerr << "[Client] connect failed\n";
        api->Release();
        delete spi;
        return 1;
    }

    api->SubscribeMarketData({"rb2501", "hc2501"}, "SHFE");
    api->SubscribeMarketData({"i2501",  "j2501"},  "DCE");
    api->SubscribeMarketData({"600000", "600001"}, "SSE");

    std::this_thread::sleep_for(std::chrono::seconds(5));
    if (g_running) {
        std::cout << "\n[Client] unsubscribing rb2501...\n";
        api->UnsubscribeMarketData({"rb2501"}, "SHFE");
    }

    while (g_running) std::this_thread::sleep_for(std::chrono::milliseconds(100));

    std::cout << "\n[Client] total quotes: " << spi->count() << "\n";
    api->Disconnect();
    api->Release();
    delete spi;
    return 0;
}
