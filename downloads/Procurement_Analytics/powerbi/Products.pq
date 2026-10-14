let
    Source = Csv.Document(File.Contents(BaseFolder & "data/Products.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"SKU", type text}, {"Product", type text}, {"Category", type text}, {"BaseCost", type number}, {"BulkCost", type number}, {"BulkThreshold", type number}, {"OrderMultiple", type number}, {"MonthlyDemand", type number}, {"OnHand", type number}}, "en-GB")
in
    Typed
