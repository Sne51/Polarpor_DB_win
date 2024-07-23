from PyQt5.QtWidgets import QDialog, QLineEdit, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5 import uic
import json


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("login.ui", self)
        self.loginButton.clicked.connect(self.check_credentials)
        self.passwordInput.setEchoMode(QLineEdit.Password)

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
        username = self.usernameInput.text()
        password = self.passwordInput.text()
        with open('users.json', 'r') as file:
            users = json.load(file)
        for user in users['users']:
            if user['username'] == username and user['password'] == password:
                self.accept()
                return
        QMessageBox.warning(self, 'Ошибка', 'Неверные имя пользователя или пароль')