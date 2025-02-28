import json
import logging
import os
from firebase_admin import credentials, initialize_app, db

class FirebaseManager:
    def __init__(self):
        # Пути к файлам с учетными данными Firebase для Mac и Windows
        cred_path_mac = "/Users/sk/Documents/EDU_Python/PPT_do_quick/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"
        cred_path_win = "C:/Users/Usr/Documents/Polarpor_DB_win/Polarpor_DB_win/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"

        # Проверка наличия файла с учетными данными и инициализация Firebase
        if os.path.exists(cred_path_mac):
            cred = credentials.Certificate(cred_path_mac)
        elif os.path.exists(cred_path_win):
            cred = credentials.Certificate(cred_path_win)
        else:
            raise FileNotFoundError("Firebase credentials file not found.")

        initialize_app(cred, {
            'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })

        # Инициализация ссылок на коллекции в Firebase
        self.cases_ref = db.reference('cases')
        self.clients_ref = db.reference('clients')
        self.proformas_ref = db.reference('proformas')
        self.suppliers_ref = db.reference('suppliers')
        self.cargo_ref = db.reference('cargo')

        # Путь к файлу с менеджерами – менеджеры загружаются из JSON
        self.managers_file = "managers.json"

    def get_all_cases(self):
        cases = self.cases_ref.get()
        return cases if cases else {}

    def get_all_clients(self):
        clients = self.clients_ref.get()
        return clients if clients else {}

    def get_all_proformas(self):
        proformas = self.proformas_ref.get()
        return proformas if proformas else {}

    def get_all_suppliers(self):
        suppliers = self.suppliers_ref.get()
        return suppliers if suppliers else {}

    def get_all_cargo(self):
        cargo = self.cargo_ref.get()
        return cargo if cargo else {}

    def get_all_managers(self):
        """Загружает список менеджеров из файла managers.json."""
        try:
            with open(self.managers_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                managers = [manager["name"] for manager in data.get("managers", []) if "name" in manager]
                logging.debug(f"Loaded managers: {managers}")
                return managers
        except FileNotFoundError:
            logging.error("Файл managers.json не найден.")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка декодирования managers.json: {e}")
            return []

    def add_cargo(self, cargo_data):
        """Добавляет новую запись груза в базу Firebase."""
        # Определяем новый ID для груза (например, на основе максимального существующего ID)
        existing = self.cargo_ref.get()
        if isinstance(existing, dict):
            try:
                max_id = max([int(cid) for cid in existing.keys() if cid.isdigit()])
            except ValueError:
                max_id = 0
        else:
            max_id = 0
        new_id = str(max_id + 1)
        self.cargo_ref.child(new_id).set(cargo_data)
        logging.info(f"Груз с ID {new_id} добавлен.")
        return new_id

    def delete_cargo(self, cargo_id):
        """Удаляет запись груза по ID."""
        self.cargo_ref.child(cargo_id).delete()
        logging.info(f"Груз с ID {cargo_id} удален.")