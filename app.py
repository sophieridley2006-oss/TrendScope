import streamlit as st
import pandas as pd
import re
from collections import Counter

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="TrendScope", layout="wide")

# -------------------------------
# STYLING
# -------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main {
    background-color: #f8fafc;
}

h1 {
    color: #0f172a;
    font-size: 3rem !important;
    font-weight: 800 !important;
}
h2, h3 {
    color: #0f172a;
}

p, span {
    color: #334155;
}

label {
    color: #0f172a !important;
}

div[data-testid="stFileUploader"],
div[data-testid="stSelectbox"] {
    background: #ffffff;
    border-radius: 10px;
    padding: 0.5rem;
    border: 1px solid #e2e8f0;
}

.card {
    background: #1e293b;
    border-radius: 14px;
    padding: 1.2rem;
    border: 1px solid #334155;
}

.card, .card * {
    color: #e2e8f0 !important;
}

.metric-value {
    color: #38bdf8;
    font-size: 2.2rem;
    font-weight: 700;
}

.insight-box {
    background: #2563eb;
    border-radius: 12px;
    padding: 1rem;
    color: white !important;
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# TITLE
# -------------------------------
st.title("TrendScope")
st.markdown(
    "<p class='subtitle'>A trend intelligence dashboard for exploring YouTube virality by category and country.</p>",
    unsafe_allow_html=True
)

# -------------------------------
# FILE UPLOAD
# -------------------------------
uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []

    country_map = {
        "us": "USA",
        "gb": "UK",
        "in": "India",
        "jp": "Japan",
        "kr": "South Korea",
        "mx": "Mexico",
        "br": "Brazil",
        "ca": "Canada",
        "de": "Germany",
        "fr": "France",
        "ru": "Russia"
    }

    for uploaded_file in uploaded_files:
        temp_df = pd.read_csv(uploaded_file)
        country_code = uploaded_file.name.lower().split("_")[0]
        temp_df["country"] = country_map.get(country_code, "Unknown")
        all_dfs.append(temp_df)

    df = pd.concat(all_dfs, ignore_index=True)


    # -------------------------------
    # DATA CLEANING
    # -------------------------------
    df["publish_time"] = pd.to_datetime(
        df["publish_time"], errors="coerce", utc=True
    ).dt.tz_localize(None)

    # Convert weird trending_date format like 26.26.02 safely
    df["trending_date"] = pd.to_datetime(
        df["trending_date"].astype(str),
        format="%y.%d.%m",
        errors="coerce"
    )

    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    df["likes"] = pd.to_numeric(df["likes"], errors="coerce")
    df["comments"] = pd.to_numeric(df["comments"], errors="coerce")

    df["like_ratio"] = df["likes"] / df["views"]
    df["comment_ratio"] = df["comments"] / df["views"]
    df["title_length"] = df["title"].astype(str).str.len()

    df["trend_speed_hours"] = (
        (df["trending_date"] - df["publish_time"]).dt.total_seconds() / 3600
    )

    df["publish_hour"] = df["publish_time"].dt.hour

    # -------------------------------
    # CATEGORY MAP
    # -------------------------------
    category_map = {
        1: "Film & Animation",
        2: "Autos & Vehicles",
        10: "Music",
        15: "Pets & Animals",
        17: "Sports",
        19: "Travel & Events",
        20: "Gaming",
        22: "People & Blogs",
        23: "Comedy",
        24: "Entertainment",
        25: "News & Politics",
        26: "Howto & Style",
        27: "Education",
        28: "Science & Tech"
    }

    df["category"] = df["category_id"].map(category_map)
    df = df.dropna(subset=["category"])

    # -------------------------------
    # FILTERS
    # -------------------------------
    st.markdown("### Filters")
    col1, col2 = st.columns(2)

    with col1:
        selected_country = st.selectbox(
            "Select Country",
            sorted(df["country"].dropna().unique())
        )

    with col2:
        selected_category = st.selectbox(
            "Select Category",
            sorted(df["category"].dropna().unique())
        )

    filtered = df[
        (df["country"] == selected_country) &
        (df["category"] == selected_category)
    ].copy()

    # -------------------------------
    # DISPLAY
    # -------------------------------
    st.markdown(f"## {selected_category} in {selected_country}")

    if not filtered.empty:
        avg_views = int(filtered["views"].mean())
        like_ratio = filtered["like_ratio"].mean()
        comment_ratio = filtered["comment_ratio"].mean()
        title_len = filtered["title_length"].mean()

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(
                f"<div class='card'><div>Avg Views</div><div class='metric-value'>{avg_views:,}</div></div>",
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"<div class='card'><div>Like Rate</div><div class='metric-value'>{like_ratio:.2%}</div></div>",
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f"<div class='card'><div>Comment Rate</div><div class='metric-value'>{comment_ratio:.2%}</div></div>",
                unsafe_allow_html=True
            )

        with c4:
            st.markdown(
                f"<div class='card'><div>Avg Title Length</div><div class='metric-value'>{title_len:.1f}</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("### Trend Decoder")
        st.markdown(
            f"<div class='insight-box'>"
            f"{selected_category} videos in {selected_country} average {avg_views:,} views, "
            f"with a like rate of {like_ratio:.2%} and a comment rate of {comment_ratio:.2%}. "
            f"Titles are typically {title_len:.1f} characters long."
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("### Top Performing Videos")
        st.dataframe(
            filtered.sort_values("views", ascending=False)[
                ["title", "channel_title", "views", "likes", "comments"]
            ].head(10),
            use_container_width=True,
            hide_index=True
        )

        # -------------------------------
        # GRAPHS
        # -------------------------------
        st.markdown("## Trend Insights")

        g1, g2 = st.columns(2)

        # -------- FASTEST TO TREND --------
        with g1:
            st.markdown("### Fastest to Trend")

            trend_speed_df = filtered.dropna(subset=["trend_speed_hours"]).sort_values(
                "trend_speed_hours"
            ).head(10)

            if not trend_speed_df.empty:
                chart_data = trend_speed_df[["title", "trend_speed_hours"]].set_index("title")
                st.bar_chart(chart_data)
            else:
                st.info("Not enough data to calculate trend speed.")

        # -------- PUBLISH TIME --------
        with g2:
            st.markdown("### Best Publish Times")

            publish_hour_df = filtered["publish_hour"].dropna().value_counts().sort_index()

            if not publish_hour_df.empty:
                st.line_chart(publish_hour_df)
            else:
                st.info("Not enough data for publish timing.")

        st.markdown("### Engagement Patterns")

        scatter_df = filtered[["views", "likes", "comments"]].dropna().copy()

        if not scatter_df.empty:
            scatter_df = scatter_df.head(100)  # reduce clutter
            st.scatter_chart(
                scatter_df,
             x="views",
             y="likes",
             size="comments"
            )
        else:
            st.info("Not enough engagement data.")

        # -------------------------------
        # KEYWORDS
        # -------------------------------
        st.markdown("### Top Keywords")

        import re
        from collections import Counter

        def extract_keywords(titles):
            words = []
            for t in titles:
                words += re.findall(r"\b[a-zA-Z]{4,}\b", str(t).lower())

            stopwords = {
                "this", "that", "with", "from", "have", "will",
                "your", "about", "video", "official"
            }

            words = [w for w in words if w not in stopwords]
            return Counter(words).most_common(10)

        keywords = extract_keywords(filtered["title"])

        if keywords:
            kw_df = pd.DataFrame(keywords, columns=["Keyword", "Count"])
            st.bar_chart(kw_df.set_index("Keyword"))
        else:
            st.info("Not enough keyword data.")

    else:
        st.warning("No data for this selection.")