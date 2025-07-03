import streamlit as st
from firebase_config import auth, db
from streamlit_autorefresh import st_autorefresh

from predict import predict_pneumonia
from PIL import Image
from heatmap import get_heatmap
import plotly.express as px
from datetime import datetime
import pandas as pd
import tempfile
from email_sender import send_email
from history_logger import init_db, save_prediction, get_all_history
from pdf_generator import generate_pdf

# 🔧 Initialization
init_db()
st.set_page_config(page_title="MediScan AI", layout="centered")

# 🔄 Auto-refresh every 5 seconds for real-time messaging
if st.session_state.get("role") in ["doctor", "patient"]:
    st_autorefresh(interval=5000, key="chat_refresh")

def sanitize_email(email):
    return email.replace(".", "_").replace("@", "_at_")



# 🖤 Dark Theme
st.markdown("""
    <style>
    .stApp {
        background-color: black;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)





def messaging_portal():
    st.markdown("## 💬 Messaging Portal")

    user_email = st.session_state.user['email']
    user_role = st.session_state.role

    users = db.child("users").get(token=st.session_state.user['idToken'])

    # Chat target selection
    if user_role == "doctor":
        patients = [u.val()["email"] for u in users.each() if u.val()["role"] == "patient"]
        selected_user = st.selectbox("Select a patient to chat with", patients)
        role_of_selected = "patient"

    elif user_role == "patient":
        doctors = [u.val()["email"] for u in users.each() if u.val()["role"] == "doctor"]
        selected_user = st.selectbox("Select a doctor to chat with", doctors)
        role_of_selected = "doctor"

    else:
        st.info("Messaging is only available for doctors and patients.")
        return
    
    st.markdown(f"### 🧑‍💼 Chatting with: **{selected_user}** ({role_of_selected.capitalize()})")

    # Standardized chat_id (ensures both roles access same chat)
    emails_sorted = sorted([sanitize_email(user_email), sanitize_email(selected_user)])
    chat_id = f"{emails_sorted[0]}__{emails_sorted[1]}"

    # if st.button("🔄 Refresh Messages"):
    #     st.session_state.chat_refresh = not st.session_state.get("chat_refresh", False)
    #     st.rerun()

    # Fetch and display messages
    messages = db.child("messages").child(chat_id).get(token=st.session_state.user['idToken'])
    st.markdown("### 📜 Conversation History")

    if messages.each():
        for msg in messages.each():
            data = msg.val()
            align = "🩺 Doctor" if data["sender"] == "doctor" else "👤 Patient"
            st.markdown(f"**{align}:** {data['message']}  \n<sub>{data['timestamp']}</sub>", unsafe_allow_html=True)
    else:
        st.info("No messages yet.")

    # Send new message
    with st.form("chat_form", clear_on_submit=True):
        new_msg = st.text_area("Write your message", height=80)
        submitted = st.form_submit_button("Send")
        if submitted and new_msg.strip():
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.child("messages").child(chat_id).push({
                "sender": user_role,
                "message": new_msg,
                "timestamp": now
            }, token=st.session_state.user['idToken'])
            st.success("✅ Message sent.")
            st.rerun()


# 🧠 Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "just_registered" not in st.session_state:
    st.session_state.just_registered = False
if "login_error" not in st.session_state:
    st.session_state.login_error = False


# ============================
# 🔐 LOGIN / REGISTER SCREEN
# ============================
if st.session_state.user is None:
    st.title("🔐 MediScan AI Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.session_state.just_registered:
        st.success("✅ Account created successfully. Please log in.")
        st.session_state.just_registered = False

    if st.session_state.login_error:
        st.error("❌ Invalid email or password")
        st.session_state.login_error = False

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user

            users = db.child("users").get(token=user['idToken'])
            for u in users.each():
                if u.val()["email"] == email:
                    st.session_state.role = u.val()["role"]
                    break

            st.experimental_set_query_params(logged_in="1")
            st.rerun()

        except:
            st.session_state.login_error = True
            st.rerun()

    # 📝 Register Section
    st.markdown("---")
    st.subheader("New here?")
    role = st.selectbox("Select Role", ["doctor", "patient", "admin"])
    if st.button("Register New Account"):
        try:
        # 🔍 Check if email already exists
          existing_users = db.child("users").get()
          if any(u.val()["email"] == email for u in existing_users.each()):
            st.error("❌ Email already registered.")
          else:
            user = auth.create_user_with_email_and_password(email, password)
            user_info = {"email": email, "role": role}
            db.child("users").push(user_info)
            st.session_state.just_registered = True
            st.rerun()
        except Exception as e:
          st.error(f"❌ Error: {e}")

# ============================
# ✅ MAIN APP UI
# ============================
else:
    st.sidebar.success(f"🔓 Logged in as **{st.session_state.role.capitalize()}**")
    st.title("🩺 MediScan AI – Pneumonia Detection from X-Ray")
    
    email = st.session_state.user['email']
    st.write(f"Welcome, **{email}** 👋")
    
    with st.expander("💬 Open Messaging Portal"):
        messaging_portal()

    
    
    st.markdown("Upload a chest X-ray image and get an instant pneumonia prediction using deep learning.")

    if st.session_state.role != "admin":
        st.subheader("📝 Patient Information")
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        scan_date = st.date_input("Scan Date", value=datetime.today())

        if st.session_state.role == "doctor":
            st.text_input("Receiver Email (optional, to send report)", key="receiver_email")

        uploaded_files = st.file_uploader("Upload one or more Chest X-Ray images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        if uploaded_files:
            results = []
            for file in uploaded_files:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                img = Image.open(file).convert("RGB")
                img.save(temp_file.name)

                result, confidence = predict_pneumonia(temp_file.name)

                results.append({
                    "Image": file.name,
                    "Prediction": result,
                    "Confidence": round(confidence, 2)
                })

                st.image(img, caption=f"{file.name}", use_column_width=True)
                heatmap_path = get_heatmap(temp_file.name, save_path=f"{temp_file.name}_gradcam.jpg")
                st.image(heatmap_path, caption="AI Heatmap", use_column_width=True)
                
                notes = ""
                if st.session_state.role == "doctor":
                   notes = st.text_area("Doctor Notes (will be added to PDF)")
                
                if st.session_state.role == "doctor":
                    receiver_email = st.session_state.get("receiver_email")
                    if receiver_email:
                        send_email(
                            receiver_email,
                            subject="MediScan AI Diagnosis Report",
                            body=f"Patient: {patient_name}\nPrediction: {result}\nConfidence: {confidence}",
                            attachment_path=heatmap_path
                        )
                        st.success(f"📧 Email sent to {receiver_email}")

                save_prediction(patient_name, age, gender, file.name, result, round(confidence, 2))

                report_path = f"{temp_file.name}_report.pdf"
                generate_pdf(patient_name, age, gender, result, confidence, temp_file.name, heatmap_path, report_path, notes)
                st.success("📄 PDF report generated!")
                st.download_button("⬇️ Download Report", data=open(report_path, "rb"), file_name="MediScan_Report.pdf", mime="application/pdf")

            df = pd.DataFrame(results)
            st.subheader("🧾 Batch Prediction Results")
            st.dataframe(df)

    st.markdown("---")
    with st.expander("📜 View Patient History"):
        history = get_all_history()
        if history:
          df = pd.DataFrame(history, columns=[
            "Patient Name", "Age", "Gender", "Image", "Prediction", "Confidence", "Time"
            ])
          df["Time"] = pd.to_datetime(df["Time"])

          if st.session_state.role == "patient":
            df = df[df["Patient Name"] == patient_name]
          else:
            st.markdown("### 🔍 Filter Records")

            # Search by name
            search_name = st.text_input("Search by Patient Name")

            # Filter by date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01").date())
            with col2:
                end_date = st.date_input("End Date", value=datetime.today().date())

            # Apply filters
            if search_name:
                df = df[df["Patient Name"].str.contains(search_name, case=False)]

            df = df[(df["Time"].dt.date >= start_date) & (df["Time"].dt.date <= end_date)]

          st.dataframe(df)
          if st.session_state.role in ["doctor", "admin"]:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="patient_history.csv",
                mime="text/csv"
            )
        else:
          st.info("No history records found yet.")

    st.markdown("---")
    if st.session_state.role == "doctor":
        with st.expander("📊 Analytics Dashboard"):
            history = get_all_history()
            if history:
                df = pd.DataFrame(history, columns=[
                    "Patient Name", "Age", "Gender", "Image", "Prediction", "Confidence", "Time"
                ])
                df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
                
                # 🔢 Summary Metrics
                total_preds = len(df)
                pneumonia_cases = (df["Prediction"] == "Pneumonia").sum()
                normal_cases = (df["Prediction"] == "Normal").sum()

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Predictions", total_preds)
                col2.metric("Pneumonia Cases", pneumonia_cases)
                col3.metric("Normal Cases", normal_cases)


                st.subheader("🔵 Pneumonia vs Normal Distribution")
                pie_data = df["Prediction"].value_counts().reset_index()
                pie_data.columns = ["Prediction", "count"]
                st.plotly_chart(px.pie(pie_data, names="Prediction", values="count", title="Prediction Distribution"), use_container_width=True)

                st.subheader("🟣 Gender-wise Prediction Count")
                bar_data = df.groupby(["Gender", "Prediction"]).size().reset_index(name="Count")
                st.plotly_chart(px.bar(bar_data, x="Gender", y="Count", color="Prediction", barmode="group"), use_container_width=True)

                st.subheader("📈 Daily Case Trend")
                df["Date"] = df["Time"].dt.date
                trend_data = df.groupby(["Date", "Prediction"]).size().reset_index(name="Cases")
                st.plotly_chart(px.line(trend_data, x="Date", y="Cases", color="Prediction", markers=True), use_container_width=True)
            else:
                st.warning("⚠️ Not enough data to generate analytics.")

    if st.session_state.role == "admin":
        with st.expander("👥 Admin: Manage Users"):
            users = db.child("users").get(token=st.session_state.user['idToken'])
            user_list = []
            keys = []
            for u in users.each():
                data = u.val()
                user_list.append(data)
                keys.append(u.key())

            df = pd.DataFrame(user_list)
            st.dataframe(df)

            selected_email = st.selectbox("Select a user to delete", [u['email'] for u in user_list if u['email'] != email])
            if st.button("❌ Delete Selected User"):
                for i, u in enumerate(user_list):
                    if u['email'] == selected_email:
                        db.child("users").child(keys[i]).remove()
                        st.success(f"Deleted user {selected_email}")
                        st.rerun()
            
            st.markdown("---")
            st.markdown("### 🔁 Update User Role")

            selected_user = st.selectbox("Select a user to update role", [u['email'] for u in user_list if u['email'] != email])
            new_role = st.selectbox("Select new role", ["doctor", "patient", "admin"])

            if st.button("Update Role"):
               for i, u in enumerate(user_list):
                 if u['email'] == selected_user:
                   updated_info = {
                    "email": selected_user,
                    "role": new_role
                    }
                   db.child("users").child(keys[i]).update(updated_info)
                   st.success(f"✅ Updated role for {selected_user} to {new_role}")
                   st.rerun()

        with st.expander("📄 Admin: System-wide Logs"):
            history = get_all_history()
            if history:
                df = pd.DataFrame(history, columns=[
                    "Patient Name", "Age", "Gender", "Image", "Prediction", "Confidence", "Time"
                ])
                st.dataframe(df)
            else:
                st.info("No prediction history available.")
                
    

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()
        