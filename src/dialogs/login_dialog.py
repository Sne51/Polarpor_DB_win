# src/dialogs/login_dialog.py
import json
import logging
import requests
from PyQt5.QtWidgets import QDialog, QMessageBox, QLineEdit
from PyQt5.QtCore import QTimer
from PyQt5 import uic

logging.basicConfig(level=logging.DEBUG)

def check_internet_connection(url='http://www.google.com/', timeout=5):
    try:
        response = requests.head(url, timeout=timeout)
        return True if response.status_code == 200 else False
    except requests.ConnectionError:
        return False

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/login.ui", self)  # Обновляем путь к файлу ui
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.cancelButton.clicked.connect(self.reject)

        # Устанавливаем фокус на поле логина после полной инициализации
        QTimer.singleShot(0, self.usernameInput.setFocus)

        # Устанавливаем порядок фокуса
        self.setTabOrder(self.usernameInput, self.passwordInput)
        self.setTabOrder(self.passwordInput, self.loginButton)
        self.setTabOrder(self.loginButton, self.cancelButton)

        # Set the window size
        self.resize(320, 160)  # Adjust the size as needed

        # Increase the font size of all widgets
        font = self.font()
        font.setPointSize(14)  # Adjust the font size as needed
        self.setFont(font)

        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.loginButton.clicked.connect(self.check_credentials)

    def check_credentials(self):
        logging.debug("check_credentials called")
        logging.debug(f"username: {self.usernameInput.text()}, password: {self.passwordInput.text()}")

        username = self.usernameInput.text()
        password = self.passwordInput.text()

        logging.debug("Checking internet connection in check_credentials")
        if not check_internet_connection():
            logging.debug("No internet connection detected in check_credentials")
            QMessageBox.warning(self, 'Ошибка', 'Проверьте соединение с Интернетом')
            return

        logging.debug("Checking credentials")
        with open('users.json', 'r') as file:
            users = json.load(file)
            logging.debug(f"Loaded users: {users}")
        for user in users['users']:
            if user['username'] == username and user['password'] == password:
                logging.debug("User authenticated successfully")
                self.accept()
                return
        logging.debug("Incorrect username or password")
        QMessageBox.warning(self, 'Ошибка', 'Неверные имя пользователя или пароль')
