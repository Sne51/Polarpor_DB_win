import json
import logging
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox


class LoginDialog(QDialog):
    """
    Загружает UI из переданного файла (абсолютный путь).
    Если ui_file не передан — ищет .../Polarpor_DB_win/ui/login.ui.
    users.json читается по абсолютному пути из корня проекта.
    """
    def __init__(self, ui_file: str | None = None, parent=None):
        super().__init__(parent)

        # Корень проекта: .../Polarpor_DB_win
        root_dir = Path(__file__).resolve().parents[2]
        if ui_file is None:
            ui_file = str(root_dir / 'ui' / 'login.ui')

        try:
            uic.loadUi(ui_file, self)
        except Exception as e:
            logging.error(f"Ошибка загрузки UI: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить интерфейс: {e}")
            raise

        # Элементы
        self.usernameInput = getattr(self, "usernameInput", None)
        self.passwordInput = getattr(self, "passwordInput", None)
        self.loginButton = getattr(self, "loginButton", None)
        self.cancelButton = getattr(self, "cancelButton", None)

        # Пути к данным
        self.users_file = root_dir / 'users.json'

        # Сигналы
        if self.loginButton:
            self.loginButton.clicked.connect(self.check_credentials)
        if self.cancelButton:
            self.cancelButton.clicked.connect(self.reject)

    def _load_users(self) -> dict:
        if not self.users_file.exists():
            raise FileNotFoundError(f"Файл пользователей не найден: {self.users_file}")
        with open(self.users_file, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        return data

    def check_credentials(self, checked: bool = False):
        logging.debug("check_credentials called")
        username = self.usernameInput.text().strip() if self.usernameInput else ""
        password = self.passwordInput.text().strip() if self.passwordInput else ""
        logging.debug(f"username: {username}, password: {password}")

        try:
            users = self._load_users()
            logging.debug(f"Loaded users: {users}")
            ok = False
            for rec in users.get("users", []):
                if rec.get("username") == username and rec.get("password") == password:
                    ok = True
                    break
            if ok:
                logging.debug("User authenticated successfully")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка входа", "Неверный логин или пароль")
        except Exception as e:
            logging.error(f"Auth error: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка аутентификации: {e}")