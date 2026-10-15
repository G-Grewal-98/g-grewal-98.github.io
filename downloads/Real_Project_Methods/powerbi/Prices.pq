let
    Source = LoadCsv("Prices.csv", {
        {"SourceID", type text},
        {"SKU", type text},
        {"Retailer", type text},
        {"ListingTitle", type text},
        {"URL", type text},
        {"Price", type number},
        {"CheckedDate", type date},
        {"Availability", type text},
        {"Match", type text},
        {"UKComparable", type text},
        {"Include", type text},
        {"Evidence", type text},
        {"Delivery", type number},
        {"DeliveryNotes", type text},
        {"Origin", type text},
        {"SubmittedURL", type text},
        {"Language", type text},
        {"SupplierFormat", type text},
        {"OriginalLink", Int64.Type}
    })
in
    Source
