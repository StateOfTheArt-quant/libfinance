// Argument checks: Python's libfinance/utils/validators.py.
#include <algorithm>

#include "internal.hpp"

namespace libfinance::detail {

std::vector<std::string> list_of(const Codes& values, const std::string& name) {
  if (!values.given()) throw std::invalid_argument(name + ": expect string or list of string, got None");
  return values.values();
}

Json iso_or_null(const std::optional<DateLike>& value) { return value ? Json(value->iso()) : Json(); }

Json text_or_null(const std::optional<std::string>& value) { return value ? Json(*value) : Json(); }

Json list_or_null(const Codes& values, const std::string& name) {
  return values.given() ? Json(list_of(values, name)) : Json();
}

std::vector<std::string> order_book_ids(const Codes& values) {
  std::vector<std::string> ids = list_of(values, "order_book_ids");
  if (ids.empty()) throw std::invalid_argument("order_book_ids: at least one order book id expected");
  return ids;
}

void check_items_in(const std::vector<std::string>& items, const std::vector<std::string>& allowed,
                    const std::string& name, const std::string& container) {
  for (const auto& item : items)
    if (std::find(allowed.begin(), allowed.end(), item) == allowed.end())
      throw std::invalid_argument(name + ": got invalided value " + item + ", choose any in " +
                                  (container.empty() ? py_list(allowed) : container));
}

Json as_given(const Codes& values) {
  if (!values.given()) return Json();
  return values.single() ? Json(values.values().front()) : Json(values.values());
}

void check_date_range(const Json& start, const Json& end) {
  if (start.is_string() && end.is_string() && start.get<std::string>() > end.get<std::string>())
    throw std::invalid_argument("invalid date range: ['" + start.get<std::string>() + "', '" +
                                end.get<std::string>() + "']");
}

std::string py_list(const std::vector<std::string>& values) {
  std::string out = "[";
  for (size_t i = 0; i < values.size(); ++i) out += (i ? ", '" : "'") + values[i] + "'";
  return out + "]";
}

}  // namespace libfinance::detail
