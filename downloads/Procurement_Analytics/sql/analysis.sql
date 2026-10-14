-- Category analysis; missing prices do not become zero margins.
SELECT Category,COUNT(*) Products,COUNT(Benchmark) Priced,
 SUM(CASE WHEN Recommendation='Trial candidate' THEN 1 ELSE 0 END) Trials
FROM v_metrics GROUP BY Category;

-- Highest base margins per category, retaining tied rankings.
WITH ranked AS (
 SELECT SKU,Product,Category,BaseGM,
 DENSE_RANK() OVER(PARTITION BY Category ORDER BY BaseGM DESC) MarginRank
 FROM v_metrics WHERE Benchmark IS NOT NULL
)
SELECT * FROM ranked WHERE MarginRank<=2 ORDER BY Category,MarginRank;

-- Lower unit cost can still mean too much stock and cash exposure.
SELECT SKU,Product,BulkUnits,BulkCash,BulkCover,Recommendation
FROM v_metrics WHERE BulkVerdict='Bulk required' ORDER BY BulkCash DESC;

-- Observation history demonstrates window functions, not a sales trend.
SELECT SKU,Retailer,CheckedDate,Price,
 LAG(Price) OVER(PARTITION BY SKU,Retailer ORDER BY CheckedDate,SourceID) PreviousPrice
FROM Prices WHERE MatchType='Exact';

-- Evidence exceptions for review.
SELECT SKU,Product,Recommendation FROM v_metrics
WHERE Benchmark IS NULL OR Availability<>'In stock';
