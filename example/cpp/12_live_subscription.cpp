// 实时行情订阅（Python：example/python/12_live_subscription.py）。
//
// 流程：连网关 → （自动取票据登录）→ 发现可订源（query_sources）→ 订阅 → 收行情回调。
// 不需要登录：客户端自动向 libfinance-service 取行情票据（不登录按 IP 额度），网关地址也由它给出。
//
//   libfinance_12_live_subscription [gateways] [source]
//     gateways：不指定则用 libfinance-service 返回的网关地址；也可写 "host:port,host:port"
//     不指定 source：无源订阅，网关按健康+优先级自动选源，源掉线自动灾备切换
//     指定 source  ：定向订阅该源，不自动切源；该源不健康时明确失败
//
// 要点：订阅写在 on_rsp_login 里——断线自动重连+重登录后会再次触发，订阅随之重放。
// 代码是统一的 order_book_id（600519.XSHG），与 get_price 等函数相同；一次订阅可混合交易所。
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <ctime>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <libfinance/libfinance.hpp>

namespace lf = libfinance;

namespace {

const std::vector<std::string> kOrderBookIds = {"600519.XSHG", "000001.XSHE"};  // 贵州茅台、平安银行
std::atomic<bool> stop{false};

class DemoSpi : public lf::QuoteSpi {
 public:
  DemoSpi(lf::QuoteApi& api, std::string source) : api_(api), source_(std::move(source)) {}
  long count() const { return count_; }

  void on_connected() override { std::cout << "[client] connected\n"; }
  void on_disconnected(int reason) override {
    std::cout << "[client] disconnected reason=" << reason << "，等待自动重连…\n";
  }

  // 登录成功即发现可订源；断线重连会重新走一遍，订阅自动重放。
  void on_rsp_login(const lf::LoginRsp& rsp, int) override {
    if (rsp.error_id != 0) {
      std::cout << "[client] login FAIL: " << rsp.error_msg << "\n";
      stop = true;
      return;
    }
    const long left = std::max<long>(0, static_cast<long>(rsp.expires_at_ms / 1000 - std::time(nullptr)));
    std::cout << "[client] login OK  max_subs="
              << (rsp.max_subscriptions < 0 ? std::string("unlimited") : std::to_string(rsp.max_subscriptions))
              << "  whole_market=" << rsp.sub_all << "  ticket expires in " << left << "s (auto-renewed)\n";
    api_.query_sources();
  }

  void on_rsp_query_sources(const std::vector<lf::SourceDirEntry>& sources, int) override {
    std::cout << "[client] 发现 " << sources.size() << " 个源：\n";
    bool routable = false;
    for (const auto& s : sources) {
      std::cout << "  - " << s.source << " [" << (s.health ? "ready" : "down") << "] priority=" << s.priority
                << (s.whole_market ? " 覆盖=整市场" : "") << (s.directed_only ? " 仅定向(不自动选/灾备)" : "") << "\n";
      routable = routable || (s.health && !s.directed_only);
    }
    // 仅定向源不参与无源订阅/灾备，不能算作可用于自动路由的健康源。
    if (source_.empty() && !routable) {
      std::cout << "[client] 暂无可用于自动路由的健康源，不订阅\n";
      return;
    }
    std::cout << "[client] 订阅 " << kOrderBookIds[0] << "," << kOrderBookIds[1] << "  方式="
              << (source_.empty() ? "无源(网关自动选源)" : "定向 " + source_) << "\n";
    api_.subscribe(kOrderBookIds, source_);
  }

  void on_rsp_subscribe(const lf::SubRsp& rsp, int) override {
    switch (static_cast<lf::QuoteError>(rsp.error_id)) {
      case lf::QuoteError::Ok:
        std::cout << "[client] subscribed " << rsp.order_book_id() << " ← 供数源 '" << rsp.source << "'  ("
                  << rsp.current_subs << "/" << rsp.max_subs << ")\n";
        break;
      case lf::QuoteError::SubscriptionLimit:
        std::cout << "[client] 订阅数达到上限（不登录按 IP 额度，登录后按账号等级）: " << rsp.error_msg << "\n";
        break;
      case lf::QuoteError::MarketNotGranted:
        std::cout << "[client] 该市场不在授权内: " << rsp.error_msg << "\n";
        break;
      case lf::QuoteError::SourceUnavailable:
        std::cout << "[client] 路由冲突或指定源不可用: " << rsp.error_msg << "\n";
        break;
      default:
        std::cout << "[client] subscribe fail(" << rsp.error_id << "): " << rsp.error_msg << "\n";
    }
  }

  void on_depth_market_data(const lf::Quote& q, const lf::RecordEnvelope&) override {
    std::printf("[%5ld] %-14s  last=%9.3f  bid1=%9.3f  ask1=%9.3f  vol=%.0f\n", ++count_, q.order_book_id().c_str(),
                q.last_price, q.bid_price[0], q.ask_price[0], q.volume);
  }

 private:
  lf::QuoteApi& api_;
  std::string source_;
  std::atomic<long> count_{0};
};

}  // namespace

int main(int argc, char** argv) {
  const std::string gateways = argc > 1 ? argv[1] : "";
  const std::string source = argc > 2 ? argv[2] : "";
  std::signal(SIGINT, [](int) { stop = true; });
  std::signal(SIGTERM, [](int) { stop = true; });

  lf::QuoteApi api;
  DemoSpi spi(api, source);
  api.register_spi(&spi);
  // 不必 login：客户端自动向 libfinance-service 取票据，到期前自动续期；断线自动重连并续传。
  if (api.connect(gateways) != 0) std::cout << "[client] 暂时连不上网关，后台持续重连…\n";

  while (!stop) std::this_thread::sleep_for(std::chrono::milliseconds(200));  // Ctrl+C 退出
  std::cout << "\n[client] total quotes: " << spi.count() << "\n";
  api.disconnect();
  return 0;
}
