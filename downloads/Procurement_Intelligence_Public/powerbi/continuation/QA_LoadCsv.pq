(name as text, numericColumns as list, integerColumns as list) as table =>
let
    Source = Csv.Document(File.Contents(QA_GenerationFolder & "\data\" & name & ".csv"),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source,[PromoteAllScalars=true]),
    Blanks = Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),
    Types = List.Combine({List.Transform(numericColumns,each {_,type number}),List.Transform(integerColumns,each {_,Int64.Type})}),
    Typed = Table.TransformColumnTypes(Blanks,Types,"en-GB")
in Typed
