"""India Construction & Infra Intelligence Hub (₹) - Streamlit Application
Interactive executive platform tracking Indian infrastructure investment opportunities,
capex pipelines in ₹ Crores, listed equity beneficiaries, and industry application deadlines.
Features verified working URLs and search fallbacks to ensure 0 broken links / 404s.
"""

import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, date
import altair as alt

from database import (
    init_db, 
    get_investments, 
    get_upcoming_events, 
    get_intel_metrics
)
from collector import collect_and_store

# Set page configuration
st.set_page_config(
    page_title="India Construction & Infra Pulse (₹)",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Indian Institutional & Executive Dashboard
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }
    
    /* Opportunity Card */
    .opp-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .opp-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.08);
        border-color: #94a3b8;
    }
    
    .opp-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    
    .opp-summary {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.55;
        margin-bottom: 12px;
    }
    
    /* Investment Thesis Box */
    .thesis-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border-left: 4px solid #10b981;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.92rem;
        color: #065f46;
        line-height: 1.45;
    }
    
    /* Event / Deadline Card */
    .event-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .event-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
    }
    
    /* Custom Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 6px;
        letter-spacing: 0.4px;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    
    .badge-urgent {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #f87171;
    }
    .badge-closing {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fbbf24;
    }
    .badge-open {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    
    .badge-impact-5 {
        background-color: #fee2e2;
        color: #991b1b;
        border: 1px solid #f87171;
    }
    .badge-impact-4 {
        background-color: #ffedd5;
        color: #9a3412;
        border: 1px solid #fb923c;
    }
    .badge-impact-3 {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #60a5fa;
    }
    .badge-impact-2 {
        background-color: #ccfbf1;
        color: #115e59;
        border: 1px solid #2dd4bf;
    }
    .badge-impact-1 {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }
    
    .tag-sector {
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #cbd5e1;
    }
    .tag-capex {
        background-color: #ecfdf5;
        color: #047857;
        border: 1px solid #6ee7b7;
        font-weight: 700;
    }
    .tag-beneficiary {
        background-color: #f3e8ff;
        color: #6b21a8;
        border: 1px solid #d8b4fe;
        font-weight: 600;
    }
    .tag-organizer {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #7dd3fc;
    }
    
    .meta-bar {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .link-btn-primary {
        background-color: #2563eb;
        color: #ffffff !important;
        padding: 5px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-block;
    }
    .link-btn-secondary {
        background-color: #f1f5f9;
        color: #334155 !important;
        border: 1px solid #cbd5e1;
        padding: 4px 10px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.80rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Database and Auto-Seed
init_db()
today_str = datetime.utcnow().strftime("%Y-%m-%d")
today_date = date.today()

initial_metrics = get_intel_metrics(current_date=today_str)
if initial_metrics["total_opportunities"] == 0:
    collect_and_store()
    initial_metrics = get_intel_metrics(current_date=today_str)


# Helper Functions
def get_deadline_badge(last_date_str: str) -> str:
    """Calculates days remaining and returns appropriate urgency badge."""
    try:
        deadline = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        days_remaining = (deadline - today_date).days
        
        if days_remaining < 0:
            return '<span class="badge" style="background-color: #f1f5f9; color: #64748b;">CLOSED</span>'
        elif days_remaining <= 3:
            return f'<span class="badge badge-urgent">🔴 URGENT ({days_remaining}d left)</span>'
        elif days_remaining <= 10:
            return f'<span class="badge badge-closing">🟡 CLOSING SOON ({days_remaining}d left)</span>'
        else:
            return f'<span class="badge badge-open">🟢 OPEN ({days_remaining}d left)</span>'
    except Exception:
        return f'<span class="badge badge-open">🗓️ Due: {last_date_str}</span>'


def get_impact_badge(score: int) -> str:
    """Returns HTML for color-coded impact badge."""
    labels = {
        5: ("🔴 5 - MEGA TENDER / REFORM", "badge-impact-5"),
        4: ("🟠 4 - HIGH CONVICTION", "badge-impact-4"),
        3: ("🔵 3 - MODERATE OPPORTUNITY", "badge-impact-3"),
        2: ("🟢 2 - OPERATIONAL", "badge-impact-2"),
        1: ("⚪ 1 - INFORMATIONAL", "badge-impact-1")
    }
    text, css_class = labels.get(score, ("🔵 3 - MODERATE", "badge-impact-3"))
    return f'<span class="badge {css_class}">{text}</span>'


def get_search_fallback_url(title: str) -> str:
    """Generates a guaranteed Google News search URL for the story."""
    encoded = urllib.parse.quote(f"{title} India construction infrastructure")
    return f"https://news.google.com/search?q={encoded}"


# =========================================================================
# Sidebar Filters & Navigation
# =========================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/rupee.png", width=64)
st.sidebar.title("India Infra Pulse (₹)")
st.sidebar.caption("Institutional Investment & Industry Deadlines Intelligence")

# Action: Ingest Feeds
if st.sidebar.button("🔄 Refresh Feeds & Pipelines", use_container_width=True):
    with st.spinner("Scraping Indian feeds, verifying links & updating deadlines..."):
        tot_o, new_o, tot_e, new_e = collect_and_store()
        st.sidebar.success(f"Harvested {tot_o} opportunities & {tot_e} events")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Opportunity Filters")

search_query = st.sidebar.text_input("Search Tenders / Projects / Themes", placeholder="e.g. Metro, Expressways, Kavach...")

# Sub-Sector Multi-select
sub_sector_options = [
    "Roads & Highways",
    "Railways & Metro",
    "Cement & Steel",
    "Real Estate & REITs",
    "Renewable Infra",
    "Ports & Logistics",
    "Water & Urban Infra",
    "Power & Transmission"
]
selected_sectors = st.sidebar.multiselect(
    "Sub-Sector",
    options=sub_sector_options,
    default=None,
    help="Select one or more sectors to filter opportunities"
)

# Minimum Capex Slider (₹ Cr)
min_capex = st.sidebar.slider(
    "Minimum Capex (₹ Crores)",
    min_value=0,
    max_value=15000,
    value=0,
    step=500,
    help="Filter tenders and projects by minimum estimated capital expenditure"
)

# Beneficiary Company Search / Filter
beneficiary_filter = st.sidebar.text_input(
    "Beneficiary Ticker / Listed EPC", 
    placeholder="e.g. L&T, UltraTech, PNC Infratech, DLF"
)

# Impact Score Slider
min_impact = st.sidebar.slider(
    "Minimum Impact Score (1-5)",
    min_value=1,
    max_value=5,
    value=1,
    help="5: Mega-tenders/Policy, 4: High conviction awards, 3: Standard tenders"
)

# Sort Ordering
sort_by_label = st.sidebar.selectbox(
    "Sort Opportunities By",
    ["Highest Impact First", "Largest Capex (₹ Cr) First", "Newest Published First", "Oldest First"]
)
sort_map = {
    "Highest Impact First": "impact_desc",
    "Largest Capex (₹ Cr) First": "capex_desc",
    "Newest Published First": "date_desc",
    "Oldest First": "date_asc"
}
sort_by = sort_map[sort_by_label]

st.sidebar.markdown("---")
st.sidebar.caption("India Construction & Infra Hub • Standardized in ₹ Crores")


# =========================================================================
# Main Dashboard Header & KPI Metrics
# =========================================================================
st.title("🏗️ India Construction & Infra Intelligence Hub (₹)")
st.markdown("Real-time pipeline tracking **₹ Crore project capex**, listed equity beneficiaries, and **upcoming industry deadlines**.")

metrics = get_intel_metrics(current_date=today_str)

col1, col2, col3, col4 = st.columns(4)
with col1:
    formatted_capex = f"₹ {metrics['total_pipeline_capex_cr']:,.0f} Cr"
    st.metric("Tracked Capex Pipeline", formatted_capex, help="Total aggregated capital expenditure across all tracked Indian project opportunities")
with col2:
    st.metric("High-Conviction (Impact ≥ 4)", metrics["high_impact_count"], help="Major tenders (> ₹1,000 Cr), national corridors, and key policy approvals")
with col3:
    top_tickers_list = ", ".join(list(metrics["top_beneficiaries"].keys())[:3]) if metrics["top_beneficiaries"] else "None"
    st.metric("Top Beneficiary EPCs", top_tickers_list, help="Most frequently mentioned listed companies in new contract awards")
with col4:
    st.metric("Active Application Deadlines", metrics["active_deadlines_count"], help="Upcoming grant applications, calls for papers, and awards closing soon")

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================================
# TOP SECTION: ⏰ Upcoming Industry Deadlines & Applications
# =========================================================================
with st.expander("⏰ **UPCOMING INDUSTRY DEADLINES & APPLICATIONS** (Click to expand / collapse)", expanded=True):
    upcoming_events = get_upcoming_events(only_active=True, current_date=today_str)
    
    if not upcoming_events:
        st.info("No active application deadlines at this time.")
    else:
        st.caption(f"Showing {len(upcoming_events)} active industry calls, sorted chronologically by application deadline.")
        
        e_col1, e_col2 = st.columns(2)
        for i, evt in enumerate(upcoming_events[:6]):
            col = e_col1 if i % 2 == 0 else e_col2
            with col:
                deadline_badge = get_deadline_badge(evt["last_application_date"])
                org_badge = f'<span class="badge tag-organizer">🏛️ {evt["organizer"]}</span>'
                cat_badge = f'<span class="badge tag-sector">📌 {evt["category"]}</span>'
                search_url = get_search_fallback_url(f"{evt['event_name']} {evt['organizer']}")
                
                evt_html = f"""
                <div class="event-card">
                    <div style="margin-bottom: 6px;">
                        {deadline_badge}
                        {cat_badge}
                        {org_badge}
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                        {evt["event_name"]}
                    </div>
                    <div style="font-size: 0.88rem; color: #475569; margin-bottom: 8px;">
                        🗓️ <b>Event Schedule:</b> {evt["event_dates"]} &nbsp;|&nbsp; ⏰ <b>Deadline:</b> {evt["last_application_date"]}
                    </div>
                    <div style="font-size: 0.90rem; color: #334155; line-height: 1.45; margin-bottom: 10px;">
                        {evt["details"]}
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 8px;">
                        <a href="{search_url}" target="_blank" class="link-btn-secondary">
                            🔍 News / Updates ↗
                        </a>
                        <a href="{evt["url"]}" target="_blank" class="link-btn-primary">
                            Apply / View Portal ↗
                        </a>
                    </div>
                </div>
                """
                st.markdown(evt_html, unsafe_allow_html=True)
                
        if len(upcoming_events) > 6:
            st.info(f"💡 More deadlines available in the **Industry Events & Summits Calendar** tab below.")

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================================
# MAIN DASHBOARD TABS
# =========================================================================
tab_opps, tab_events, tab_analytics, tab_export = st.tabs([
    "💼 Investment Opportunities",
    "📅 All Industry Deadlines & Events",
    "📊 Capex & Equity Analytics",
    "🗄️ Raw Data & CSV Export"
])

# Fetch Filtered Opportunities
opportunities = get_investments(
    sub_sectors=selected_sectors if selected_sectors else None,
    min_capex=float(min_capex),
    min_impact=min_impact,
    max_impact=5,
    beneficiary=beneficiary_filter,
    search_query=search_query,
    sort_by=sort_by
)


# ================= TAB 1: INVESTMENT OPPORTUNITIES =================
with tab_opps:
    col_hdr, col_fil = st.columns([3, 1])
    with col_hdr:
        st.subheader(f"Tracked Opportunities ({len(opportunities)} items match filters)")
    with col_fil:
        if selected_sectors or min_capex > 0 or beneficiary_filter or min_impact > 1 or search_query:
            st.info("Active Filters Applied")
            
    if not opportunities:
        st.warning("No investment opportunities match your criteria. Try adjusting the Capex slider, sub-sector, or beneficiary filter.")
    else:
        for opp in opportunities:
            impact_badge = get_impact_badge(opp["impact_score"])
            sector_badge = f'<span class="badge tag-sector">🏗️ {opp["sub_sector"]}</span>'
            
            # Capex Badge
            if opp["estimated_capex_cr"] and opp["estimated_capex_cr"] > 0:
                capex_badge = f'<span class="badge tag-capex">💰 ₹ {opp["estimated_capex_cr"]:,.0f} Cr</span>'
            else:
                capex_badge = '<span class="badge tag-capex">💰 Capex: Pending Details</span>'
                
            # Beneficiary Tickers
            if opp["beneficiary_tickers"]:
                tickers = [f'<span class="badge tag-beneficiary">📈 {t.strip()}</span>' for t in opp["beneficiary_tickers"].split(",") if t.strip()]
                tickers_html = "".join(tickers)
            else:
                tickers_html = '<span class="badge tag-beneficiary">📈 EPC Stakeholders</span>'
                
            date_tag = f'<span>🗓️ Published: {opp["published_date"]}</span>'
            search_fallback = get_search_fallback_url(opp["title"])
            
            opp_html = f"""
            <div class="opp-card">
                <div style="margin-bottom: 8px;">
                    {impact_badge}
                    {sector_badge}
                    {capex_badge}
                    {tickers_html}
                </div>
                <div class="opp-title">{opp["title"]}</div>
                <div class="opp-summary">{opp["summary"]}</div>
                <div class="thesis-box">
                    <b>💡 Investment Angle & Catalyst:</b><br>
                    {opp["investment_thesis"]}
                </div>
                <div class="meta-bar">
                    <div>{date_tag}</div>
                    <div style="display: flex; gap: 8px;">
                        <a href="{search_fallback}" target="_blank" class="link-btn-secondary">
                            🔍 Search Live Coverage ↗
                        </a>
                        <a href="{opp["url"]}" target="_blank" class="link-btn-primary">
                            Open Source Link ↗
                        </a>
                    </div>
                </div>
            </div>
            """
            st.markdown(opp_html, unsafe_allow_html=True)


# ================= TAB 2: ALL INDUSTRY DEADLINES & EVENTS =================
with tab_events:
    st.subheader("📅 Complete Industry Deadlines & Summit Calendar")
    st.caption("Track upcoming calls for papers, hackathons, ConTech summits, and award nominations from CTAI, ASAPP, CREDAI, NAREDCO, and MoHUA.")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cat_filter = st.selectbox(
            "Filter Event Category", 
            ["All", "Hackathon/Pitch", "Call for Papers", "Award Nominations", "Expo/Conference"]
        )
    with col_c2:
        org_filter = st.selectbox(
            "Filter Organizer",
            ["All", "CTAI (Construction Technology Association of India)", "ASAPP Info Global / Construction World", "CREDAI", "NAREDCO", "MoHUA (Ministry of Housing and Urban Affairs)", "NICMAR University", "CII (Confederation of Indian Industry)", "NHAI (National Highways Authority of India)"]
        )
        
    all_events = get_upcoming_events(
        category=cat_filter,
        organizer=org_filter,
        only_active=False,
        current_date=today_str
    )
    
    if not all_events:
        st.info("No events match the selected criteria.")
    else:
        for evt in all_events:
            deadline_badge = get_deadline_badge(evt["last_application_date"])
            org_badge = f'<span class="badge tag-organizer">🏛️ {evt["organizer"]}</span>'
            cat_badge = f'<span class="badge tag-sector">📌 {evt["category"]}</span>'
            search_url = get_search_fallback_url(f"{evt['event_name']} {evt['organizer']}")
            
            card_html = f"""
            <div class="event-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <div style="margin-bottom: 6px;">
                            {deadline_badge}
                            {cat_badge}
                            {org_badge}
                        </div>
                        <div style="font-size: 1.12rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                            {evt["event_name"]}
                        </div>
                        <div style="font-size: 0.88rem; color: #475569; margin-bottom: 6px;">
                            🗓️ <b>Event Schedule:</b> {evt["event_dates"]} &nbsp;|&nbsp; ⏰ <b>Last Date to Apply:</b> {evt["last_application_date"]}
                        </div>
                        <div style="font-size: 0.92rem; color: #334155; margin-top: 6px;">
                            {evt["details"]}
                        </div>
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 8px;">
                        <a href="{search_url}" target="_blank" class="link-btn-secondary">
                            🔍 News / Updates ↗
                        </a>
                        <a href="{evt["url"]}" target="_blank" class="link-btn-primary">
                            Apply / Register ↗
                        </a>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)


# ================= TAB 3: CAPEX & EQUITY ANALYTICS =================
with tab_analytics:
    st.subheader("📊 Capital Expenditure & Beneficiary Equity Analytics")
    
    all_opps_raw = get_investments(min_impact=1, max_impact=5, limit=500)
    if all_opps_raw:
        df = pd.DataFrame(all_opps_raw)
        
        c_ch1, c_ch2 = st.columns(2)
        
        with c_ch1:
            st.markdown("##### 💰 Tracked Capex Pipeline by Sub-Sector (₹ Crores)")
            sector_capex = df.groupby("sub_sector")["estimated_capex_cr"].sum().reset_index()
            sector_capex.columns = ["Sub-Sector", "Capex (₹ Cr)"]
            sector_capex = sector_capex.sort_values(by="Capex (₹ Cr)", ascending=False)
            
            chart_sector = alt.Chart(sector_capex).mark_bar(cornerRadius=6).encode(
                x=alt.X("Capex (₹ Cr):Q", title="Total Capex (₹ Crores)"),
                y=alt.Y("Sub-Sector:N", sort="-x", title="Sub-Sector"),
                color=alt.Color("Capex (₹ Cr):Q", scale=alt.Scale(scheme="greens")),
                tooltip=["Sub-Sector", alt.Tooltip("Capex (₹ Cr):Q", format=",.0f")]
            ).properties(height=300)
            st.altair_chart(chart_sector, use_container_width=True)
            
        with c_ch2:
            st.markdown("##### 🏢 Top Mentioned Beneficiary Companies & Listed EPCs")
            company_freq = {}
            for tickers_str in df["beneficiary_tickers"].dropna():
                for t in tickers_str.split(","):
                    name = t.strip()
                    if name:
                        company_freq[name] = company_freq.get(name, 0) + 1
                        
            comp_df = pd.DataFrame(list(company_freq.items()), columns=["Company", "Opportunity Count"])
            comp_df = comp_df.sort_values(by="Opportunity Count", ascending=False).head(10)
            
            chart_comp = alt.Chart(comp_df).mark_bar(cornerRadius=6).encode(
                x=alt.X("Opportunity Count:Q", title="Project Opportunities"),
                y=alt.Y("Company:N", sort="-x", title="Listed Company / EPC"),
                color=alt.Color("Opportunity Count:Q", scale=alt.Scale(scheme="purples")),
                tooltip=["Company", "Opportunity Count"]
            ).properties(height=300)
            st.altair_chart(chart_comp, use_container_width=True)
            
        st.markdown("---")
        c_ch3, c_ch4 = st.columns(2)
        
        with c_ch3:
            st.markdown("##### 🎯 Opportunity Distribution by Impact Tier")
            impact_df = df["impact_score"].value_counts().reset_index()
            impact_df.columns = ["Impact Score", "Count"]
            impact_df["Impact Tier"] = impact_df["Impact Score"].map({
                5: "5 - Mega Tender / Reform",
                4: "4 - High Conviction",
                3: "3 - Moderate Opportunity",
                2: "2 - Operational",
                1: "1 - Informational"
            })
            
            chart_impact = alt.Chart(impact_df).mark_bar(cornerRadius=6).encode(
                x=alt.X("Count:Q", title="Number of Opportunities"),
                y=alt.Y("Impact Tier:N", sort="-x", title="Impact Level"),
                color=alt.Color("Impact Score:Q", scale=alt.Scale(scheme="oranges")),
                tooltip=["Impact Tier", "Count"]
            ).properties(height=280)
            st.altair_chart(chart_impact, use_container_width=True)
            
        with c_ch4:
            st.markdown("##### 📁 Volume of Projects by Sub-Sector")
            vol_df = df["sub_sector"].value_counts().reset_index()
            vol_df.columns = ["Sub-Sector", "Count"]
            
            chart_vol = alt.Chart(vol_df).mark_arc(innerRadius=45).encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Sub-Sector:N"),
                tooltip=["Sub-Sector", "Count"]
            ).properties(height=280)
            st.altair_chart(chart_vol, use_container_width=True)
    else:
        st.info("No opportunity data available for analytics.")


# ================= TAB 4: RAW DATA & CSV EXPORT =================
with tab_export:
    st.subheader("🗄️ Database Records & CSV Export")
    
    st.markdown("#### 1. Investment Opportunities Dataset")
    all_opps = get_investments(min_impact=1, max_impact=5, limit=500)
    if all_opps:
        opp_df = pd.DataFrame(all_opps)
        cols_opp = ["id", "impact_score", "sub_sector", "estimated_capex_cr", "beneficiary_tickers", "title", "published_date", "investment_thesis", "url", "summary"]
        existing_opp_cols = [c for c in cols_opp if c in opp_df.columns]
        display_opp_df = opp_df[existing_opp_cols]
        st.dataframe(display_opp_df, use_container_width=True, height=280)
        
        csv_opp = display_opp_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Investment Opportunities (CSV)",
            data=csv_opp,
            file_name=f"india_infra_opportunities_{today_str}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 2. Industry Events & Deadlines Dataset")
    all_evts = get_upcoming_events(only_active=False, current_date=today_str)
    if all_evts:
        evt_df = pd.DataFrame(all_evts)
        cols_evt = ["id", "event_name", "organizer", "category", "last_application_date", "event_dates", "url", "details"]
        existing_evt_cols = [c for c in cols_evt if c in evt_df.columns]
        display_evt_df = evt_df[existing_evt_cols]
        st.dataframe(display_evt_df, use_container_width=True, height=250)
        
        csv_evt = display_evt_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Industry Deadlines & Events (CSV)",
            data=csv_evt,
            file_name=f"india_infra_deadlines_{today_str}.csv",
            mime="text/csv",
            use_container_width=True
        )
