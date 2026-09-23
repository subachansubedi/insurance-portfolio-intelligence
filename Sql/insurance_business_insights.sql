-- Insurance Portfolio Intelligence
-- Business questions beyond dashboard KPI validation


-- Q01. Which states have unusually high lapsed and claimed shares?
SELECT "State",
       COUNT(*) AS records,
       COUNT(*) FILTER (WHERE "Policy Status" = 'Lapsed') AS lapsed_records,
       COUNT(*) FILTER (WHERE "Policy Status" = 'Claimed') AS claimed_records,
       ROUND(100.0 * COUNT(*) FILTER (WHERE "Policy Status" IN ('Lapsed','Claimed')) / COUNT(*), 2) AS issue_rate_pct
FROM "FCT.Insurance_Policy_Table"
GROUP BY "State"
ORDER BY issue_rate_pct DESC;
-- Interpretation: identifies states requiring status-assignment or servicing review.

-- Q02. Which plans have the highest modeled annual premium per record?
SELECT "Policy Code",
       COUNT(*) AS records,
       ROUND(SUM("Premium Amount" * CASE "Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END) / COUNT(*), 2) AS annual_premium_per_record
FROM "FCT.Insurance_Policy_Table"
GROUP BY "Policy Code"
ORDER BY annual_premium_per_record DESC;
-- Interpretation: separates popular plans from high-value plans.

-- Q03. Which payment frequencies have the highest average coverage?
SELECT "Payment Frequency",
       COUNT(*) AS records,
       ROUND(AVG("Sum Assured INR/Coverage Amount"), 2) AS average_coverage
FROM "FCT.Insurance_Policy_Table"
GROUP BY "Payment Frequency"
ORDER BY average_coverage DESC;
-- Interpretation: shows whether cash-flow choice is associated with coverage size.

-- Q04. Which policy types have the highest average modeled lifetime premium?
SELECT "Policy Type Code",
       COUNT(*) AS records,
       ROUND(AVG("Premium Amount" * CASE "Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END * "Tenure (Years)"), 2) AS average_lifetime_premium
FROM "FCT.Insurance_Policy_Table"
GROUP BY "Policy Type Code"
ORDER BY average_lifetime_premium DESC;
-- Interpretation: highlights policy types with larger modeled customer value.

-- Q05. Are smoker and non-smoker policies priced differently after annualization?
SELECT c."Smoker Status",
       COUNT(*) AS records,
       ROUND(AVG(p."Premium Amount" * CASE p."Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END), 2) AS average_annual_premium
FROM "FCT.Insurance_Policy_Table" p
JOIN "DM.Customer_Detail_Table" c ON c."Customer ID" = p."Customer ID"
GROUP BY c."Smoker Status"
ORDER BY average_annual_premium DESC;
-- Interpretation: supports an underwriting and pricing review.

-- Q06. Which agents manage the most lapsed records?
SELECT p."Sales Agent Code", a."Sales Agent",
       COUNT(*) FILTER (WHERE p."Policy Status" = 'Lapsed') AS lapsed_records,
       COUNT(*) AS total_records,
       ROUND(100.0 * COUNT(*) FILTER (WHERE p."Policy Status" = 'Lapsed') / COUNT(*), 2) AS lapsed_rate_pct
FROM "FCT.Insurance_Policy_Table" p
LEFT JOIN "DM.Insurance_Agent_Table" a ON a."Agent Code" = p."Sales Agent Code"
GROUP BY p."Sales Agent Code", a."Sales Agent"
HAVING COUNT(*) >= 50
ORDER BY lapsed_rate_pct DESC;
-- Interpretation: compares agent portfolios while avoiding very small denominators.

-- Q07. Which purchase years have the highest surrender rate?
SELECT "Purchase Year",
       COUNT(*) AS records,
       ROUND(100.0 * COUNT(*) FILTER (WHERE "Policy Status" = 'Surrendered') / COUNT(*), 2) AS surrender_rate_pct
FROM "FCT.Insurance_Policy_Table"
GROUP BY "Purchase Year"
ORDER BY "Purchase Year";
-- Interpretation: explores whether surrender varies across acquisition cohorts.

-- Q08. Where are region assignments missing?
SELECT COUNT(*) AS rows_without_region_mapping
FROM "FCT.Insurance_Policy_Table" p
WHERE CASE
    WHEN "State" IN ('Minnesota','Wisconsin','Michigan','North Dakota','South Dakota','Iowa') THEN 'North'
    WHEN "State" IN ('Texas','Florida','Georgia','North Carolina','Tennessee') THEN 'South'
    WHEN "State" IN ('California','Oregon','Washington','Arizona') THEN 'West'
    WHEN "State" IN ('New York','Pennsylvania','Massachusetts','New Jersey') THEN 'East'
    WHEN "State" IN ('Ohio','Illinois','Indiana','Missouri') THEN 'Central'
    ELSE NULL
END IS NULL;
-- Interpretation: counts states not covered by the current five-region mapping.

-- Q09. Which agents carry the most annual premium per policy?
SELECT p."Sales Agent Code", a."Sales Agent",
       COUNT(*) AS records,
       ROUND(SUM(p."Premium Amount" * CASE p."Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END) / COUNT(*), 2) AS premium_per_record
FROM "FCT.Insurance_Policy_Table" p
LEFT JOIN "DM.Insurance_Agent_Table" a ON a."Agent Code" = p."Sales Agent Code"
GROUP BY p."Sales Agent Code", a."Sales Agent"
HAVING COUNT(*) >= 50
ORDER BY premium_per_record DESC;
-- Interpretation: distinguishes high-volume agents from agents with high-value portfolios.

-- Q10. Which records have impossible or warning-level premium conditions?
SELECT
    COUNT(*) FILTER (WHERE "Premium Amount" <= 0) AS non_positive_premium,
    COUNT(*) FILTER (WHERE "Tenure (Years)" <= 0) AS non_positive_tenure,
    COUNT(*) FILTER (
        WHERE TO_DATE("Last Paid Date", 'DD-Mon-YY') < TO_DATE("Start Date", 'DD-MM-YYYY')
    ) AS paid_before_start,
    COUNT(*) FILTER (WHERE "Claim ID" IS NOT NULL AND "Policy Status" NOT IN ('Claimed','Lapsed')) AS claim_id_status_mismatch
FROM "FCT.Insurance_Policy_Table";
-- Interpretation: provides a compact quality-control check before using financial KPIs.
