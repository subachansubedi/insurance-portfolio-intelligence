-- Insurance Portfolio Intelligence
-- 10 dashboard KPI validation questions
-- PostgreSQL syntax

-- Q01. How many policy records are in the fact table?
SELECT COUNT(*) AS policy_records
FROM "FCT.Insurance_Policy_Table";
-- Interpretation: validates the 10,000 policy-record headline.

-- Q02. How many distinct policy numbers are present?
SELECT COUNT(DISTINCT "Policy Number") AS distinct_policy_numbers
FROM "FCT.Insurance_Policy_Table";
-- Interpretation: checks whether one row equals one unique policy.

-- Q03. How many active records are in the portfolio?
SELECT COUNT(*) AS active_records
FROM "FCT.Insurance_Policy_Table"
WHERE "Policy Status" = 'Active';
-- Interpretation: validates the active-record KPI.

-- Q04. What is the active-record percentage?
SELECT ROUND(
    100.0 * COUNT(*) FILTER (WHERE "Policy Status" = 'Active') / COUNT(*), 2
) AS active_percentage
FROM "FCT.Insurance_Policy_Table";
-- Interpretation: validates the dashboard's active share.

-- Q05. What is modeled annual premium for active records?
SELECT ROUND(SUM(
    "Premium Amount" *
    CASE "Payment Frequency"
        WHEN 'Monthly' THEN 12
        WHEN 'Quarterly' THEN 4
        WHEN 'Annually' THEN 1
    END
), 2) AS active_annual_premium
FROM "FCT.Insurance_Policy_Table"
WHERE "Policy Status" = 'Active';
-- Interpretation: validates the active annual-premium KPI.

-- Q06. What is modeled lifetime premium for active records?
SELECT ROUND(SUM(
    "Premium Amount" *
    CASE "Payment Frequency"
        WHEN 'Monthly' THEN 12
        WHEN 'Quarterly' THEN 4
        WHEN 'Annually' THEN 1
    END * "Tenure (Years)"
), 2) AS active_lifetime_premium
FROM "FCT.Insurance_Policy_Table"
WHERE "Policy Status" = 'Active';
-- Interpretation: validates the modeled lifetime-premium measure.

-- Q07. What is modeled premium paid for active records?
SELECT ROUND(SUM(
    "Premium Amount" *
    CASE "Payment Frequency"
        WHEN 'Monthly' THEN 12
        WHEN 'Quarterly' THEN 4
        WHEN 'Annually' THEN 1
    END *
    LEAST(
        "Tenure (Years)",
        GREATEST(
            0,
            EXTRACT(DAY FROM (DATE '2025-07-23' - TO_DATE("Start Date", 'DD-MM-YYYY'))) / 365.25
        )
    )
), 2) AS modeled_paid_premium
FROM "FCT.Insurance_Policy_Table"
WHERE "Policy Status" = 'Active';
-- Interpretation: validates the paid-premium calculation using the report snapshot date.

-- Q08. What share of active lifetime premium is modeled as paid?
WITH active AS (
    SELECT
        "Premium Amount" *
        CASE "Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END AS annual_premium,
        "Tenure (Years)",
        TO_DATE("Start Date", 'DD-MM-YYYY') AS start_date
    FROM "FCT.Insurance_Policy_Table"
    WHERE "Policy Status" = 'Active'
)
SELECT ROUND(
    100.0 * SUM(annual_premium * LEAST("Tenure (Years)", GREATEST(0, DATE '2025-07-23' - start_date) / 365.25))
    / SUM(annual_premium * "Tenure (Years)"), 2
) AS modeled_paid_share
FROM active;
-- Interpretation: validates the paid-versus-lifetime premium KPI.

-- Q09. What share of records are in the two largest protection plans?
SELECT ROUND(
    100.0 * SUM(plan_count) FILTER (WHERE plan_rank <= 2) / SUM(plan_count), 2
) AS top_two_plan_share
FROM (
    SELECT "Policy Code", COUNT(*) AS plan_count,
           DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS plan_rank
    FROM "FCT.Insurance_Policy_Table"
    GROUP BY "Policy Code"
) plans;
-- Interpretation: validates portfolio concentration by protection plan.

-- Q10. What share of active annual premium comes from the top three states?
WITH states AS (
    SELECT "State", SUM(
        "Premium Amount" *
        CASE "Payment Frequency" WHEN 'Monthly' THEN 12 WHEN 'Quarterly' THEN 4 WHEN 'Annually' THEN 1 END
    ) AS annual_premium
    FROM "FCT.Insurance_Policy_Table"
    WHERE "Policy Status" = 'Active'
    GROUP BY "State"
),
ranked AS (
    SELECT *, DENSE_RANK() OVER (ORDER BY annual_premium DESC) AS state_rank
    FROM states
)
SELECT ROUND(100.0 * SUM(annual_premium) FILTER (WHERE state_rank <= 3) / SUM(annual_premium), 2)
    AS top_three_state_share
FROM ranked;
-- Interpretation: validates geographic premium concentration.
