import os
os.system("pip install folium streamlit-folium reportlab earthengine-api pandas geopy")

import streamlit as st
import folium
from streamlit_folium import st_folium
import io
import json

# Page Setup
st.set_page_config(
    page_title="TerraRisk-AI | Enterprise Dropdown Engine",
    page_icon="🛡️",
    layout="wide"
)

# ==============================================================================
# 🏛️ INDEPENDENT DATABASE REGISTER (NO HARD-CODED INDEXES)
# ==============================================================================
LATUR_MASTER_DB = {
    "Latur (लातूर)": {
        "Center": [18.4088, 76.5604],
        "Villages": ["Murud (मुरुड)", "Harangul Bk. (हरंगुळ बु.)", "Chincholi (चिंचोली)", "Arvi (आर्वी)", "Khandapur (खांदापूर)"]
    },
    "Ausa (औसा)": {
        "Center": [18.2531, 76.5019],
        "Villages": ["Killari (किल्लारी)", "Lamjana (लामजना)", "Matola (मातोळा)", "Belkund (बेलकुंड)", "Ashiv (आशिव)"]
    },
    "Nilanga (निलंगा)": {
        "Center": [18.1278, 76.7570],
        "Villages": ["Aurad Shahajani (औराद शहाजानी)", "Kasarsirsi (कासारशिरशी)", "Halgara (हळгरा)", "Shirur Tajband (शिरूर ताजबंद)"]
    },
    "Udgir (उदगीर)": {
        "Center": [18.3934, 77.1186],
        "Villages": ["Wadhwana (वाढवणा)", "Nideban (निदेबन)", "Her (हेर)", "Dongarshelki (डोंगरशेळकी)"]
    },
    "Ahmedpur (अहमदपूर)": {
        "Center": [18.7058, 76.9328],
        "Villages": ["Kingaon (किनगाव)", "Hadolti (हाडोळती)", "Valandi (वळंदी)", "Shirur Tajband (शिरूर ताजबंद)"]
    },
    "Chakur (चाकुर)": {
        "Center": [18.5238, 76.8631],
        "Villages": ["Vadwal Nagnath (वडवळ नागनाथ)", "Latur Road (लातूर रोड)", "Nalegaon (नळेगाव)", "Chapoli (चापोली)"]
    },
    "Renapur (रेणापूर)": {
        "Center": [18.5218, 76.5214],
        "Villages": ["Pohregaon (पोहरेगाव)", "Digol (डिगोळ)", "Pangaon (पांगण)", "Kharola (खरोला)", "Motegaon (मोतेगाव)", "Renapur Rural (रेणापूर ग्रामीण)"]
    },
    "Shirur Anantpal (शिरूर अनंतपाळ)": {
        "Center": [18.2917, 76.8406],
        "Villages": ["Talegaon (तळेगाव)", "Hisamabad (हिसमाबाद)", "Kamkheda (कामखेडा)", "Sakarwadi (साकरवाडी)"]
    },
    "Deoni (देवणी)": {
        "Center": [18.2581, 77.1118],
        "Villages": ["Deoni Bk. (देवणी बु.)", "Walindi (वलिंदी)", "Vilegaon (विलेगाव)", "Sawalegaon (सावळेगाव)"]
    },
    "Jalkot (जळकोट)": {
        "Center": [18.6315, 77.2144],
        "Villages": ["Atnoor (अतणूर)", "Rawankola (रावणकोळा)", "Khadgaon (खडगाव)", "Mangrul (मंगरुळ)"]
    }
}

# Session Management for Dashboard Lock
if 'engine_active' not in st.session_state:
    st.session_state.engine_active = False

st.title("🛡️ TerraRisk-AI: Land Verification Ledger (Latur Core)")
st.write("---")

# ==============================================================================
# 📋 EXPERT SCREEN ARCHITECTURE (FORM-FREE FOR INSTANT REFRESH)
# ==============================================================================
if not st.session_state.engine_active:
    st.subheader("📋 Step 1: Institutional Entry & Location Routing")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("##### 👤 Auditor Details")
        input_officer = st.text_input("Officer Name (बँक अधिकाऱ्याचे नाव):", value="Prathmesh Sonvane")
        input_bank = st.text_input("Institution Name (बँक किंवा शाखेचे नाव):", value="State Bank of India (SBI)")
        
        st.markdown("##### 📄 Land Record Registry (7/12)")
        input_farmer = st.text_input("Farmer Name (7/12 प्रमाणे नाव):", value="Ramrao Vitthal Patil")
        input_gut = st.text_input("Gut / Survey Number (गट क्रमांक):", value="104")
        input_area = st.text_input("Declared Land Area (Acres):", value="4.5")

    with col_right:
        st.markdown("##### 🗺️ Target Location Routing (Instant Reactive Core)")
        st.selectbox("Select State:", ["Maharashtra"])
        st.selectbox("Select District:", ["Latur (लातूर)"])
        
        # १. तालुका निवड (यावर क्लिक करताच खालचा बॉक्स लगेच बदलेल)
        taluka_options = sorted(list(LATUR_MASTER_DB.keys()))
        selected_taluka = st.selectbox("Select Taluka (तालुका निवडा):", taluka_options)
        
        # २. डेटाबेस थेट रिफ्रेश - EXPERT SYSTEM
        current_db_slice = LATUR_MASTER_DB[selected_taluka]
        village_options = sorted(current_db_slice["Villages"])
        
        # ३. गाव निवड (आता रेणापूर निवडल्यास फक्त रेणापूरचीच गावे दिसतील, कोणताही घोळ नाही!)
        selected_village = st.selectbox("Select Village (गाव निवडा):", village_options)
        
        st.markdown("##### 📊 Scope Setup")
        input_scope = st.radio("Evaluation Scope:", ["Single Asset (1 Farmer)", "Regional Portfolio"])

    st.write("---")
    # ट्रीगर बटण फॉर्मच्या बाहेर स्वतंत्र ठेवले आहे
    trigger_lock = st.button("🔓 Open Mapping Engine & Verify Asset")
    
    if trigger_lock:
        st.session_state.cached_data = {
            "officer": input_officer, "bank": input_bank, "farmer": input_farmer,
            "gut": input_gut, "area": input_area, "taluka": selected_taluka,
            "village": selected_village, "lat": current_db_slice["Center"][0],
            "lon": current_db_slice["Center"][1]
        }
        st.session_state.engine_active = True
        st.rerun()

# ==============================================================================
# 🗺️ PHASE 2: ACTIVE GEOSPATIAL MAP (UNLOCKED)
# ==============================================================================
else:
    data = st.session_state.cached_data
    
    st.sidebar.markdown(f"#### 🟢 Secured Session Active")
    st.sidebar.write(f"**Officer:** {data['officer']}")
    st.sidebar.write(f"**Bank:** {data['bank']}")
    st.sidebar.write(f"**Location:** {data['village']}, {data['taluka']}")
    
    if st.sidebar.button("🔄 Audit New Asset (नवीन फॉर्म भरा)"):
        st.session_state.engine_active = False
        st.rerun()
        
    st.success(f"🎯 Geospatial Engine Locked on Target: {data['village']} ({data['taluka']})")
    
    c_map, c_report = st.columns([1.6, 1.4])
    
    with c_map:
        st.markdown("### 🗺️ Farm Boundary Trace")
        m = folium.Map(location=[data['lat'], data['lon']], zoom_start=14)
        folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite', name='Google').add_to(m)
        st_folium(m, width=650, height=450)
        
    with c_report:
        st.markdown("### 📊 Verification Metadata")
        st.info(f"🏡 **Village Approved:** `{data['village']}`")
        st.write(f"📍 **Taluka Region:** `{data['taluka']}`")
        st.write(f"👤 **Farmer Profile:** `{data['farmer']}`")
        st.write(f"🆔 **Gut Number Registry:** `{data['gut']}`")
        st.write(f"📏 **Area:** `{data['area']} Acres`")
