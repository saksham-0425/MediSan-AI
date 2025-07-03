import pyrebase

firebase_config = {
    "apiKey": "AIzaSyDLI9Wjpo2-e-li5bSrhR1ky6qA7RdzQ2c",
    "authDomain": "mediscan-ai-bd957.firebaseapp.com",
    "databaseURL": "https://mediscan-ai-bd957-default-rtdb.firebaseio.com/",
    "projectId": "mediscan-ai-bd957",
    "storageBucket": "mediscan-ai-bd957.appspot.com",
    "messagingSenderId": "849624048358",
    "appId": "1:849624048358:web:0e8496e6438fc8e4211127",
    "measurementId": "G-YZ5TVD3CY7"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()  # ✅ MAKE SURE THIS LINE EXISTS

# ✅ Export both
__all__ = ["auth", "db"]
