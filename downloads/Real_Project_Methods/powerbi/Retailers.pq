let
    Source = LoadCsv("Retailers.csv", {
        {"Retailer", type text}
    })
in
    Source
