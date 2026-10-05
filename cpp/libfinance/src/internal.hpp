// What the API modules share: calling the server, argument checks (Python's
// libfinance/utils/validators.py), caches (libfinance/utils/cache.py and ttl_cache).
#pragma once

#include <chrono>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include "libfinance/client.hpp"
#include "libfinance/errors.hpp"
#include "libfinance/types.hpp"

namespace libfinance::detail {

// ---------------------------------------------------------------- calls

//: get_client().call(function, args).
Json call(const std::string& function, const Json& args);
//: A call whose answer is a table.
Table call_table(const std::string& function, const Json& args);
//: warnings.warn(message).
void warn(const std::string& message);

// ---------------------------------------------------------------- arguments

//: ensure_list_of_string: the codes as a list (an error when none were given).
std::vector<std::string> list_of(const Codes& values, const std::string& name);
//: A date argument as the ISO day the server takes, or null.
Json iso_or_null(const std::optional<DateLike>& value);
Json text_or_null(const std::optional<std::string>& value);
//: A list argument, or null when none was given.
Json list_or_null(const Codes& values, const std::string& name);
//: "at least one order book id expected" when empty.
std::vector<std::string> order_book_ids(const Codes& values);
//: check_items_in_container: every item one of `allowed`.
//: `container` is how the message names the allowed values (Python prints its list or tuple).
void check_items_in(const std::vector<std::string>& items, const std::vector<std::string>& allowed,
                    const std::string& name, const std::string& container = "");
//: A codes argument as Python passes it on untouched: one string, a list, or null.
Json as_given(const Codes& values);
//: "invalid date range: ['a', 'b']" when start is after end (both given).
void check_date_range(const Json& start, const Json& end);
//: Python's repr of a list of strings: ['a', 'b'].
std::string py_list(const std::vector<std::string>& values);

// ---------------------------------------------------------------- tables

//: A table's rows as JSON objects (DataFrame.to_dict("records")); timestamps as ISO text.
std::vector<Json> rows_of(const Table& table);
//: The table with `name` moved to the first column (unchanged when it has no such column).
Table column_first(const Table& table, const std::string& name);

// ---------------------------------------------------------------- caches

//: The server's data version (ping's data_version), asked at most every 2 s; nullopt when the
//: server does not report one (then caches fall back to a 5 minute TTL).
std::optional<std::string> current_data_version();

//: Values cached by the server's data version: a change of version drops them, an unknown version
//: keeps them 5 minutes (Python's versioned_cache).
template <typename Value>
class VersionedCache {
 public:
  VersionedCache();
  Value get(const std::string& key, const std::function<Value()>& compute) {
    const auto version = current_data_version();
    const auto now = std::chrono::steady_clock::now();
    {
      std::lock_guard<std::mutex> guard(lock_);
      auto it = entries_.find(key);
      if (it != entries_.end()) {
        const Entry& hit = it->second;
        if (version && hit.version == version) return hit.value;
        if (!version && !hit.version && now - hit.at < std::chrono::minutes(5)) return hit.value;
      }
    }
    Value value = compute();
    std::lock_guard<std::mutex> guard(lock_);
    entries_[key] = Entry{version, now, value};
    return value;
  }
  void clear() {
    std::lock_guard<std::mutex> guard(lock_);
    entries_.clear();
  }

 private:
  struct Entry {
    std::optional<std::string> version;
    std::chrono::steady_clock::time_point at;
    Value value;
  };
  std::mutex lock_;
  std::map<std::string, Entry> entries_;
};

//: Registers a cache for clear_cache().
void register_cache(std::function<void()> clear);

template <typename Value>
VersionedCache<Value>::VersionedCache() {
  register_cache([this] { clear(); });
}

//: Values cached for a fixed time (Python's ttl_cache).
template <typename Value>
class TtlCache {
 public:
  explicit TtlCache(std::chrono::seconds ttl) : ttl_(ttl) {}
  Value get(const std::string& key, const std::function<Value()>& compute) {
    const auto now = std::chrono::steady_clock::now();
    {
      std::lock_guard<std::mutex> guard(lock_);
      auto it = entries_.find(key);
      if (it != entries_.end() && now - it->second.first < ttl_) return it->second.second;
    }
    Value value = compute();
    std::lock_guard<std::mutex> guard(lock_);
    entries_[key] = {now, value};
    return value;
  }

 private:
  std::chrono::seconds ttl_;
  std::mutex lock_;
  std::map<std::string, std::pair<std::chrono::steady_clock::time_point, Value>> entries_;
};

}  // namespace libfinance::detail
