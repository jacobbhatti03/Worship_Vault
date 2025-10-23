import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage, firestore
import tempfile
import os
import json
import traceback

# --- FIREBASE INITIALIZATION ---
try:
    firebase_config = st.secrets["firebase"]

    cred = credentials.Certificate({
        "type": firebase_config["type"],
        "project_id": firebase_config["project_id"],
        "private_key_id": firebase_config["private_key_id"],
        "private_key": firebase_config["private_key"].replace("\\n", "\n"),
        "client_email": firebase_config["client_email"],
        "client_id": firebase_config["client_id"],
        "auth_uri": firebase_config["auth_uri"],
        "token_uri": firebase_config["token_uri"],
        "auth_provider_x509_cert_url": firebase_config["auth_provider_x509_cert_url"],
        "client_x509_cert_url": firebase_config["client_x509_cert_url"]
    })

    # Avoid "already initialized" error on Streamlit refresh
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    # ✅ Create the Firestore client
    db = firestore.client()

except Exception as e:
    st.error(f"❌ Firebase initialization failed: {e}")
    db = None

try:
    pass # your load files logic
except Exception as e:
    import traceback
    st.error(f"❌ Failed to load files: {e}")
    st.code(traceback.format_exc())  # ← shows the exact file + line number


# -------------------------------
# 🔥 Firebase Initialization
# -------------------------------
if not firebase_admin._apps:
    try:
        # ✅ Try to load from Streamlit Cloud secrets (recommended for deployment)
        if "FIREBASE_CONFIG" in st.secrets:
            firebase_config = json.loads(st.secrets["FIREBASE_CONFIG"])
            cred = credentials.Certificate(firebase_config)
        # ✅ Fallback for local testing
        elif os.path.exists("firebase_config.json"):
            cred = credentials.Certificate("firebase_config.json")
        else:
            st.error("❌ Firebase credentials not found. Please add them via Streamlit Secrets or firebase_config.json.")
            st.stop()

        firebase_admin.initialize_app(cred, {
            'storageBucket': 'worshipvault.appspot.com'
        })

        db = firestore.client()
        bucket = storage.bucket()

        # ✅ Connection test
        test_doc = db.collection("connection_test").document("test")
        test_doc.set({"status": "connected"})
        print("✅ Firebase connected successfully")
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {e}")
        print("❌ Firebase initialization failed:", e)
        st.stop()

# -------------------------------
# 🎨 Streamlit UI Setup
# -------------------------------
st.set_page_config(page_title="WorshipVault", page_icon="💿", layout="wide")
st.markdown(
    """
    <h1 style='text-align: center; color: #FFD700;'>💿 WorshipVault</h1>
    <p style='text-align: center; color: gray;'>Store, view, and download all your worship media — simple and secure.</p>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# 📤 Upload Section
# -------------------------------
st.subheader("📤 Upload Media Files")
uploaded_file = st.file_uploader("Choose an image or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        # Upload to Firebase Storage
        blob = bucket.blob(f"uploads/{uploaded_file.name}")
        blob.upload_from_filename(tmp_path)
        blob.make_public()

        # Save metadata to Firestore
        db.collection("files").add({
            "filename": uploaded_file.name,
            "url": blob.public_url
        })

        st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        st.markdown(f"[📄 View File]({blob.public_url})", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        print("❌ Upload failed:", e)

# -------------------------------
# 📁 Display Stored Files
# -------------------------------
st.subheader("📁 Stored Files")
try:
    files = db.collection("uploads").stream()
    for file in files:
        data = file.to_dict()
        st.markdown(f"""
            <div style='padding:10px; border-radius:10px; background-color:#1e1e1e; margin-bottom:10px;'>
            📄 <b>{data['filename']}</b><br>
            <a href='{data['url']}' target='_blank' style='color:#4FC3F7;'>Download</a>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"❌ Failed to load files: {e}")

st.caption("Your uploaded files will remain in the cloud and be available anytime.")


