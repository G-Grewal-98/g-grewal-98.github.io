-- Run against procurement.sqlite. Demonstrates joins, CTEs, windows and exceptions.
-- 1. Category opportunity; NULL margins are never converted into zero-value products.
SELECT * FROM v_category_summary ORDER BY MeetsBaseTarget DESC;

-- 2. Rank price opportunities within category. Confirm recommendation before buying.
WITH opportunities AS (
 SELECT p.Category,d.SKU,p.Product,d.BaseGM,d.Rating,d.Recommendation,
 DENSE_RANK() OVER(PARTITION BY p.Category ORDER BY d.BaseGM DESC) AS MarginRank
 FROM Products p JOIN Decisions d USING(SKU) WHERE d.Benchmark IS NOT NULL
)
SELECT * FROM opportunities WHERE MarginRank<=3 ORDER BY Category,MarginRank;

-- 3. Evidence gaps and unit-basis exceptions.
SELECT p.SKU,p.Product,d.PriceStatus,p.CostReview,d.Explanation
FROM Products p JOIN Decisions d USING(SKU)
WHERE d.Benchmark IS NULL OR p.CostReview='Review' OR d.PriceStatus<>'Current in-stock';

-- 4. Cash tied up at the bulk break. These are hypothetical purchases, not savings.
SELECT SKU,Product,BulkUnits,BulkCash,BulkCover,BulkVerdict,Recommendation
FROM Decisions WHERE BulkVerdict='Bulk required' ORDER BY BulkCash DESC;

-- 5. Retained observation history; comparable only when format and language match.
SELECT SKU,Retailer,CheckedDate,Price,
 LAG(Price) OVER(PARTITION BY SKU,Retailer,URL ORDER BY CheckedDate,SourceID) AS PreviousListedPrice
FROM Prices WHERE Match='Exact' AND CheckedDate IS NOT NULL;

-- 6. Independent model reconciliation. Expected zero rows.
SELECT * FROM v_reconciliation WHERE BenchmarkMismatch+MarginMismatch+RatingMismatch+BulkUnitsMismatch>0;
