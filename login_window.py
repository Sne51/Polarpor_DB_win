from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
import json
import logging


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(400, 200, 300, 150)

        layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

        self.load_users()

    def load_users(self):
        try:
            with open('users.json', 'r') as file:
                self.users = json.load(file)["users"]
                logging.debug(f"Users loaded: {self.users}")
        except Exception as e:
            logging.error(f"Error loading users: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error loading users: {str(e)}")
            self.users = []

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        logging.debug(f"Attempting login with username: {username}, password: {password}")
        for user in self.users:
            if user["username"] == username and user["password"] == password:
                logging.info("Login successful")
                self.accept()
                return
        logging.warning("Incorrect username or password")
        QMessageBox.warning(self, "Error", "Incorrect username or password")
