let
    Source = Csv.Document(File.Contents(BaseFolder & "data/Prices.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"SourceID", type text}, {"SKU", type text}, {"Retailer", type text}, {"Price", type number}, {"CheckedDate", type date}, {"Availability", type text}, {"MatchType", type text}}, "en-GB")
in
    Typed
