CREATE TABLE Products (
 SKU TEXT PRIMARY KEY NOT NULL, Product TEXT NOT NULL, Category TEXT NOT NULL,
 BaseCost REAL NOT NULL CHECK(BaseCost>0), BulkCost REAL CHECK(BulkCost>0),
 BulkThreshold INTEGER NOT NULL CHECK(BulkThreshold>0), OrderMultiple INTEGER NOT NULL CHECK(OrderMultiple>0),
 MonthlyDemand REAL CHECK(MonthlyDemand>0), OnHand INTEGER NOT NULL CHECK(OnHand>=0)
);
CREATE TABLE Prices (
 SourceID TEXT PRIMARY KEY NOT NULL, SKU TEXT NOT NULL REFERENCES Products(SKU),
 Retailer TEXT NOT NULL, Price REAL CHECK(Price>0), CheckedDate TEXT NOT NULL,
 Availability TEXT NOT NULL, MatchType TEXT NOT NULL
);
CREATE TABLE Settings (VAT REAL, TargetGM REAL, Premium REAL, FeeRate REAL, MaxCover REAL, FreshDays INTEGER, AsOfDate TEXT);
INSERT INTO Settings VALUES (.2,.3,.1,.015,3,30,'2026-10-14');
CREATE VIEW v_benchmarks AS
WITH eligible AS (
 SELECT p.*, ROW_NUMBER() OVER (PARTITION BY SKU ORDER BY
 CASE WHEN Availability='In stock' THEN 0 ELSE 1 END, Price, CheckedDate DESC, SourceID) AS rn
 FROM Prices p CROSS JOIN Settings s
 WHERE MatchType='Exact' AND CheckedDate<=s.AsOfDate
 AND julianday(s.AsOfDate)-julianday(CheckedDate)<=s.FreshDays
)
SELECT * FROM eligible WHERE rn=1;
CREATE VIEW v_metrics AS
WITH shelf AS (
 SELECT p.*,b.Price Benchmark,b.Availability,b.Retailer,b.SourceID,
 CAST(ROUND(b.Price*(1+s.Premium)*20,8) AS INTEGER)/20.0 AS Shelf,
 CAST((p.BulkThreshold+p.OrderMultiple-1)/p.OrderMultiple AS INTEGER)*p.OrderMultiple BulkUnits,
 s.VAT,s.TargetGM,s.FeeRate,s.MaxCover
 FROM Products p CROSS JOIN Settings s LEFT JOIN v_benchmarks b USING(SKU)
), economics AS (
 SELECT *,1-BaseCost/NULLIF(Shelf/(1+VAT),0) BaseGM,
 1-BulkCost/NULLIF(Shelf/(1+VAT),0) BulkGM,
 Shelf/(1+VAT)-BaseCost-Shelf*FeeRate BaseContribution,
 Shelf/(1+VAT)-BulkCost-Shelf*FeeRate BulkContribution,
 BulkUnits*BulkCost*(1+VAT) BulkCash,
 (OnHand+BulkUnits)/NULLIF(MonthlyDemand,0) BulkCover
 FROM shelf
), verdicts AS (
 SELECT *,CASE WHEN Benchmark IS NULL THEN 'Missing evidence'
 WHEN BulkCost IS NULL THEN 'No bulk offer'
 WHEN BulkCost>=BaseCost THEN 'No unit saving'
 WHEN BaseGM>=TargetGM AND BaseContribution>0 THEN 'Bulk optional'
 WHEN BulkGM>=TargetGM AND BulkContribution>0 THEN 'Bulk required'
 ELSE 'Below target' END BulkVerdict
 FROM economics
)
SELECT *, CASE WHEN Benchmark IS NULL THEN 'Research price'
 WHEN Availability<>'In stock' THEN 'Verify availability'
 WHEN BaseGM>=TargetGM AND BaseContribution>0 THEN 'Trial candidate'
 WHEN BulkVerdict='Bulk required' AND (BulkCover IS NULL OR BulkCover>MaxCover) THEN 'Review stock exposure'
 WHEN BulkVerdict='Bulk required' THEN 'Bulk candidate'
 ELSE 'Below target' END Recommendation
FROM verdicts;
