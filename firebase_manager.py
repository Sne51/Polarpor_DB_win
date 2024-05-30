import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Инициализация Firebase
cred = credentials.Certificate('/Users/sk/Documents/EDU_Python/PPT_BD/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app'
})


# Класс для работы с Firebase Realtime Database
class FirebaseManager:
    def __init__(self):
        self.ref = db.reference('cases')

    def add_case(self, case_id, name, customer, comment):
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ref.child(case_id).set({
            'name': name,
            'customer': customer,
            'comment': comment,
            'creation_date': creation_date
        })

    def get_all_cases(self):
        return self.ref.get()

    def delete_case(self, case_id):
        self.ref.child(case_id).delete()
