import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import platform

print("Определение пути к файлу учетных данных...")

# Определяем путь к файлу учетных данных в зависимости от операционной системы
if platform.system() == "Windows":
    cred_path = r'C:\\Users\\Usr\\Documents\\Polarpor_DB_win\\Polarpor_DB_win\\polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json'
else:
    cred_path = '/Users/sk/Documents/EDU_Python/PPT_BD/Polarpor_DB_win_clean/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json'

print(f"Путь к файлу учетных данных: {cred_path}")

# Проверка существования файла учетных данных
if not os.path.exists(cred_path):
    raise FileNotFoundError(f"Файл учетных данных не найден: {cred_path}")

print("Файл учетных данных найден. Инициализация Firebase...")

# Инициализация Firebase
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app'
})

print("Firebase инициализирован. Создание класса FirebaseManager...")


# Класс для работы с Firebase Realtime Database
class FirebaseManager:
    def __init__(self):
        self.ref = db.reference('cases')
        self.proforma_ref = db.reference('proformas')
        self.users_ref = db.reference('users')

    def add_case(self, case_id, name, customer, comment, creation_date):
        print(f"Добавление дела: case_id={case_id}, name={name}, customer={customer}, comment={comment}")
        self.ref.child(case_id).set({
            'name': name,
            'customer': customer,
            'comment': comment,
            'creation_date': creation_date
        })
        print(f"Дело {case_id} добавлено успешно.")

    def add_proforma(self, case_number, name, proforma_number, comment):
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.proforma_ref.child(proforma_number).set({
            'case_number': case_number,
            'name': name,
            'proforma_number': proforma_number,
            'comment': comment,
            'creation_date': creation_date
        })
        print(f"Проформа {proforma_number} добавлена успешно.")

    def get_all_cases(self):
        print("Получение всех дел...")
        return self.ref.get()

    def get_all_proformas(self):
        print("Получение всех проформ...")
        return self.proforma_ref.get()

    def delete_case(self, case_id):
        print(f"Удаление дела: case_id={case_id}")
        self.ref.child(case_id).delete()
        print(f"Дело {case_id} удалено успешно.")

    def delete_proforma(self, proforma_id):
        print(f"Удаление проформы: proforma_id={proforma_id}")
        self.proforma_ref.child(proforma_id).delete()
        print(f"Проформа {proforma_id} удалена успешно.")


print("Класс FirebaseManager создан.")
