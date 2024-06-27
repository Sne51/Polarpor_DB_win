import firebase_admin
from firebase_admin import credentials, db
import os
import platform
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
from database import DatabaseManager


class AddUserWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Add Client')

        layout = QVBoxLayout()

        self.client_id_input = QLineEdit(self)
        self.client_id_input.setPlaceholderText('Enter Client ID')
        layout.addWidget(self.client_id_input)

        self.add_button = QPushButton('Add Client', self)
        self.add_button.clicked.connect(self.add_client)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_client(self):
        client_id = self.client_id_input.text()
        if client_id:
            client_data = {'client_id': client_id}
            if self.db.add_client(client_data):
                QMessageBox.information(self, 'Success', 'Client added successfully!')
            else:
                QMessageBox.warning(self, 'Error', 'Client already exists!')
        else:
            QMessageBox.warning(self, 'Error', 'Client ID cannot be empty!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AddUserWindow()
    window.show()
    sys.exit(app.exec_())

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
