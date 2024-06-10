import firebase_admin
from firebase_admin import credentials, db
import os
import platform

# Определение пути к файлу учетных данных в зависимости от операционной системы
if platform.system() == "Windows":
    cred_path = r'C:\\Users\\Usr\\Documents\\Polarpor_DB_win_clean\\polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json'
else:
    cred_path = '/Users/sk/Documents/EDU_Python/PPT_BD/Polarpor_DB_win_clean/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json'

# Инициализация Firebase
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# Добавление пользователей
users_ref = db.reference('users')

users_ref.set({
    'user1': {'password': 'password1'},
    'user2': {'password': 'password2'}
})

print("Пользователи добавлены.")
