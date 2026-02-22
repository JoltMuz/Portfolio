import streamlit as st
from logic import get_psx_data, calculate_signal

# Force wide mode and set page title
st.set_page_config(page_title="PSX Sniper", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Animated Mesh Background */
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #0d0e16, #1a1c2c, #0f172a, #020617);
        background-size: 400% 400%;
        animation: gradientFlow 15s ease infinite;
        background-attachment: fixed;
    }

    /* Organic Grain Overlay */
    /*.stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        opacity: 0.04;
        pointer-events: none;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    }*/

    /* Minimalist Glass Card */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.4s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transform: translateY(-3px);
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 20, 0.6) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Typography Polish */
    .section-head {
        font-size: 14px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.4);
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 25px 0 10px 0;
    }

    .main-title {
        text-align: center;
        font-weight: 200;
        letter-spacing: -1px;
        color: #f8fafc;
        padding: 20px 0;
    }

    /* Hide redundant streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title"> 📈PSX Stock Valuation & Recommendation📊</h1>', unsafe_allow_html=True)
st.divider()

# Sidebar
ticker_input = st.sidebar.text_input("Enter Ticker (e.g. FABL)", "FABL").upper()
scan_btn = st.sidebar.button("🔬 Analyze")

if scan_btn:
    with st.spinner(f"Processing {ticker_input}..."):
        data = get_psx_data(ticker_input)
        
    if data:
        signal_text, signal_type = calculate_signal(data)
        
        # --- HEADER: Asset Info ---
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            st.markdown(f"### 💎 {ticker_input}")
        with col_t2:
            if signal_type == "Success":
                st.success(f"**{signal_text}** | Expected Upside: Rs. {round(data['target_value'] - data['current_price'], 2)}")
            elif signal_type == "Error":
                st.error(f"**{signal_text}** | Estimated Overprice: Rs. {round(data['current_price'] - data['target_value'], 2)}")
            else:
                st.warning(f"**{signal_text}**")

        # --- GRID LAYOUT ---
        st.markdown('<p class="section-head">Market Performance</p>', unsafe_allow_html=True)
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
        
        r1_c1.metric("Live Price", f"Rs. {data.get('current_price')}")
        r1_c2.metric("3D Moving Avg", f"Rs. {data.get('three_day_avg')}")
        r1_c3.metric("30D Moving Avg", f"Rs. {data.get('thirty_day_avg')}")
        r1_c4.metric("PE Val Target", f"Rs. {data.get('target_value_pe')}")
        
        upside_pct = round(((data['target_value']/data['current_price'])-1)*100, 1)
        r1_c5.metric("Final Target", f"Rs. {data.get('target_value')}", delta=f"{upside_pct}%")

        st.markdown('<p class="section-head">Fundamental Analysis</p>', unsafe_allow_html=True)
        r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
        
        r2_c1.metric("Company P/E", f"{data.get('pe_ratio')}")
        r2_c2.metric("Sector P/E", f"{data.get('industry_pe')}")
        r2_c3.metric("Book Value", f"Rs. {data.get('book_value')}")
        r2_c4.metric("Sector P/B", f"{data.get('industry_pb')}")
        
        current_pb = round(data['current_price'] / data['book_value'], 2) if data['book_value'] > 0 else 0
        r2_c5.metric("Current P/B", f"{current_pb}")

    else:
        st.error("Ticker data not found.")
else:
    st.info("👈 Enter a ticker and click Analyze to begin.")