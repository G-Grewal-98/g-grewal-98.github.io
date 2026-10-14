let
    Source = Csv.Document(File.Contents(BaseFolder & "data/Metrics.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"SKU", type text}, {"Product", type text}, {"Category", type text}, {"BaseCost", type number}, {"BulkCost", type number}, {"BulkThreshold", type number}, {"OrderMultiple", type number}, {"MonthlyDemand", type number}, {"OnHand", type number}, {"Benchmark", type number}, {"Availability", type text}, {"Retailer", type text}, {"SourceID", type text}, {"Shelf", type number}, {"BulkUnits", type number}, {"VAT", type number}, {"TargetGM", type number}, {"FeeRate", type number}, {"MaxCover", type number}, {"BaseGM", type number}, {"BulkGM", type number}, {"BaseContribution", type number}, {"BulkContribution", type number}, {"BulkCash", type number}, {"BulkCover", type number}, {"BulkVerdict", type text}, {"Recommendation", type text}}, "en-GB")
in
    Typed
