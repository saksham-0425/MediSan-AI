import streamlit as st
from firebase_config import db
from datetime import datetime

st.set_page_config(page_title="💬 Messaging Portal")

st.title("💬 Doctor-Patient Chat")

# Ensure user is logged in
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Please login to use messaging feature.")
    st.stop()

user_email = st.session_state.user["email"]
role = st.session_state.role

# Utility to create chat_id
def get_chat_id(doctor, patient):
    return f"{doctor}:{patient}" if doctor < patient else f"{patient}:{doctor}"

# Role-specific logic
if role == "doctor":
    st.subheader("Select Patient to Chat With")
    users = db.child("users").get(token=st.session_state.user['idToken'])
    patients = [u.val()["email"] for u in users.each() if u.val()["role"] == "patient"]
    selected_patient = st.selectbox("Choose Patient", patients)

    if selected_patient:
        chat_id = get_chat_id(user_email, selected_patient)

elif role == "patient":
    selected_patient = user_email
    # Get doctor from Firebase (any doctor, or store it beforehand)
    users = db.child("users").get(token=st.session_state.user['idToken'])
    doctor = next((u.val()["email"] for u in users.each() if u.val()["role"] == "doctor"), None)
    chat_id = get_chat_id(doctor, user_email)
else:
    st.warning("Admin can't use messaging.")
    st.stop()

# Display chat messages
st.markdown("---")
st.subheader("📨 Chat")

messages = db.child("messages").child(chat_id).get(token=st.session_state.user['idToken'])
chat = []
if messages.each():
    for msg in messages.each():
        data = msg.val()
        sender = data["sender"]
        content = data["text"]
        timestamp = data["timestamp"]
        st.markdown(f"**{sender}** ({timestamp}): {content}")
else:
    st.info("No messages yet. Start the conversation!")

# Input to send message
st.markdown("---")
st.subheader("✍️ Send Message")
message = st.text_input("Type your message")
if st.button("Send"):
    if message.strip():
        db.child("messages").child(chat_id).push({
            "text": message,
            "sender": user_email,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, token=st.session_state.user['idToken'])
        st.success("Message sent!")
        st.rerun()
    else:
        st.warning("Message cannot be empty.")
