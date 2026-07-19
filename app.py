"""
NovaRetail Customer Intelligence Dashboard
--------------------------------------------------
Interactive Streamlit dashboard for exploring customer behavior segments,
revenue drivers, and churn/decline risk across NovaRetail's regions,
product categories, and sales channels.

Data: NR_dataset.xlsx (99-100 sampled transactions)
Author: [Your Name]
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_confpiig(
    page_title="NovaRetail Customer Intelligence Dashboard",
    page_icon="🛍️",
    layout="wide",
)

# ----------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------

# The raw ProductCategory field contains ~35 near-duplicate labels
# (e.g. "Beauty Products", "Cosmetics", "Health & Beauty" all describe
# the same shopping category). We consolidate them into a manageable
# set of business-relevant categories so charts are actually readable.
CATEGORY_MAP = {
    "Electronics": "Electronics",
    "Home Appliances": "Home & Garden",
    "Home & Garden": "Home & Garden",
    "Furniture": "Home & Garden",
    "Home Improvement": "Home & Garden",
    "Home Decor": "Home & Garden",
    "Furniture & Decor": "Home & Garden",
    "Gardening Tools": "Home & Garden",
    "Outdoor Equipment": "Home & Garden",
    "Clothing": "Clothing & Fashion",
    "Fashion": "Clothing & Fashion",
    "Fashion & Apparel": "Clothing & Fashion",
    "Fashion Accessories": "Clothing & Fashion",
    "Children's Clothing": "Clothing & Fashion",
    "Sportswear": "Clothing & Fashion",
    "Groceries": "Groceries & Food",
    "Grocery": "Groceries & Food",
    "Grocery Items": "Groceries & Food",
    "Food & Beverages": "Groceries & Food",
    "Books": "Books & Media",
    "Books & Magazines": "Books & Media",
    "Toys": "Toys & Gaming",
    "Toys & Games": "Toys & Gaming",
    "Gaming": "Toys & Gaming",
    "Health & Wellness": "Health & Beauty",
    "Health & Beauty": "Health & Beauty",
    "Beauty Products": "Health & Beauty",
    "Beauty & Personal Care": "Health & Beauty",
    "Cosmetics": "Health & Beauty",
    "Health Supplements": "Health & Beauty",
    "Sporting Goods": "Sports & Outdoors",
    "Sports & Outdoors": "Sports & Outdoors",
    "Sports Equipment": "Sports & Outdoors",
    "Automotive": "Automotive",
    "Office Supplies": "Office Supplies",
}


@st.cache_data
def load_data(path: str = "NR_dataset.xlsx") -> pd.DataFrame:
    df = pd.read_excel(path)

    # Drop rows with no behavioral segment label -- they can't be used
    # for segment-based analysis, and there is only a small number of them.
    df = df.dropna(subset=["label"]).copy()

    # Consolidate product categories into readable groups; anything not
    # in the map falls back to its original value so nothing is silently lost.
    df["CategoryGroup"] = df["ProductCategory"].map(CATEGORY_MAP).fillna(df["ProductCategory"])

    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
    df["Month"] = df["TransactionDate"].dt.to_period("M").astype(str)

    return df


df = load_data()

# ----------------------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------------------
st.sidebar.header("Filters")

segments = st.sidebar.multiselect(
    "Customer Segment", options=sorted(df["label"].unique()), default=sorted(df["label"].unique())
)
regions = st.sidebar.multiselect(
    "Region", options=sorted(df["CustomerRegion"].unique()), default=sorted(df["CustomerRegion"].unique())
)
channels = st.sidebar.multiselect(
    "Sales Channel", options=sorted(df["RetailChannel"].unique()), default=sorted(df["RetailChannel"].unique())
)
categories = st.sidebar.multiselect(
    "Product Category", options=sorted(df["CategoryGroup"].unique()), default=sorted(df["CategoryGroup"].unique())
)
age_groups = st.sidebar.multiselect(
    "Age Group", options=sorted(df["CustomerAgeGroup"].unique()), default=sorted(df["CustomerAgeGroup"].unique())
)

date_min, date_max = df["TransactionDate"].min(), df["TransactionDate"].max()
date_range = st.sidebar.date_input("Date Range", value=(date_min, date_max), min_value=date_min, max_value=date_max)

filtered = df[
    df["label"].isin(segments)
    & df["CustomerRegion"].isin(regions)
    & df["RetailChannel"].isin(channels)
    & df["CategoryGroup"].isin(categories)
    & df["CustomerAgeGroup"].isin(age_groups)
]
if len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered = filtered[(filtered["TransactionDate"] >= start) & (filtered["TransactionDate"] <= end)]

st.sidebar.markdown(f"**{len(filtered)}** of {len(df)} transactions match your filters.")

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.title("🛍️ NovaRetail Customer Intelligence Dashboard")
st.caption(
    "Explore revenue, customer segments, and engagement patterns to identify growth "
    "opportunities and early warning signs of customer decline."
)

if filtered.empty:
    st.warning("No transactions match the current filters. Try widening your selection.")
    st.stop()

# ----------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------
total_revenue = filtered["PurchaseAmount"].sum()
avg_order_value = filtered["PurchaseAmount"].mean()
n_customers = filtered["CustomerID"].nunique()
avg_satisfaction = filtered["CustomerSatisfaction"].mean()
decline_share = (filtered["label"] == "Decline").mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Revenue", f"${total_revenue:,.0f}")
k2.metric("Avg Order Value", f"${avg_order_value:,.2f}")
k3.metric("Unique Customers", f"{n_customers}")
k4.metric("Avg Satisfaction", f"{avg_satisfaction:.1f} / 5")
k5.metric("Share in Decline", f"{decline_share:.0f}%")

st.divider()

# ----------------------------------------------------------------------
# ROW 1: Revenue by Segment | Segment Mix
# ----------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Revenue by Customer Segment")
    rev_by_segment = filtered.groupby("label", as_index=False)["PurchaseAmount"].sum().sort_values(
        "PurchaseAmount", ascending=False
    )
    fig = px.bar(
        rev_by_segment, x="label", y="PurchaseAmount", color="label",
        labels={"label": "Segment", "PurchaseAmount": "Revenue ($)"},
        color_discrete_map={"Promising": "#2E86AB", "Growth": "#2CA858", "Stable": "#F2A93B", "Decline": "#D9534F"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Customer Segment Mix")
    seg_counts = filtered.drop_duplicates("CustomerID")["label"].value_counts().reset_index()
    seg_counts.columns = ["label", "count"]
    fig = px.pie(
        seg_counts, names="label", values="count", hole=0.45,
        color="label",
        color_discrete_map={"Promising": "#2E86AB", "Growth": "#2CA858", "Stable": "#F2A93B", "Decline": "#D9534F"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# ROW 2: Revenue by Region | Revenue by Category
# ----------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("Revenue by Region")
    rev_by_region = filtered.groupby("CustomerRegion", as_index=False)["PurchaseAmount"].sum()
    fig = px.bar(rev_by_region, x="CustomerRegion", y="PurchaseAmount", labels={"PurchaseAmount": "Revenue ($)", "CustomerRegion": "Region"})
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Revenue by Product Category")
    rev_by_cat = filtered.groupby("CategoryGroup", as_index=False)["PurchaseAmount"].sum().sort_values(
        "PurchaseAmount", ascending=True
    )
    fig = px.bar(rev_by_cat, x="PurchaseAmount", y="CategoryGroup", orientation="h", labels={"PurchaseAmount": "Revenue ($)", "CategoryGroup": "Category"})
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# ROW 3: Revenue trend | Satisfaction by segment
# ----------------------------------------------------------------------
c5, c6 = st.columns(2)

with c5:
    st.subheader("Revenue Trend Over Time")
    trend = filtered.groupby("Month", as_index=False)["PurchaseAmount"].sum().sort_values("Month")
    fig = px.line(trend, x="Month", y="PurchaseAmount", markers=True, labels={"PurchaseAmount": "Revenue ($)"})
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Satisfaction by Segment")
    fig = px.box(
        filtered, x="label", y="CustomerSatisfaction", color="label",
        color_discrete_map={"Promising": "#2E86AB", "Growth": "#2CA858", "Stable": "#F2A93B", "Decline": "#D9534F"},
        labels={"label": "Segment", "CustomerSatisfaction": "Satisfaction (1-5)"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------
# ROW 4: Channel split | Category performance by segment (heatmap)
# ----------------------------------------------------------------------
c7, c8 = st.columns(2)

with c7:
    st.subheader("Revenue by Sales Channel")
    rev_by_channel = filtered.groupby("RetailChannel", as_index=False)["PurchaseAmount"].sum()
    fig = px.pie(rev_by_channel, names="RetailChannel", values="PurchaseAmount", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

with c8:
    st.subheader("Category Revenue by Segment")
    heat = filtered.pivot_table(index="CategoryGroup", columns="label", values="PurchaseAmount", aggfunc="sum", fill_value=0)
    fig = px.imshow(heat, text_auto=".0f", aspect="auto", color_continuous_scale="Blues", labels=dict(color="Revenue ($)"))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ----------------------------------------------------------------------
# INSIGHTS PANEL
# ----------------------------------------------------------------------
st.subheader("📌 Key Insights")

top_segment = rev_by_segment.iloc[0]["label"]
top_region = rev_by_region.sort_values("PurchaseAmount", ascending=False).iloc[0]["CustomerRegion"]
top_category = rev_by_cat.sort_values("PurchaseAmount", ascending=False).iloc[0]["CategoryGroup"]
decline_df = filtered[filtered["label"] == "Decline"]
decline_satisfaction = decline_df["CustomerSatisfaction"].mean() if not decline_df.empty else float("nan")

insight_col1, insight_col2 = st.columns(2)
with insight_col1:
    st.success(
        f"**Growth opportunity:** {top_segment} customers generate the most revenue "
        f"(${rev_by_segment.iloc[0]['PurchaseAmount']:,.0f}); {top_region} region and "
        f"{top_category} lead overall revenue -- prioritize retention offers and cross-sell "
        f"campaigns here."
    )
with insight_col2:
    if not decline_df.empty:
        st.error(
            f"**Decline warning:** Customers in the Decline segment average "
            f"{decline_satisfaction:.1f}/5 satisfaction, versus {avg_satisfaction:.1f}/5 overall. "
            f"Consider proactive outreach or win-back promotions for this segment."
        )
    else:
        st.info("No Decline-segment transactions in the current filter selection.")

# ----------------------------------------------------------------------
# DATA TABLE
# ----------------------------------------------------------------------
with st.expander("View filtered transaction data"):
    st.dataframe(
        filtered[
            ["CustomerID", "TransactionDate", "CategoryGroup", "PurchaseAmount",
             "CustomerAgeGroup", "CustomerGender", "CustomerRegion",
             "CustomerSatisfaction", "RetailChannel", "label"]
        ].sort_values("TransactionDate", ascending=False),
        use_container_width=True,
    )
