// Table answers: Arrow IPC (the C++ server) and pandas' orient=table JSON (the Python one).
#include <gtest/gtest.h>

#include <arrow/api.h>
#include <arrow/io/memory.h>
#include <arrow/ipc/writer.h>

#include <libfinance/client.hpp>

using libfinance::Json;

TEST(AsTable, ReadsPandasTableJson) {
  const Json document = {
      {"schema",
       {{"fields",
         {{{"name", "index"}, {"type", "integer"}},
          {{"name", "order_book_id"}, {"type", "string"}},
          {{"name", "ex_date"}, {"type", "datetime"}},
          {{"name", "ratio"}, {"type", "string"}},  // an object column of numbers (Decimals)
          {{"name", "confirmed"}, {"type", "boolean"}}}},
        {"primaryKey", {"index"}}}},
      {"data",
       {{{"index", 0}, {"order_book_id", "AAPL.US"}, {"ex_date", "2020-08-31T00:00:00.000"}, {"ratio", 4.0},
         {"confirmed", true}},
        {{"index", 1}, {"order_book_id", "MSFT.US"}, {"ex_date", nullptr}, {"ratio", nullptr}, {"confirmed", false}}}}};
  const auto table = libfinance::as_table({{"type", "pandas"}, {"data", document.dump()}});
  ASSERT_TRUE(table);
  EXPECT_EQ(table->num_rows(), 2);
  EXPECT_EQ(table->schema()->field_names(), (std::vector<std::string>{"order_book_id", "ex_date", "ratio", "confirmed"}));
  EXPECT_EQ(table->GetColumnByName("ex_date")->type()->id(), arrow::Type::TIMESTAMP);
  EXPECT_EQ(table->GetColumnByName("ratio")->type()->id(), arrow::Type::DOUBLE);
  EXPECT_EQ(table->GetColumnByName("ratio")->null_count(), 1);
}

TEST(AsTable, ReadsArrowIpc) {
  arrow::StringBuilder ids;
  ASSERT_TRUE(ids.AppendValues({"600000.XSHG", "000001.XSHE"}).ok());
  const auto source = arrow::Table::Make(arrow::schema({arrow::field("order_book_id", arrow::utf8())}),
                                         {ids.Finish().ValueOrDie()});
  auto sink = arrow::io::BufferOutputStream::Create().ValueOrDie();
  auto writer = arrow::ipc::MakeStreamWriter(sink, source->schema()).ValueOrDie();
  ASSERT_TRUE(writer->WriteTable(*source).ok());
  ASSERT_TRUE(writer->Close().ok());
  const auto buffer = sink->Finish().ValueOrDie();
  const Json answer = {{"type", "arrow"},
                       {"data", Json::binary(std::vector<uint8_t>(buffer->data(), buffer->data() + buffer->size()))}};
  const auto table = libfinance::as_table(answer);
  ASSERT_TRUE(table);
  EXPECT_TRUE(table->Equals(*source));
}

TEST(AsTable, RefusesOtherAnswers) {
  EXPECT_THROW(libfinance::as_table(Json{{"status", "ok"}}), std::invalid_argument);
  EXPECT_EQ(libfinance::as_table(Json()), nullptr);
}
