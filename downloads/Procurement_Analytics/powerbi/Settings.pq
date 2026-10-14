let
    Source = Csv.Document(File.Contents(BaseFolder & "data/Settings.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"VAT", type number}, {"TargetGM", type number}, {"Premium", type number}, {"FeeRate", type number}, {"MaxCover", type number}, {"FreshDays", type number}, {"AsOfDate", type date}}, "en-GB")
in
    Typed
