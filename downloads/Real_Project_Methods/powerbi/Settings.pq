let
    Source = LoadCsv("Settings.csv", {
        {"AsOfDate", type date},
        {"VAT", type number},
        {"TargetGM", type number},
        {"MinimumGM", type number},
        {"StrongGM", type number},
        {"Premium", type number},
        {"FeeRate", type number},
        {"FreshDays", type number},
        {"MaxCover", type number},
        {"MinDemand", type number},
        {"CashBudget", type number},
        {"MinimumOrder", type number},
        {"TermsConfirmed", type text},
        {"Freight", type number},
        {"MinContribution", type number},
        {"OrderSupplier", type text}
    })
in
    Source
