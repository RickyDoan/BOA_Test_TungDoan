import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 0. CẤU HÌNH TRANG & GIAO DIỆN (DARK MODE OPTIMIZED UI)
# ==========================================
st.set_page_config(page_title="Client-Coach Executive Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Palette Màu Đồng Nhất (Consistent palette)
VIVID_HIGHLIGHT = "#38BDF8" # Xanh Neon (Vivid Sky Blue) - Đỉnh 13 khách, Engagement tốt
SILVER_DIM = "#94A3B8"      # Bạc Slate (Dim) - Màu nền cho các giá trị thấp/trung bình
AVG_HIGHLIGHT = "#BAE6FD"   # Xanh Nhẹ (Lighter Blue) - Cho thanh Bar ở vị trí 4 khách
CRITICAL_ALERT = "#EF4444"  # Đỏ Critical - Dành riêng cho cảnh báo đỉnh Churn

st.markdown(f"""
<style>
    /* Chỉnh các thẻ Metric (KPI) */
    div[data-testid="metric-container"] {{
        background-color: var(--secondary-background-color); 
        border: 1px solid var(--faded-text-10); 
        padding: 5% 5% 5% 10%;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        border-left: 5px solid {VIVID_HIGHLIGHT}; /* Viền xanh Neon rực rỡ */
    }}
    
    /* Phóng to Tiêu đề */
    h1 {{ font-size: 2.5rem !important; font-weight: 800 !important; }}
    h2 {{ font-size: 1.7rem !important; font-weight: 700 !important; margin-bottom: 15px !important; }}
    h1, h2, h3 {{ font-family: 'Helvetica Neue', sans-serif; }}
</style>
""", unsafe_allow_html=True)

st.title("🎯 Client-Coach Operations Executive Dashboard")
st.markdown("---")

# ==========================================
# 1. LOAD DATA 
# ==========================================
@st.cache_data
def load_data():
    # Giữ nguyên tên file .xlsx của bạn
    df_clients = pd.read_excel('client_cleaned.xlsx')
    df_coaches = pd.read_excel('coach_cleaned.xlsx')
    df_clients['last_payment_at'] = pd.to_datetime(df_clients['last_payment_at'])
    df_clients['payment_month_year'] = df_clients['last_payment_at'].dt.to_period('M').astype(str)
    return df_clients, df_coaches

df_clients, df_coaches = load_data()

# ==========================================
# 2. OVERVIEW KPI CARDS
# ==========================================
st.markdown("## 📊 1. System Overview")
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

left_col, right_col = st.columns(2)

# ==========================================
# 3. WORKLOAD DISTRIBUTION (HIGHLIGHT ĐÍCH DANH CỘT 13 VÀ CỘT 4)
# ==========================================
with left_col:
    st.markdown("## ⚖️ 2. Workload Allocation (Alert: Overloaded)")
    
    # Tính toán tần suất
    workload_counts = df_clients['coach_name'].value_counts()
    max_clients = workload_counts.max() # Lấy giá trị lớn nhất (13)
    avg_clients = workload_counts.mean() # ~4.9
    
    # Tạo dataframe tần suất đã được fix lỗi "ValueError cannot insert count"
    workload_freq = workload_counts.value_counts().rename_axis('client_count').reset_index(name='coach_frequency')
    workload_freq = workload_freq.sort_values('client_count')
    
    # LOGIC ĐỔ MÀU CỘT (Cái này sếp rất thích này):
    # Cột 13 khách -> Xanh Neon rực rỡ. 
    # Cột 4 khách (gần trung bình nhất) -> Xanh Sáng Nhẹ. 
    # Còn lại -> Dim Bạc Slate sạch sẽ.
    color_map_workload = []
    for val in workload_freq['client_count']:
        if val == max_clients:
            color_map_workload.append(VIVID_HIGHLIGHT)
        elif val == 4:
            color_map_workload.append(AVG_HIGHLIGHT)
        else:
            color_map_workload.append(SILVER_DIM)
    
    fig_workload = px.bar(workload_freq, x='client_count', y='coach_frequency',
                        #   title=f"Highlighted: {max_clients} Clients (Neon) vs ~Average 4 Clients (Light Blue)",
                          labels={'client_count': 'Assigned Client Count', 'coach_frequency': 'Frequency (Coaches)'})
    
    # Ép mảng màu vào cột, bo tròn nhẹ góc cột, ẩn viền
    fig_workload.update_traces(marker_color=color_map_workload, marker_line_width=0) 
    
    # Vẫn giữ 1 đường trung bình mảnh nhẹ để người xem biết chính xác số là 4.9
    fig_workload.add_vline(x=avg_clients, line_dash="dash", line_color=AVG_HIGHLIGHT, line_width=1.5, 
                           annotation_text=f"Avg ({avg_clients:.1f})", annotation_font_color=AVG_HIGHLIGHT, annotation_font_size=12)
    
    st.plotly_chart(fig_workload, use_container_width=True, theme="streamlit")

# ==========================================
# 4. ENGAGEMENT PERFORMANCE (ĐÃ THÊM ĐƯỜNG TRUNG BÌNH)
# ==========================================
with right_col:
    st.markdown("## 💰 3. Financial Engagement (Performance Highlights)")
    
    # Tính toán tỷ lệ thanh toán cho từng Coach
    engagement = pd.crosstab(df_clients['coach_name'], df_clients['payment_status'], normalize='index') * 100
    engagement = engagement.reset_index().sort_values('Full Payment', ascending=False)
    
    # TÍNH TỶ LỆ TRUNG BÌNH CỦA TOÀN HỆ THỐNG
    avg_payment_rate = engagement['Full Payment'].mean()
    
    # Lấy Top 5 và Bottom 5 để hiển thị
    top_bottom = pd.concat([engagement.head(5), engagement.tail(5)])
    
    # Logic đổ màu: >= 90% -> Xanh Neon | Còn lại -> Bạc Slate
    color_map_engage = [VIVID_HIGHLIGHT if val >= 90 else SILVER_DIM for val in top_bottom['Full Payment']]
    
    fig_engage = px.bar(top_bottom, y='coach_name', x='Full Payment', orientation='h',
                        title="Top Performers (Neon) vs Bottom (Silver) vs Average (Light Blue)",
                        labels={'Full Payment': 'Full Payment Rate (%)'})
    
    # Ép màu, bo góc, ẩn viền
    fig_engage.update_traces(marker_color=color_map_engage, marker_line_width=0)
    fig_engage.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    
    # THÊM ĐƯỜNG TRUNG BÌNH (VLINE) MÀU XANH NHẸ
    fig_engage.add_vline(x=avg_payment_rate, line_dash="dash", line_color=AVG_HIGHLIGHT, line_width=2, 
                         annotation_text=f"Avg ({avg_payment_rate:.1f}%)", 
                         annotation_font_color=AVG_HIGHLIGHT, 
                         annotation_font_size=12,
                         annotation_position="bottom right") # Để chữ nằm gọn dưới cùng bên phải đường line

    st.plotly_chart(fig_engage, use_container_width=True, theme="streamlit")

# ==========================================
# 5. CHURN TREND
# ==========================================
with left_col2:
    st.markdown("## 📉 4. Churn Timeline (Alert: Peak Drop-off)")
    trend_data = df_clients.groupby('payment_month_year').size().reset_index(name='client_drop_off')
    trend_data = trend_data.sort_values('payment_month_year')
    
    # Lấy đỉnh Churn
    max_churn = trend_data['client_drop_off'].max()
    max_churn_period = trend_data[trend_data['client_drop_off'] == max_churn]['payment_month_year'].values[0]
    
    fig_trend = go.Figure()
    
    # Thêm đường Line Bạc Silver làm nền (Mute)
    fig_trend.add_trace(go.Scatter(x=trend_data['payment_month_year'], y=trend_data['client_drop_off'],
                                   mode='lines+markers', line=dict(color=SILVER_DIM, width=2),
                                   marker=dict(color=SILVER_DIM, size=6),
                                   name="Drop-off Trend"))
    
    # HIGHLIGHT Peak: Chỉ điểm đỉnh dùng Marker màu Đỏ Critical
    fig_trend.add_trace(go.Scatter(x=[max_churn_period], y=[max_churn],
                                    mode='markers+text', 
                                    marker=dict(color=CRITICAL_ALERT, size=14, symbol="diamond", line=dict(color='white', width=2)),
                                    name="CRITICAL Peak",
                                    text=[f"PEAK: {max_churn}"], textposition="top center", textfont=dict(color=CRITICAL_ALERT, size=13, weight="bold")))
    
    fig_trend.update_layout(title=f"Highlighted: Peak Churn Period ({max_churn_period})",
                            xaxis_title="Timeline (Month/Year)", yaxis_title="Clients Lost",
                            margin=dict(l=20, r=20, t=50, b=20), plot_bgcolor='rgba(0,0,0,0)')
    
    # Đổ bóng nhẹ màu Bạc dưới đường line
    fig_trend.update_traces(selector=dict(name="Drop-off Trend"), fill='tozeroy', fillcolor='rgba(203, 213, 225, 0.1)') 
    st.plotly_chart(fig_trend, use_container_width=True, theme="streamlit")

# ==========================================
# 6. GENDER MATCHING (HEATMAP)
# ==========================================
with right_col2:
    st.markdown("## 💡 5. Matching Patterns ('Gender First' Advantage)")
    # Merge giới tính của Coach vào bảng Client
    merged_df = df_clients.merge(df_coaches[['coach_name', 'coach_gender']], on='coach_name', how='left')
    merged_df['client_gender'] = merged_df['client_gender'].str.title()
    merged_df['coach_gender'] = merged_df['coach_gender'].str.title()
    
    # Tạo bảng chéo tính tỷ lệ % giới tính
    gender_match = pd.crosstab(merged_df['client_gender'], merged_df['coach_gender'], normalize='index') * 100
    
    # Dải màu Custom Gradient: Thấp -> Dim (Xám Slate đậm để lùi vào nền); Cao -> Vivid Xanh Neon
    custom_blues_scale_ghosted = [
        [0, "#1E293B"],    # Slate cực đậm cho mờ tịt (Ghosted)
        [0.4, SILVER_DIM], # Slate sáng mờ vừa
        [1, VIVID_HIGHLIGHT]  # Xanh Neon cho Đỉnh
    ]
    
    fig_match = px.imshow(gender_match, text_auto='.1f', color_continuous_scale=custom_blues_scale_ghosted, 
                        #   title="Preference Matching: Highlights Same-Gender (Low Values Ghosted)",
                          labels=dict(x="Assigned Coach Gender", y="Client Gender", color="%"))
    fig_match.update_coloraxes(showscale=False) # Tắt thanh màu thừa
    st.plotly_chart(fig_match, use_container_width=True, theme="streamlit")

# ==========================================
# 7. POTENTIAL OPPORTUNITIES (GIẢI QUYẾT TASK 3)
# ==========================================
st.markdown("---")
st.markdown("## 🚀 Potential Opportunities & Alerts (Operational Focus)")

i_col1, i_col2, i_col3 = st.columns(3)
workload_counts = df_clients['coach_name'].value_counts()
max_clients = workload_counts.max()

with i_col1:
    st.error(f"**🔴 RED ALERT: Financial Underperformance**\n\nOperational Issues Detected: The bottom 3 coaches have a **0% Full Payment Rate**, and one coach handles **{max_clients} clients**. This indicates serious contract collection leakage and requires an immediate audit.")

with i_col2:
    # Tính toán cơ hội từ việc rebalancing
    low_workload_coaches = (workload_counts <= 2).sum()
    low_workload_pct = (low_workload_coaches / len(df_coaches)) * 100
    st.warning(f"**🟠 Opportunity: Workload Rebalancing**\n\nOperational Data: Workload is highly skewed (25% handle 1-2 clients). **{low_workload_coaches} Coaches ({low_workload_pct:.1f}%)** are severely underutilized. Redistributing clients will reduce burnout of peak performers.")

with i_col3:
    st.success("**🟢 Strategy: 'Gender-First' Marketing**\n\nAdditional Insight: Data shows an ~80% same-gender matching preference. Formalizing this as a business rule in CRM will comfort clients and increase initial engagement.")