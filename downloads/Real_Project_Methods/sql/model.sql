-- SQLite 3.25+. One row per SKU in Products/Decisions; one observation per SourceID.
-- Decisions is an Excel snapshot. These views independently recompute economics.
CREATE INDEX ix_prices_sku ON Prices(SKU);
CREATE INDEX ix_prices_checked ON Prices(CheckedDate);
CREATE VIEW v_eligible AS
SELECT p.* FROM Prices p CROSS JOIN Settings s
WHERE p.Price>0 AND p.Match='Exact' AND p.UKComparable='Yes' AND p.Include='Yes'
  AND p.CheckedDate IS NOT NULL AND p.CheckedDate<=s.AsOfDate;

CREATE VIEW v_benchmarks AS
WITH ranked AS (
 SELECT e.*, ROW_NUMBER() OVER (
   PARTITION BY e.SKU
   ORDER BY CASE WHEN Availability='In stock' THEN 0 ELSE 1 END, Price,
   (SELECT rowid FROM Prices p WHERE p.SourceID=e.SourceID)
 ) AS PreferenceRank FROM v_eligible e
)
SELECT * FROM ranked WHERE PreferenceRank=1;

CREATE VIEW v_economics AS
WITH priced AS (
 SELECT p.*,b.Price AS Benchmark,b.SourceID,b.Availability,b.CheckedDate,
   COALESCE(p.ShelfOverride,CAST(ROUND(b.Price*(1+s.Premium)*20,8) AS INTEGER)/20.0) AS Shelf,
   CASE WHEN p.BulkThreshold IS NOT NULL AND p.BulkCost IS NOT NULL
     THEN CAST((MAX(p.BulkThreshold,p.MOQ)+p.OrderMultiple-1)/p.OrderMultiple AS INTEGER)*p.OrderMultiple END AS BulkUnits,
   s.VAT,s.TargetGM,s.MinimumGM,s.StrongGM,s.FeeRate,s.MinContribution
 FROM Products p CROSS JOIN Settings s LEFT JOIN v_benchmarks b ON p.SKU=b.SKU
), margins AS (
 SELECT *,1-(BaseCost+LandedExtras)/NULLIF(Shelf/(1+VAT),0) AS BaseGM,
   1-(BulkCost+LandedExtras)/NULLIF(Shelf/(1+VAT),0) AS BulkGM,
   Shelf/(1+VAT)-BaseCost-LandedExtras-Shelf*FeeRate AS BaseContribution,
   Shelf/(1+VAT)-BulkCost-LandedExtras-Shelf*FeeRate AS BulkContribution
 FROM priced
)
SELECT *,CASE WHEN Benchmark IS NULL THEN NULL WHEN BaseGM>=StrongGM THEN 5
 WHEN BaseGM>=TargetGM THEN 4 WHEN BaseGM>=MinimumGM THEN 3 WHEN BaseGM>=0 THEN 2 ELSE 1 END AS Rating,
 CASE WHEN BulkCost IS NULL THEN 'No bulk offer' WHEN BulkCost>=BaseCost THEN 'No unit saving'
 WHEN BaseGM>=TargetGM AND BaseContribution>MinContribution THEN 'Bulk optional'
 WHEN BulkGM>=TargetGM AND BulkContribution>MinContribution THEN 'Bulk required'
 ELSE 'Still below target' END AS BulkVerdictSQL
FROM margins;

CREATE VIEW v_reconciliation AS
SELECT e.SKU,
 CASE WHEN (e.Benchmark IS NULL)<>(d.Benchmark IS NULL) OR ABS(e.Benchmark-d.Benchmark)>0.000001 THEN 1 ELSE 0 END AS BenchmarkMismatch,
 CASE WHEN (e.BaseGM IS NULL)<>(d.BaseGM IS NULL) OR ABS(e.BaseGM-d.BaseGM)>0.000001 THEN 1 ELSE 0 END AS MarginMismatch,
 CASE WHEN e.Rating IS NOT d.Rating THEN 1 ELSE 0 END AS RatingMismatch,
 CASE WHEN e.BulkUnits IS NOT d.BulkUnits THEN 1 ELSE 0 END AS BulkUnitsMismatch
FROM v_economics e JOIN Decisions d ON d.SKU=e.SKU;

CREATE VIEW v_category_summary AS
SELECT p.Category, COUNT(*) AS Products,COUNT(d.Benchmark) AS Benchmarked,
 SUM(CASE WHEN d.Rating>=4 THEN 1 ELSE 0 END) AS MeetsBaseTarget,
 SUM(CASE WHEN d.BulkVerdict='Bulk required' THEN 1 ELSE 0 END) AS BulkRequired,
 SUM(d.PlannedCash) AS PlannedCash, SUM(d.PlannedContribution) AS ContributionBeforeFreight
FROM Products p JOIN Decisions d USING(SKU) GROUP BY p.Category;
