// Reusable UTF-8 CSV loader. Empty fields stay null; identifiers stay text.
(fileName as text, columnTypes as list) as table =>
let
    Source = Csv.Document(File.Contents(BaseFolder & "data/" & fileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(Nulls, columnTypes, "en-GB")
in
    Typed
