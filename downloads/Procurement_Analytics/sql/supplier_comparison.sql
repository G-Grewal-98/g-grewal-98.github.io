-- Fixed basket: 24 units of each SKU. Fictional offers, excluding freight.
-- Offers requiring more units are excluded; a low price alone is not comparable.
WITH eligible AS (
 SELECT o.SKU,p.Product,s.Supplier,o.UnitCost,o.MinUnits,
        o.UnitCost*24 AS NetGoodsCost,
        DENSE_RANK() OVER(PARTITION BY o.SKU ORDER BY o.UnitCost) AS PriceRank
 FROM Offers o
 JOIN Products p ON p.SKU=o.SKU
 JOIN Suppliers s ON s.SupplierID=o.SupplierID
 WHERE o.MinUnits<=24
)
SELECT * FROM eligible ORDER BY SKU,PriceRank,Supplier;
