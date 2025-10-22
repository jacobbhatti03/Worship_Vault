import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
import tempfile
import os

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'worshipvault.appspot.com'
    })

db = firestore.client()
bucket = storage.bucket()

# Streamlit UI setup
st.set_page_config(page_title="WorshipVault", page_icon="💿", layout="wide")
st.markdown(
    """
    <h1 style='text-align: center; color: #FFD700;'>💿 WorshipVault</h1>
    <p style='text-align: center; color: gray;'>Store, view, and download all your worship media — simple and secure.</p>
    """,
    unsafe_allow_html=True
)

# Upload Section
st.subheader("📤 Upload Media Files")
uploaded_file = st.file_uploader("Choose an image or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # Upload to Firebase
    blob = bucket.blob(f"uploads/{uploaded_file.name}")
    blob.upload_from_filename(tmp_path)
    blob.make_public()

    # Save metadata to Firestore
    db.collection("uploads").add({
        "filename": uploaded_file.name,
        "url": blob.public_url
    })

    st.success(f"✅ {uploaded_file.name} uploaded successfully!")

# Display Stored Files
st.subheader("📁 Stored Files")
files = db.collection("uploads").stream()
for file in files:
    data = file.to_dict()
    st.markdown(f"""
        <div style='padding:10px; border-radius:10px; background-color:#1e1e1e; margin-bottom:10px;'>
        📄 <b>{data['filename']}</b><br>
        <a href='{data['url']}' target='_blank' style='color:#4FC3F7;'>Download</a>
        </div>
    """, unsafe_allow_html=True)

st.caption("Your uploaded files will remain in the cloud and be available anytime.")
