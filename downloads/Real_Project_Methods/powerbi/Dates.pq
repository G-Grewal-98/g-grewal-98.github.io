let
    Source = LoadCsv("Dates.csv", {
        {"Date", type date},
        {"Year", Int64.Type},
        {"Month", Int64.Type},
        {"MonthName", type text}
    })
in
    Source
