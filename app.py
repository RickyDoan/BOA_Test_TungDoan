import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 0. CẤU HÌNH TRANG & GIAO DIỆN (ADAPTIVE UI)
# ==========================================
st.set_page_config(page_title="Client-Coach Analytics", layout="wide", initial_sidebar_state="collapsed")

# Nhúng CSS dùng biến tự động (Thích ứng Sáng/Tối)
st.markdown("""
<style>
    /* Chỉnh các thẻ Metric (KPI) */
    div[data-testid="metric-container"] {
        background-color: var(--secondary-background-color); /* Tự đổi màu theo theme */
        border: 1px solid var(--faded-text-10); /* Viền mờ tự động */
        padding: 5% 5% 5% 10%;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #1f77b4;
    }
    
    /* Chỉnh Font chữ chung nhưng KHÔNG ép màu */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Client-Coach Operations Executive Dashboard")
st.markdown("---")

# ==========================================
# 1. LOAD DATA 
# ==========================================
@st.cache_data
def load_data():
    df_clients = pd.read_excel('client_cleaned.xlsx')
    df_coaches = pd.read_excel('coach_cleaned.xlsx')
    df_clients['last_payment_at'] = pd.to_datetime(df_clients['last_payment_at'])
    df_clients['payment_month_year'] = df_clients['last_payment_at'].dt.to_period('M').astype(str)
    return df_clients, df_coaches

df_clients, df_coaches = load_data()

# ==========================================
# 2. OVERVIEW KPI CARDS
# ==========================================
st.markdown("### 📊 1. System Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Inactive Clients", f"{len(df_clients):,}")
with col2:
    st.metric("Total Active Coaches", f"{len(df_coaches):,}")
with col3:
    st.metric("Average Workload", f"{len(df_clients)/len(df_coaches):.1f} Clients/Coach")
with col4:
    female_pct = (df_clients['client_gender'].str.lower() == 'female').mean() * 100
    st.metric("Female Client Dominance", f"{female_pct:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# Tách 2 cột chính cho các biểu đồ
left_col, right_col = st.columns(2)

# ==========================================
# 3. WORKLOAD DISTRIBUTION
# ==========================================
with left_col:
    st.markdown("### ⚖️ 2. Workload Distribution")
    workload = df_clients['coach_name'].value_counts().reset_index()
    workload.columns = ['coach_name', 'current_clients']
    
    fig_workload = px.histogram(workload, x='current_clients', nbins=15, 
                                title="Client Allocation Skewness",
                                labels={'current_clients': 'Number of Assigned Clients', 'count': 'Frequency (Coaches)'},
                                color_discrete_sequence=['#3b82f6'])
    fig_workload.update_traces(marker_line_width=1, marker_line_color="rgba(255,255,255,0.2)") 
    fig_workload.add_vline(x=workload['current_clients'].mean(), line_dash="dash", line_color="#ef4444", annotation_text="Avg")
    
    # Bỏ hàm clean_plotly_layout đi, dùng theme mặc định của Streamlit
    st.plotly_chart(fig_workload, use_container_width=True, theme="streamlit")

# ==========================================
# 4. ENGAGEMENT PERFORMANCE
# ==========================================
with right_col:
    st.markdown("### 💰 3. Financial Engagement (Top vs Bottom)")
    engagement = pd.crosstab(df_clients['coach_name'], df_clients['payment_status'], normalize='index') * 100
    engagement = engagement.reset_index().sort_values('Full Payment', ascending=False)
    top_bottom = pd.concat([engagement.head(5), engagement.tail(5)])
    
    fig_engage = px.bar(top_bottom, y='coach_name', x='Full Payment', orientation='h',
                        title="100% vs 0% Full Payment Rate",
                        color='Full Payment', color_continuous_scale='tealrose',
                        labels={'Full Payment': 'Full Payment Rate (%)'})
    fig_engage.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_engage, use_container_width=True, theme="streamlit")

st.markdown("<br>", unsafe_allow_html=True)
left_col2, right_col2 = st.columns(2)

# ==========================================
# 5. CHURN TREND
# ==========================================
with left_col2:
    st.markdown("### 🚨 4. Operational Issue: The Churn Timeline")
    trend_data = df_clients.groupby('payment_month_year').size().reset_index(name='client_drop_off')
    trend_data = trend_data.sort_values('payment_month_year')
    
    fig_trend = px.line(trend_data, x='payment_month_year', y='client_drop_off', markers=True,
                        title="When did we lose these 500 clients?",
                        labels={'payment_month_year': 'Timeline (Month/Year)', 'client_drop_off': 'Clients Lost'})
    fig_trend.update_traces(line_color='#8b5cf6', line_width=4, marker=dict(size=8, color='#c4b5fd'))
    fig_trend.update_traces(fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.1)') 
    st.plotly_chart(fig_trend, use_container_width=True, theme="streamlit")

# ==========================================
# 6. GENDER MATCHING
# ==========================================
with right_col2:
    st.markdown("### 💡 5. Additional Insight: 'Gender Matching'")
    merged_df = df_clients.merge(df_coaches[['coach_name', 'coach_gender']], on='coach_name', how='left')
    merged_df['client_gender'] = merged_df['client_gender'].str.title()
    merged_df['coach_gender'] = merged_df['coach_gender'].str.title()
    
    gender_match = pd.crosstab(merged_df['client_gender'], merged_df['coach_gender'], normalize='index') * 100
    fig_match = px.imshow(gender_match, text_auto='.1f', color_continuous_scale='BuPu', 
                          title="Preference: Clients are matched with same-gender coaches",
                          labels=dict(x="Assigned Coach Gender", y="Client Gender", color="%"))
    st.plotly_chart(fig_match, use_container_width=True, theme="streamlit")

# ==========================================
# 7. BUSINESS INSIGHTS 
# ==========================================
st.markdown("---")
st.markdown("### 🚀 Strategic Recommendations")

i_col1, i_col2, i_col3 = st.columns(3)

with i_col1:
    st.error("**🔴 Risk: Revenue Leakage**\n\nThe bottom 3 coaches have a **0% full payment rate**. This is an immediate red flag requiring a contract management audit to recover underpaid accounts.")
with i_col2:
    st.warning("**🟠 Opportunity: Rebalancing**\n\nWorkload is highly skewed. 25% of coaches handle only 1-2 clients. Redistributing clients from overloaded coaches (10+) will prevent burnout and improve retention.")
with i_col3:
    st.success("**🟢 Strategy: Gender-First Matching**\n\nData shows an ~80% natural preference for same-gender matching. Automating this rule in the CRM will increase initial client comfort and long-term engagement.")