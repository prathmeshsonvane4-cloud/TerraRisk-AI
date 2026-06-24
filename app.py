import streamlit as st
import streamlit_folium as st_folium
import folium
from folium.plugins import Draw
import json
import datetime
import ee

# --- १. STREAMLIT CONFIGURATION ---
st.set_page_config(page_title="TerraRisk-AI: GeoAI Platform", layout="wide")
st.title("🌍 TerraRisk-AI (लातूर जिल्हा GeoAI प्लॅटफॉर्म)")
st.subheader("Bilingual Satellite Risk Assessment Engine | सॅटेलाइट आधारित जोखीम मूल्यांकन")

# --- २. GOOGLE EARTH ENGINE AUTHENTICATION ---
@st.cache_resource
def initialize_ee():
    try:
        # Streamlit Secrets मधून गुगल क्रेडेंशियल्स मिळवणे
        if "gcp_service_account" in st.secrets:
            secret_dict = dict(st.secrets["gcp_service_account"])
            # Newlines व्यवस्थित करण्यासाठी (\n ची अडचण दूर करणे)
            secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
            
            credentials = ee.ServiceAccountCredentials(
                secret_dict["client_email"], 
                key_data=json.dumps(secret_dict)
            )
            ee.Initialize(credentials, project='geoai-flood-analytics')
            return True
        else:
            st.error("❌ Streamlit Secrets मध्ये 'gcp_service_account' सापडला नाही!")
            return False
    except Exception as e:
        st.error(f"❌ Earth Engine जोडताना एरर आली: {e}")
        return False

ee_connected = initialize_ee()

# --- ३. DYNAMIC MAP WITH DRAWING TOOLS ---
st.markdown("### 🗺️ Draw Polygon on Area of Interest / नकाशावर क्षेत्र निवडा (पॉलिगॉन ड्रॉ करा)")

m = folium.Map(location=[18.4088, 76.5604], zoom_start=11)

# Folium Draw tool setup
draw = Draw(
    export=False,
    position='topleft',
    draw_options={
        'poly': {'allowIntersection': False, 'showArea': True},
        'rectangle': True,
        'circle': False,
        'marker': False,
        'polyline': False
    }
)
draw.add_to(m)

# Display map in Streamlit
map_data = st_folium.st_folium(m, width=1100, height=500)

# Capture Area coordinates
coordinates = None
if map_data and 'all_drawings' in map_data and map_data['all_drawings']:
    last_drawing = map_data['all_drawings'][-1]
    if last_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
        coordinates = last_drawing['geometry']['coordinates'][0]

if coordinates:
    st.success("✅ Area Selected Successfully! / क्षेत्र यशस्वीरित्या निवडले गेले आहे!")
else:
    st.warning("⚠️ Please draw a polygon on the map to run Earth Engine Analytics. / सॅटेलाइट डेटा मिळवण्यासाठी कृपया नकाशावर पॉलिगॉन काढा.")

# --- ४. GOOGLE EARTH ENGINE SATELLITE PROCESSING LOGIC ---
def run_satellite_analytics(coords):
    if not ee_connected:
        return {"flood_risk": "N/A", "ndwi": 0.0, "status": "EE Error"}
    
    try:
        # Create EE Geometry from Drawn Polygon
        aoi = ee.Geometry.Polygon(coords)
        
        # Sentinel-1 SAR GRD Data Fetching (Same as your Colab Notebook)
        s1_collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
                         .filterBounds(aoi)
                         .filterDate('2025-01-01', datetime.date.today().strftime('%Y-%m-%d'))
                         .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
                         .filter(ee.Filter.eq('instrumentMode', 'IW')))
        
        # Calculate Backscatter stats over the AOI
        mean_image = s1_collection.select('VV').mean()
        stats = mean_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        vv_val = stats.get('VV', -15.0) if stats else -15.0
        
        # Water/Flood Detection Threshold Logic
        # -18 dB पेक्षा कमी व्हॅल्यू पाण्याचे अस्तित्व दर्शवते
        if vv_val < -18.0:
            flood_idx = 0.85
            risk_en = "High Hazard (Water Retention Detected)"
            risk_mr = "उच्च जोखीम (पाणी साचल्याचे संकेत)"
        elif vv_val < -14.0:
            flood_idx = 0.45
            risk_en = "Moderate Risk"
            risk_mr = "मध्यम जोखीम क्षेत्र"
        else:
            flood_idx = 0.12
            risk_en = "Low Hazard Risk / Safe Zone"
            risk_mr = "कमी जोखीम / सुरक्षित क्षेत्र"
            
        return {
            "flood_index": flood_idx,
            "risk_en": risk_en,
            "risk_mr": risk_mr,
            "vv_db": round(vv_val, 2)
        }
    except Exception as e:
        return {"error": str(e)}

# --- ५. DYNAMIC REPORT GENERATION AND DOWNLOAD ---
if coordinates:
    st.markdown("---")
    st.markdown("### 📄 Run Satellite Query & Generate Report / विश्लेषण करा")
    
    if st.button("🚀 Run Live GeoAI Satellite Analysis"):
        with st.spinner("Connecting to Google Earth Engine & Processing Sentinel Imagery..."):
            
            # Run the background satellite analysis
            results = run_satellite_analytics(coordinates)
            report_date = datetime.date.today().strftime("%d-%m-%Y")
            
            if "error" in results:
                st.error(f"Earth Engine Analytics failed: {results['error']}")
            else:
                # English Section Content
                en_report = f"""
======================================================
        TERRARISK-AI: SATELLITE RISK ASSESSMENT REPORT
======================================================
Date Generated: {report_date}
Target Area Geometry: Chosen Map Polygon Area (Latur Region)
Geospatial Extent: {json.dumps(coordinates[:2])}...

[GEOSPATIAL AI SATELLITE ANALYTICS - RECENT PASS]
1. Flood Risk Index: {results['flood_index']}
2. SAR Backscatter Value (VV dB): {results['vv_db']}
3. Hazard Classification: {results['risk_en']}
4. Infrastructure Recommendation: Approved based on current satellite thresholds.
======================================================
"""
                
                # Marathi Section Content
                mr_report = f"""
======================================================
        टेरารिस्क-एआय: सॅटेलाइट जोखीम मूल्यांकन अहवाल
======================================================
अहवाल दिनांक: {report_date}
