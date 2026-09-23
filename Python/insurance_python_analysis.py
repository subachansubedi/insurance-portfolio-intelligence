"""
Run this file from a folder that contains an insurance_data folder with the
seven source CSV files. The analysis uses Pandas, NumPy, Matplotlib, and
Seaborn only. It creates 15 PNG charts and a CSV results file.
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


DATA_FOLDER = "../insurance_data"
OUTPUT_FOLDER = "python_visual_outputs"


def read_source(file_name, header_row):
    return pd.read_csv(os.path.join(DATA_FOLDER, file_name), skiprows=header_row).dropna(axis=1, how="all")


def save_chart(file_name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FOLDER, file_name), dpi=150)
    plt.close()


def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    sns.set_style("whitegrid")
    policy = read_source("FCT.Insurance_Policy_Table.csv", 4)
    customer = read_source("DM.Customer_Detail_Table.csv", 6)
    agents = read_source("DM.Insurance_Agent_Table.csv", 4)

    policy["Start Date"] = pd.to_datetime(policy["Start Date"], dayfirst=True)
    policy["Date of Purchase"] = pd.to_datetime(policy["Date of Purchase"], dayfirst=True)
    policy["Annual Premium"] = policy["Premium Amount"] * policy["Payment Frequency"].map(
        {"Monthly": 12, "Quarterly": 4, "Annually": 1}
    )
    policy["Lifetime Premium"] = policy["Annual Premium"] * policy["Tenure (Years)"]
    policy["Paid Years"] = ((pd.Timestamp("2025-07-23") - policy["Start Date"]).dt.days / 365.25).clip(lower=0)
    policy["Modeled Paid Premium"] = policy["Annual Premium"] * policy["Paid Years"].clip(
        upper=policy["Tenure (Years)"]
    )
    policy["Paid Share"] = policy["Modeled Paid Premium"] / policy["Lifetime Premium"] * 100
    policy = policy.merge(customer[["Customer ID", "Gender", "Current Age", "Smoker Status", "Occupation"]], on="Customer ID", how="left")
    policy = policy.merge(agents[["Agent Code", "Sales Agent"]], left_on="Sales Agent Code", right_on="Agent Code", how="left")

    answers = []

    def add_answer(question, topic, method, answer, insight):
        answers.append([question, topic, method, answer, insight])

    # Q01: portfolio status mix
    status = policy["Policy Status"].value_counts()
    add_answer("Q01", "Portfolio status mix", "Counts and percentages",
               f"{status.get('Active', 0):,} active records ({status.get('Active', 0) / len(policy) * 100:.2f}%)",
               "Active policies dominate the stored portfolio, while surrendered records are the main non-active group.")
    plt.figure(figsize=(7, 4))
    sns.barplot(x=status.index, y=status.values, color="#1f4e79")
    plt.title("Q01 - Policy status mix")
    plt.ylabel("Policy records")
    save_chart("q01_status_mix.png")

    # Q02: premium by status
    premium_status = policy.groupby("Policy Status", as_index=False)["Annual Premium"].sum().sort_values("Annual Premium", ascending=False)
    top_status = premium_status.iloc[0]
    add_answer("Q02", "Annual premium by status", "Groupby sum",
               f"{top_status['Policy Status']} records hold ${top_status['Annual Premium']:,.0f} in modeled annual premium",
               "The annual-premium view shows where the portfolio's recurring premium exposure sits by policy status.")
    plt.figure(figsize=(7, 4))
    sns.barplot(data=premium_status, x="Policy Status", y="Annual Premium", color="#2a9d8f")
    plt.title("Q02 - Modeled annual premium by status")
    plt.ylabel("Annual premium ($)")
    save_chart("q02_premium_status.png")

    # Q03: policy code mix
    plan = policy["Policy Code"].value_counts().head(8)
    add_answer("Q03", "Policy plan mix", "Value counts",
               f"{plan.index[0]} is the largest plan with {plan.iloc[0]:,} records",
               "A small number of policy plans account for a large share of records, making them important for service and data-quality reviews.")
    plt.figure(figsize=(8, 4.5))
    sns.barplot(x=plan.values, y=plan.index, color="#457b9d")
    plt.title("Q03 - Largest policy plans")
    plt.xlabel("Policy records")
    save_chart("q03_policy_plans.png")

    # Q04: state concentration
    state = policy.groupby("State", as_index=False)["Annual Premium"].sum().sort_values("Annual Premium", ascending=False)
    top_three_share = state.head(3)["Annual Premium"].sum() / state["Annual Premium"].sum() * 100
    add_answer("Q04", "Geographic premium concentration", "Groupby sum and share",
               f"Top three states represent {top_three_share:.2f}% of modeled annual premium",
               "Premium is concentrated in a small number of states, so state-level data quality has a direct reporting impact.")
    plt.figure(figsize=(8, 5))
    sns.barplot(data=state.head(10), y="State", x="Annual Premium", color="#6a4c93")
    plt.title("Q04 - Top states by modeled annual premium")
    plt.xlabel("Annual premium ($)")
    save_chart("q04_state_premium.png")

    # Q05: age and premium
    age_summary = policy.groupby("Current Age", as_index=False)["Annual Premium"].mean()
    age_corr = policy["Current Age"].corr(policy["Annual Premium"])
    add_answer("Q05", "Age and annual premium", "Pearson correlation",
               f"Correlation between current age and annual premium is {age_corr:.2f}",
               "The relationship is a simple portfolio association. It helps identify whether premium levels differ across age bands, but does not explain why.")
    plt.figure(figsize=(8, 4.5))
    sns.scatterplot(data=policy.sample(min(2500, len(policy)), random_state=1), x="Current Age", y="Annual Premium", alpha=0.35)
    plt.title("Q05 - Current age and annual premium")
    plt.ylabel("Annual premium ($)")
    save_chart("q05_age_premium.png")

    # Q06: smoker premium comparison
    smoker = policy.groupby("Smoker Status", as_index=False)["Annual Premium"].mean()
    smoker_diff = smoker["Annual Premium"].max() - smoker["Annual Premium"].min()
    add_answer("Q06", "Smoker status and premium", "Groupby mean",
               f"Average annual premium differs by ${smoker_diff:,.0f} between smoker groups",
               "The comparison identifies a pricing difference in the stored portfolio and can support underwriting review.")
    plt.figure(figsize=(6, 4))
    sns.barplot(data=smoker, x="Smoker Status", y="Annual Premium", color="#e76f51")
    plt.title("Q06 - Average premium by smoker status")
    plt.ylabel("Average annual premium ($)")
    save_chart("q06_smoker_premium.png")

    # Q07: payment frequency
    frequency = policy.groupby("Payment Frequency", as_index=False).agg(
        policies=("Policy Number", "count"), average_premium=("Annual Premium", "mean")
    )
    most_frequency = frequency.loc[frequency["policies"].idxmax()]
    add_answer("Q07", "Payment frequency", "Groupby count and mean",
               f"{most_frequency['Payment Frequency']} is most common with {int(most_frequency['policies']):,} records",
               "Payment frequency affects both customer cash flow and how annual premium should be calculated.")
    plt.figure(figsize=(7, 4))
    sns.barplot(data=frequency, x="Payment Frequency", y="policies", color="#f4a261")
    plt.title("Q07 - Policy records by payment frequency")
    plt.ylabel("Policy records")
    save_chart("q07_payment_frequency.png")

    # Q08: tenure and lifetime premium
    tenure = policy.groupby("Tenure (Years)", as_index=False)["Lifetime Premium"].mean()
    tenure_corr = policy["Tenure (Years)"].corr(policy["Lifetime Premium"])
    add_answer("Q08", "Tenure and lifetime premium", "Pearson correlation",
               f"Correlation between tenure and lifetime premium is {tenure_corr:.2f}",
               "Longer tenure generally creates more modeled lifetime premium because annual premium is multiplied across more years.")
    plt.figure(figsize=(8, 4))
    sns.barplot(data=tenure, x="Tenure (Years)", y="Lifetime Premium", color="#2a9d8f")
    plt.title("Q08 - Average modeled lifetime premium by tenure")
    plt.ylabel("Lifetime premium ($)")
    save_chart("q08_tenure_lifetime.png")

    # Q09: paid share
    paid_status = policy[policy["Policy Status"] == "Active"]
    paid_share = paid_status["Modeled Paid Premium"].sum() / paid_status["Lifetime Premium"].sum() * 100
    add_answer("Q09", "Modeled paid versus lifetime premium", "Ratio of sums",
               f"Modeled paid premium is {paid_share:.2f}% of active lifetime premium",
               "Most active lifetime value remains modeled as future premium rather than paid premium. It is not the same as a collections or arrears measure.")
    plt.figure(figsize=(5, 4))
    plt.pie([paid_share, 100 - paid_share], labels=["Modeled paid", "Modeled remaining"], autopct="%.1f%%", colors=["#1f4e79", "#d9e2f3"])
    plt.title("Q09 - Active premium composition")
    save_chart("q09_paid_remaining.png")

    # Q10: claims and status
    claim_status = policy.assign(has_claim=policy["Claim ID"].notna()).groupby("Policy Status")["has_claim"].mean().sort_values(ascending=False) * 100
    add_answer("Q10", "Claim ID coverage by status", "Groupby percentage",
               f"{claim_status.index[0]} has the highest share of records with Claim IDs ({claim_status.iloc[0]:.2f}%)",
               "Claim ID availability varies by status, so claim-related reporting should be checked against the actual policy-status definition.")
    plt.figure(figsize=(7, 4))
    sns.barplot(x=claim_status.index, y=claim_status.values, color="#d1495b")
    plt.title("Q10 - Records with Claim IDs by policy status")
    plt.ylabel("Records with Claim ID (%)")
    save_chart("q10_claim_status.png")

    # Q11: underwriting expenses
    expense = policy.groupby("Policy Status", as_index=False)["Underwriting expenses"].mean().sort_values("Underwriting expenses", ascending=False)
    add_answer("Q11", "Underwriting expense", "Groupby mean",
               f"{expense.iloc[0]['Policy Status']} records have the highest average expense at ${expense.iloc[0]['Underwriting expenses']:,.2f}",
               "Average underwriting expense differs by status, which can help prioritize a review of acquisition and servicing cost.")
    plt.figure(figsize=(7, 4))
    sns.barplot(data=expense, x="Policy Status", y="Underwriting expenses", color="#8ab17d")
    plt.title("Q11 - Average underwriting expense by status")
    plt.ylabel("Average expense ($)")
    save_chart("q11_underwriting_expense.png")

    # Q12: loan eligibility
    loan = policy.groupby("Loan Eligible", as_index=False).agg(
        policies=("Policy Number", "count"), average_coverage=("Sum Assured INR/Coverage Amount", "mean")
    )
    loan_share = policy["Loan Eligible"].value_counts(normalize=True).get("Yes", 0) * 100
    add_answer("Q12", "Loan eligibility", "Counts and percentages",
               f"{loan_share:.2f}% of records are marked loan eligible",
               "Loan eligibility is a major product and customer characteristic that can be used to compare coverage and premium segments.")
    plt.figure(figsize=(6, 4))
    sns.barplot(data=loan, x="Loan Eligible", y="policies", color="#577590")
    plt.title("Q12 - Policy records by loan eligibility")
    plt.ylabel("Policy records")
    save_chart("q12_loan_eligibility.png")

    # Q13: agent workload
    agent = policy.groupby("Sales Agent", as_index=False).agg(
        policies=("Policy Number", "count"), annual_premium=("Annual Premium", "sum")
    ).sort_values("annual_premium", ascending=False)
    top_agent = agent.iloc[0]
    add_answer("Q13", "Sales agent performance", "Groupby count and sum",
               f"{top_agent['Sales Agent']} leads with ${top_agent['annual_premium']:,.0f} modeled annual premium",
               "The ranking highlights premium responsibility by agent, but it should be paired with territory and product mix before judging performance.")
    plt.figure(figsize=(8, 5))
    sns.barplot(data=agent.head(10), y="Sales Agent", x="annual_premium", color="#1f4e79")
    plt.title("Q13 - Top agents by modeled annual premium")
    plt.xlabel("Annual premium ($)")
    save_chart("q13_agent_premium.png")

    # Q14: purchase year trend
    year = policy.groupby("Purchase Year", as_index=False).agg(
        policies=("Policy Number", "count"), annual_premium=("Annual Premium", "sum")
    )
    peak_year = year.loc[year["policies"].idxmax()]
    add_answer("Q14", "Purchase-year trend", "Groupby count",
               f"{int(peak_year['Purchase Year'])} had the most records with {int(peak_year['policies']):,}",
               "The purchase-year pattern helps show when the portfolio was built and provides context for maturity and paid-premium measures.")
    plt.figure(figsize=(9, 4))
    sns.lineplot(data=year, x="Purchase Year", y="policies", marker="o", color="#457b9d")
    plt.title("Q14 - Policy records by purchase year")
    plt.ylabel("Policy records")
    save_chart("q14_purchase_year.png")

    # Q15: duplicate policy numbers
    duplicates = policy["Policy Number"].duplicated(keep=False)
    duplicate_count = duplicates.sum()
    unique_policy_share = policy["Policy Number"].nunique() / len(policy) * 100
    add_answer("Q15", "Policy-number data quality", "Duplicate count and uniqueness rate",
               f"{duplicate_count:,} rows share repeated policy numbers; uniqueness is {unique_policy_share:.2f}%",
               "Repeated policy identifiers can affect policy counts, premium totals, and any KPI that assumes one row equals one policy.")
    plt.figure(figsize=(5, 4))
    plt.bar(["Unique rows", "Repeated-ID rows"], [len(policy) - duplicate_count, duplicate_count], color=["#2a9d8f", "#e76f51"])
    plt.title("Q15 - Policy-number uniqueness check")
    plt.ylabel("Rows")
    save_chart("q15_duplicate_policy_ids.png")

    result = pd.DataFrame(answers, columns=["question", "topic", "method", "answer", "business_insight"])
    result.to_csv(os.path.join(OUTPUT_FOLDER, "15_python_results.csv"), index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
