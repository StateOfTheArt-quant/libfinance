// Daily bars (Python: libfinance/api/get_price.py).
#pragma once

#include <optional>
#include <string>

#include "libfinance/types.hpp"

namespace libfinance {

//: Daily bars of stocks and indexes, mixed in one batch: columns order_book_id, datetime, then the
//: fields, sorted by (order_book_id, datetime) -- the Python client's
//: (order_book_id, datetime) index as columns.
//:
//: frequency: "1d" only. adjust_type: "pre" (default), "post" or "none" for stocks; indexes are
//: returned as published. Volume is scaled against the adjustment, turnover is not. The server
//: resolves the codes as of end_date and checks the fields. See get_price_coverage for the dates a
//: query may reach.
Table get_price(const Codes& order_book_ids, const DateLike& start_date, const DateLike& end_date,
                const std::string& frequency = "1d", const Codes& fields = {}, bool skip_suspended = false,
                bool include_now = true, const std::string& adjust_type = "pre",
                const std::optional<DateLike>& adjust_orig = std::nullopt);

//: {type: {venue: {"start", "end", "raw_end", "adjust_cutoff"?}}}: where daily bars start and end.
//: A stock's `end` is the last day adjusted prices reach (the smaller of the bars' end and the
//: exfactor cutoff); an index is not adjusted, so its `end` is `raw_end`.
Json get_price_coverage(const std::string& market = "cn");

}  // namespace libfinance
