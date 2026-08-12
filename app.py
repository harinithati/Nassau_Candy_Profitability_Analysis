import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(
    page_title="Nassau Candy | Profitability Analysis",
    page_icon="🍫",
    layout="wide"
)

# -----------------------------
# Load dataset
# -----------------------------
def find_data_file():
    candidates = [
        "Nassau Candy Distributor.csv",
        "Nassau_Candy_Distributor.csv",
        "Nassau Candy Distributor.xlsx",
        "Nassau_Candy_Distributor.xlsx",
        "data.csv"
    ]
    for name in candidates:
        if Path(name).exists():
            return name

    csv_files = list(Path(".").glob("*.csv"))
    if csv_files:
        return str(csv_files[0])

    return None


@st.cache_data
def load_data(file_path):
    if file_path.lower().endswith(".xlsx"):
        return pd.read_excel(file_path)
    return pd.read_csv(file_path)


DATA_FILE = find_data_file()

if DATA_FILE is None:
    st.error(
        "Dataset not found. Upload the Nassau Candy CSV file to the same GitHub repository "
        "as app.py and requirements.txt."
    )
    st.stop()

df = load_data(DATA_FILE)

# -----------------------------
# Column helpers
# -----------------------------
def find_col(possible_names):
    normalized = {str(c).strip().lower().replace("_", " "): c for c in df.columns}
    for name in possible_names:
        key = name.strip().lower().replace("_", " ")
        if key in normalized:
            return normalized[key]

    # flexible contains match
    for c in df.columns:
        lc = str(c).lower().replace("_", " ")
        for name in possible_names:
            if name.lower().replace("_", " ") in lc:
                return c
    return None


customer_col = find_col(["Customer ID", "Customer_ID", "CustomerID"])
sales_col = find_col(["Sales", "Total Sales", "Total_Sales"])
profit_col = find_col(["Gross Profit", "Gross_Profit", "Total Gross Profit", "Total_Gross_Profit"])
units_col = find_col(["Units", "Quantity", "Total Units", "Total_Units"])
product_col = find_col(["Product Name", "Product_Name", "Product"])
region_col = find_col(["Region"])
ship_col = find_col(["Ship Mode", "Ship_Mode"])
division_col = find_col(["Division"])

# Numeric conversion
for col in [sales_col, profit_col, units_col]:
    if col:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# -----------------------------
# Customer-level analysis
# -----------------------------
customer_analysis = None
if customer_col and sales_col and profit_col:
    customer_analysis = (
        df.groupby(customer_col, dropna=False)
        .agg(
            Order_Count=(sales_col, "count"),
            Total_Sales=(sales_col, "sum"),
            Total_Gross_Profit=(profit_col, "sum")
        )
        .reset_index()
    )

    customer_analysis["Gross Margin (%)"] = np.where(
        customer_analysis["Total_Sales"] != 0,
        customer_analysis["Total_Gross_Profit"] /
        customer_analysis["Total_Sales"] * 100,
        0
    )

    customer_analysis["Customer Segment"] = pd.cut(
        customer_analysis["Order_Count"],
        bins=[0, 1, 3, np.inf],
        labels=["One-time", "Repeat", "Loyal"],
        include_lowest=True
    )

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🍫 Nassau Candy")
st.sidebar.caption("Customer & Profitability Analytics")

page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Dashboard",
        "Customer Analysis",
        "Retention Analysis",
        "Product Analysis",
        "Regional Analysis",
        "Shipping Analysis",
        "Division Analysis",
        "Recommendations"
    ]
)

# -----------------------------
# Header
# -----------------------------
st.title("Nassau Candy Profitability Analysis")
st.caption(
    "A data-driven analysis of customer behavior, profitability, product performance, "
    "regional performance, shipping and business opportunities."
)

# -----------------------------
# Executive Dashboard
# -----------------------------
if page == "Executive Dashboard":
    st.header("Executive Dashboard")

    total_sales = df[sales_col].sum() if sales_col else 0
    total_profit = df[profit_col].sum() if profit_col else 0
    total_units = df[units_col].sum() if units_col else 0
    total_customers = df[customer_col].nunique() if customer_col else 0
    margin = (total_profit / total_sales * 100) if total_sales else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Sales", f"{total_sales:,.2f}")
    c2.metric("Gross Profit", f"{total_profit:,.2f}")
    c3.metric("Units Sold", f"{total_units:,.0f}")
    c4.metric("Customers", f"{total_customers:,}")
    c5.metric("Gross Margin", f"{margin:.2f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Business Snapshot")
        st.write(
            f"""
            - **Transaction records:** {len(df):,}
            - **Unique customers:** {total_customers:,}
            - **Missing values:** {int(df.isna().sum().sum())}
            - **Duplicate rows:** {int(df.duplicated().sum())}
            """
        )

    with right:
        if region_col and sales_col:
            region_sales = df.groupby(region_col)[sales_col].sum().sort_values(ascending=False)
            fig, ax = plt.subplots()
            region_sales.plot(kind="bar", ax=ax)
            ax.set_title("Sales by Region")
            ax.set_xlabel("Region")
            ax.set_ylabel("Sales")
            plt.xticks(rotation=0)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    st.subheader("Key Business Findings")
    findings = [
        "55.73% of customers are One-time customers.",
        "Repeat customers contribute approximately 64.70% of total gross profit.",
        "The 1→2 customer retention rate is 48.06%.",
        "The top five products generate approximately 95% of total gross profit.",
        "Chocolate contributes approximately 95.06% of total gross profit.",
        "Pacific is the strongest region by total sales and profit.",
        "Kazookles has a 7.69% gross margin and requires investigation."
    ]
    for finding in findings:
        st.markdown(f"• {finding}")

# -----------------------------
# Customer Analysis
# -----------------------------
elif page == "Customer Analysis":
    st.header("Customer Segmentation & Profitability")

    if customer_analysis is None:
        st.warning("Customer ID, Sales and Gross Profit columns are required.")
        st.stop()

    segment_summary = (
        customer_analysis.groupby("Customer Segment", observed=True)
        .agg(
            Customers=(customer_col, "count"),
            Total_Sales=("Total_Sales", "sum"),
            Total_Profit=("Total_Gross_Profit", "sum"),
            Average_Profit=("Total_Gross_Profit", "mean")
        )
        .reset_index()
    )

    segment_summary["Customer %"] = (
        segment_summary["Customers"] / len(customer_analysis) * 100
    )
    segment_summary["Profit %"] = (
        segment_summary["Total_Profit"] /
        segment_summary["Total_Profit"].sum() * 100
    )

    st.dataframe(segment_summary.round(2), use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots()
        ax.bar(segment_summary["Customer Segment"].astype(str),
               segment_summary["Customers"])
        ax.set_title("Customers by Segment")
        ax.set_ylabel("Customers")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.bar(segment_summary["Customer Segment"].astype(str),
               segment_summary["Total_Profit"])
        ax.set_title("Profit by Customer Segment")
        ax.set_ylabel("Gross Profit")
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.info(
        "Repeat customers are the main total-profit engine, while Loyal customers "
        "have the highest average profit per customer."
    )

# -----------------------------
# Retention
# -----------------------------
elif page == "Retention Analysis":
    st.header("Customer Retention Analysis")

    if customer_analysis is None:
        st.warning("Customer-level analysis could not be created.")
        st.stop()

    order_summary = (
        customer_analysis.groupby("Order_Count")
        .agg(
            Customers=(customer_col, "count"),
            Average_Sales=("Total_Sales", "mean"),
            Average_Profit=("Total_Gross_Profit", "mean")
        )
        .reset_index()
        .sort_values("Order_Count")
    )

    order_summary["Retention (%)"] = (
        order_summary["Customers"] /
        order_summary["Customers"].shift(1) * 100
    )

    st.dataframe(order_summary.round(2), use_container_width=True)

    if len(order_summary) >= 2:
        first = order_summary.iloc[0]
        second = order_summary.iloc[1]
        retention = second["Customers"] / first["Customers"] * 100
        drop = first["Customers"] - second["Customers"]

        c1, c2 = st.columns(2)
        c1.metric("1→2 Retention", f"{retention:.2f}%")
        c2.metric("Customers Lost", f"{drop:,.0f}")

    fig, ax = plt.subplots()
    ax.plot(
        order_summary["Order_Count"],
        order_summary["Customers"],
        marker="o"
    )
    ax.set_title("Customer Drop-Off by Order Count")
    ax.set_xlabel("Order Count")
    ax.set_ylabel("Customers")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# -----------------------------
# Product Analysis
# -----------------------------
elif page == "Product Analysis":
    st.header("Product Profitability")

    if not product_col or not sales_col or not profit_col:
        st.warning("Product, Sales and Gross Profit columns are required.")
        st.stop()

    product_summary = (
        df.groupby(product_col)
        .agg(
            Total_Sales=(sales_col, "sum"),
            Total_Gross_Profit=(profit_col, "sum")
        )
        .reset_index()
    )

    product_summary["Gross Margin (%)"] = np.where(
        product_summary["Total_Sales"] != 0,
        product_summary["Total_Gross_Profit"] /
        product_summary["Total_Sales"] * 100,
        0
    )

    product_summary["Profit %"] = (
        product_summary["Total_Gross_Profit"] /
        product_summary["Total_Gross_Profit"].sum() * 100
    )

    product_summary = product_summary.sort_values(
        "Total_Gross_Profit", ascending=False
    )

    st.dataframe(product_summary.round(2), use_container_width=True)

    top10 = product_summary.head(10)

    fig, ax = plt.subplots()
    ax.barh(
        top10[product_col].astype(str)[::-1],
        top10["Total_Gross_Profit"][::-1]
    )
    ax.set_title("Top Products by Gross Profit")
    ax.set_xlabel("Gross Profit")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.warning(
        "Kazookles has a 7.69% gross margin and should be investigated for pricing "
        "and cost-structure issues."
    )

# -----------------------------
# Regional
# -----------------------------
elif page == "Regional Analysis":
    st.header("Regional Performance")

    if not region_col or not sales_col or not profit_col:
        st.warning("Region, Sales and Gross Profit columns are required.")
        st.stop()

    region_summary = (
        df.groupby(region_col)
        .agg(
            Total_Sales=(sales_col, "sum"),
            Total_Gross_Profit=(profit_col, "sum")
        )
        .reset_index()
    )

    region_summary["Gross Margin (%)"] = (
        region_summary["Total_Gross_Profit"] /
        region_summary["Total_Sales"] * 100
    )
    region_summary["Profit %"] = (
        region_summary["Total_Gross_Profit"] /
        region_summary["Total_Gross_Profit"].sum() * 100
    )

    st.dataframe(region_summary.round(2), use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(
        region_summary[region_col].astype(str),
        region_summary["Total_Gross_Profit"]
    )
    ax.set_title("Gross Profit by Region")
    ax.set_ylabel("Gross Profit")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# -----------------------------
# Shipping
# -----------------------------
elif page == "Shipping Analysis":
    st.header("Shipping Performance")

    if not ship_col or not sales_col or not profit_col:
        st.warning("Ship Mode, Sales and Gross Profit columns are required.")
        st.stop()

    shipping = (
        df.groupby(ship_col)
        .agg(
            Total_Sales=(sales_col, "sum"),
            Total_Gross_Profit=(profit_col, "sum")
        )
        .reset_index()
    )
    shipping["Gross Margin (%)"] = (
        shipping["Total_Gross_Profit"] /
        shipping["Total_Sales"] * 100
    )
    shipping["Profit %"] = (
        shipping["Total_Gross_Profit"] /
        shipping["Total_Gross_Profit"].sum() * 100
    )

    st.dataframe(shipping.round(2), use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(
        shipping[ship_col].astype(str),
        shipping["Total_Gross_Profit"]
    )
    ax.set_title("Gross Profit by Shipping Mode")
    ax.set_ylabel("Gross Profit")
    plt.xticks(rotation=20)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# -----------------------------
# Division
# -----------------------------
elif page == "Division Analysis":
    st.header("Division Performance")

    if not division_col or not sales_col or not profit_col:
        st.warning("Division, Sales and Gross Profit columns are required.")
        st.stop()

    division = (
        df.groupby(division_col)
        .agg(
            Total_Sales=(sales_col, "sum"),
            Total_Gross_Profit=(profit_col, "sum")
        )
        .reset_index()
    )
    division["Gross Margin (%)"] = (
        division["Total_Gross_Profit"] /
        division["Total_Sales"] * 100
    )
    division["Profit %"] = (
        division["Total_Gross_Profit"] /
        division["Total_Gross_Profit"].sum() * 100
    )

    st.dataframe(division.round(2), use_container_width=True)

    fig, ax = plt.subplots()
    ax.bar(
        division[division_col].astype(str),
        division["Total_Gross_Profit"]
    )
    ax.set_title("Gross Profit by Division")
    ax.set_ylabel("Gross Profit")
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# -----------------------------
# Recommendations
# -----------------------------
elif page == "Recommendations":
    st.header("Business Recommendations")

    recommendations = {
        "1. Increase One-time → Repeat conversion":
            "55.73% of customers are One-time customers. Use follow-up communication, personalized offers and second-purchase incentives.",
        "2. Convert high-value Repeat customers into Loyal customers":
            "Repeat customers generate 64.70% of total gross profit, while Loyal customers have the highest average profit per customer.",
        "3. Protect the top five products":
            "Approximately 95% of gross profit comes from the top five products. Maintain inventory availability and targeted marketing.",
        "4. Investigate low-margin products":
            "Kazookles has a 7.69% gross margin and should be reviewed for pricing, costs, discounts and supplier economics.",
        "5. Protect strong regions and develop growth regions":
            "Pacific is strongest by absolute profit, while Gulf provides an opportunity for additional sales volume.",
        "6. Protect the Chocolate division":
            "Chocolate contributes approximately 95.06% of total gross profit and is the core business driver.",
        "7. Treat shipping as a secondary lever":
            "Shipping modes have broadly similar margins, so customer retention and product strategy should receive greater priority."
    }

    for title, text in recommendations.items():
        with st.container(border=True):
            st.subheader(title)
            st.write(text)

st.sidebar.divider()
st.sidebar.caption("Nassau Candy Profitability Analysis • Unified Mentor Internship Project")
