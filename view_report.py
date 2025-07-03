import streamlit as st
from firebase_config import db
from PIL import Image
import os

# 🖤 Dark Theme
st.set_page_config(page_title="📄 View MediScan Report", layout="centered")
st.markdown("""
    <style>
    .stApp {
        background-color: black;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 MediScan – Shared Report")

# Get token from URL
query_params = st.experimental_get_query_params()
token = query_params.get("token", [None])[0]

if not token:
    st.error("❌ Invalid or missing token.")
    st.stop()

# Fetch report from Firebase
try:
    report = db.child("shared_reports").child(token).get().val()
except:
    report = None

if not report:
    st.error("❌ Report not found or expired.")
else:
    st.success("✅ Report Loaded Successfully!")

    st.markdown(f"**👤 Patient Name:** {report['patient_name']}")
    st.markdown(f"**📅 Age:** {report['age']}")
    st.markdown(f"**🚻 Gender:** {report['gender']}")
    st.markdown(f"**📈 Prediction:** {report['prediction']} ({report['confidence']}%)")
    if report["notes"]:
        st.markdown(f"**📝 Doctor Notes:** {report['notes']}")
    
    st.markdown("### 🩻 X-ray Image")
    st.image(report["image_path"], caption="Original X-ray", use_column_width=True)
    
    st.markdown("### 🔥 AI Heatmap")
    st.image(report["heatmap_path"], caption="Grad-CAM Heatmap", use_column_width=True)
