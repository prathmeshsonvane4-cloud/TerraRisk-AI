import os
os.system("pip install folium streamlit-folium reportlab earthengine-api pandas geopy")

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from geopy.geocoders import Nominatim

st.set_page_config(
    page_title="TerraRisk-AI | Latur Regional Suite",
    page_icon="🛡️",
    layout="wide"
)

# ==============================================================================
# 🏛️ FIXED LATUR REVENUE DATABASE (100% CORRECT MAPPING)
# ==============================================================================
# आता प्रत्येक तालुक्याच्या नावासोबत मराठी नाव एकाच ठिकाणी मॅप केले आहे जेणेकरून गल्लत होणार नाही.
LATUR_GOVT_DATABASE = {
    "Latur (लातूर)": {
        "Center": [18.4088, 76.5604],
        "Villages": ["Murud (मुरुड)", "Harangul Bk. (हरंगुळ बु.)", "Chincholi (चिंचोली)", "Pangaon (पांगण)", "Arvi (आर्वी)", "Khandapur (खांदापूर)"]
    },
    "Ausa (औसा)": {
        "Center": [18.2531, 76.5019],
        "Villages": ["Killari (किल्लारी)", "Lamjana (लामजना)", "Matola (मातोळा)", "Belkund (बेलकुंड)", "Ashiv (आशिव)"]
    },
    "Nilanga (निलंगा)": {
        "Center": [18.1278, 76.7570],
        "Villages": ["Aurad Shahajani (औराद शहाजानी)", "Kasarsirsi (कासारशिरशी)", "Halgara (हळगरा)", "Shirur Tajband (शिरूर ताजबंद)"]
    },
    "Udgir (उदगीर)": {
        "Center": [18.3934, 77.1186],
        "Villages": ["Wadhwana (वाढवणा)", "Nideban (निदेबन)", "Her (हेर)", "Dongarshelki (डोंगरशेळकी)"]
    },
    "Ahmedpur (अहमदपूर)": {
        "Center": [18.7058, 76.9328],
        "Villages": ["Kingaon (किनगाव)", "Shirur Tajband (शिरूर ताजबंद)", "Hadolti (हाडोळती)", "Valandi (वळंदी)"]
    },
    "Chakur (चाकुर)": {
        "Center": [18.5238, 76.8631],
        "Villages": ["Vadwal Nagnath (वडवळ नागनाथ)", "Latur Road (लातूर रोड)", "Nalegaon (नळेगाव)", "Chapoli (चापोली)"]
    },
    "Renapur (रेणापूर)": {
        "Center": [18.5218, 76.5214],
        "Villages": ["Pohregaon (पोहरेगाव)", "Digol (डिगोळ)", "Pangaon (पांगण)", "Kharola (खरोला)", "Motegaon (मोतेगाव)", "Renapur Rural (रेणापूर ग्रामीण)", "Phaswadi (फासवाडी)"]
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

st.title("🛡️ TerraRisk-AI: Latur Enterprise Land Verification Ledger")
st.write("---")

if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

if not st.session_state.form_submitted:
    st.subheader("📋 Step 1: Institutional Credential & Land Entry / माहिती नोंदवा")
    
    with st.form(key="verification_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 👤 Auditor / User Details")
            off_name = st.text_input(label="Officer Name (बँक अधिकाऱ्याचे नाव):", value="Prathmesh Sonvane")
            inst_name = st.text_input(label="Institution Name (बँक किंवा शाखेचे नाव):", value="State Bank of India (SBI)")
            p_role = st.selectbox("Your Profile / तुमची भूमिका:", ["Bank Credit Officer (बँक अधिकारी)"])
            
            report_level = st.radio(
                "What level of report do you need?",
                ["Village Level / वैयक्तिक शेतकरी (7/12 गट क्रमांक)", "Taluka Level Portfolio (संपूर्ण तालुका एकत्रित रिपोर्ट)"]
            )
            
            if "Village Level" in report_level:
                f_name = st.text_input(label="Farmer Name (7/12 प्रमाणे नाव):", value="Ramrao Vitthal Patil")
                g_num = st.text_input(label="Gut / Survey / Plot Number (गट क्रमांक):", value="104")
                l_area = st.text_input(label="Declared Land Area (Acres):", value="4.5")
            else:
                f_name, g_num, l_area = "N/A", "ALL GUTS", "N/A"
            
        with c2:
            st.markdown("##### 🗺️ Target Location Routing")
            st.selectbox("Select State (राज्य):", ["Maharashtra"])
            st.selectbox("Select District (जिल्हा):", ["Latur (लातूर)"])
            
            # FIXED: थेट लिस्ट सॉर्ट करून वापरली जेणेकरून UI आणि डेटा मॅच होईल
            taluka_list = sorted(list(LATUR_GOVT_DATABASE.keys()))
            selected_taluka = st.selectbox("Select Taluka (तालुका निवडा):", taluka_list)
            
            # FIXED: वर निवडलेल्या तालुक्याचा अचूक डेटा इथून खेचला जाईल
            actual_taluka_data = LATUR_GOVT_DATABASE[selected_taluka]
            
            if "Village Level" in report_level:
                # आता रेणापूर निवडल्यास रेणापूरचीच गावे दिसतील!
                selected_village = st.selectbox("Select Village (गाव निवडा):", sorted(actual_taluka_data["Villages"]))
            else:
                selected_village = "ALL VILLAGES"
            
            a_scope = st.radio("Evaluation Scope:", ["Single Asset (1 Farmer / वैयक्तिक शेतकरी)", "Regional Portfolio"])
        
        submit_btn = st.form_submit_button(label="🔓 Open Mapping Engine")
        
        if submit_btn:
            st.session_state.detected_lat = actual_taluka_data["Center"][0]
            st.session_state.detected_lon = actual_taluka_data["Center"][1]
            st.session_state.user_data = {
                "officer": off_name, "org": inst_name, "taluka": selected_taluka, 
                "village": selected_village, "farmer": f_name, "gut": g_num, "level": report_level
            }
            st.session_state.form_submitted = True
            st.rerun()
    st.stop()

# Phase 2 - Map View
ud = st.session_state.user_data
st.success(f"🔓 GPS Active for {ud['village']}, {ud['taluka']}")

col1, col2 = st.columns([1.6, 1.4])
with col1:
    m = folium.Map(location=[st.session_state.detected_lat, st.session_state.detected_lon], zoom_start=14)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google Satellite', name='Google').add_to(m)
    map_data = st_folium(m, width=650, height=450)
with col2:
    st.markdown("### 📊 Live Audit Metadata")
    st.write(f"🏢 **Taluka Base:** `{ud['taluka']}`")
    st.write(f"🏡 **Village Selected:** `{ud['village']}`")
    st.write(f"🆔 **Gut No:** `{ud['gut']}`")
