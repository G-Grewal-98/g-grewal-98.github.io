let
    Source = LoadCsv("Products.csv", {
        {"SKU", type text},
        {"Product", type text},
        {"Category", type text},
        {"Barcode", type text},
        {"Language", type text},
        {"Supplier", type text},
        {"BaseCost", type number},
        {"BulkThreshold", Int64.Type},
        {"BulkCost", type number},
        {"MOQ", Int64.Type},
        {"OrderMultiple", Int64.Type},
        {"SupplierStock", Int64.Type},
        {"CostDate", type date},
        {"LandedExtras", type number},
        {"DemandRating", Int64.Type},
        {"MonthlySales", type number},
        {"OnHand", Int64.Type},
        {"PlannedQty", Int64.Type},
        {"ShelfOverride", type number},
        {"Active", type text},
        {"CostReview", type text},
        {"Notes", type text},
        {"ProductType", type text}
    })
in
    Source
