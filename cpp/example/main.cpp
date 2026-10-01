// The quick start of the Python README, in C++.
//
//   LIBFINANCE_HOST=127.0.0.1 ./libfinance_example
#include <iostream>

#include <libfinance/libfinance.hpp>

namespace lf = libfinance;

int main() {
  try {
    for (const auto& instrument : lf::instruments("600000.XSHG", "2024-03-01"))
      std::cout << instrument.order_book_id() << " " << instrument.name() << " " << instrument.type() << "\n";

    const lf::Table bars = lf::get_price({"000001.XSHE", "600000.XSHG"}, "2024-03-01", "2024-03-06", "1d", {}, false,
                                         true, /*adjust_type=*/"none");
    std::cout << bars->ToString() << "\n";

    std::cout << "trading days in March 2024: " << lf::count_trading_dates("2024-03-01", "2024-03-31") << "\n";
  } catch (const lf::RpcError& error) {
    std::cerr << error.kind() << " " << error.what() << "\n";
    return 1;
  }
  return 0;
}
