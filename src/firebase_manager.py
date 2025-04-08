import json
import logging
import os
from firebase_admin import credentials, initialize_app, db

class FirebaseManager:
    def __init__(self):
        # Пути к файлам с учетными данными для Mac и Windows
        cred_path_mac = "/Users/sk/Documents/EDU_Python/PPT_do_quick/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"
        cred_path_win = "C:/Users/Usr/Documents/Polarpor_DB_win/Polarpor_DB_win/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"

        if os.path.exists(cred_path_mac):
            cred = credentials.Certificate(cred_path_mac)
        elif os.path.exists(cred_path_win):
            cred = credentials.Certificate(cred_path_win)
        else:
            raise FileNotFoundError("Firebase credentials file not found.")

        initialize_app(cred, {
            'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })

        # Инициализация ссылок на коллекции
        self.cases_ref = db.reference('cases')
        self.clients_ref = db.reference('clients')
        self.proformas_ref = db.reference('proformas')
        self.suppliers_ref = db.reference('suppliers')
        self.cargo_ref = db.reference('cargo')
        
        # Файл со списком менеджеров (он остаётся локальным JSON-файлом)
        self.managers_file = "managers.json"

    def get_all_cases(self):
        cases = self.cases_ref.get()
        return cases if cases else {}

    def get_all_clients(self):
        try:
            clients = self.clients_ref.get()
            return clients if clients else {}
        except Exception as e:
            logging.error(f"Ошибка при получении данных клиентов: {e}")
            return {}

    def get_all_proformas(self):
        proformas = self.proformas_ref.get()
        return proformas if proformas else {}

    def get_all_suppliers(self):
        suppliers = self.suppliers_ref.get()
        return suppliers if suppliers else {}

    def get_all_managers(self):
        try:
            with open(self.managers_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                logging.debug(f"Loaded managers: {data}")
                return [manager["name"] for manager in data.get("managers", []) if "name" in manager]
        except Exception as e:
            logging.error(f"Ошибка загрузки списка менеджеров: {e}")
            return []

    def get_all_cargo(self):
        try:
            cargo_data = self.cargo_ref.get()
            if cargo_data is None:
                logging.warning("Нет данных о грузах в Firebase.")
                return {}
            return cargo_data
        except Exception as e:
            logging.error(f"Ошибка при получении данных о грузе: {e}")
            return {}

    def add_cargo(self, cargo_data):
        try:
            cargo = self.get_all_cargo()
            # Если данные представлены в виде словаря – вычисляем новый ID
            if isinstance(cargo, dict):
                existing_ids = [int(cid) for cid in cargo.keys() if cid.isdigit()]
                new_id = str(max(existing_ids) + 1) if existing_ids else "1"
            else:
                new_id = "1"
            self.cargo_ref.child(new_id).set(cargo_data)
        except Exception as e:
            logging.error(f"Ошибка при добавлении груза: {e}")
            raise

    def delete_cargo(self, cargo_id):
        try:
            self.cargo_ref.child(cargo_id).delete()
        except Exception as e:
            logging.error(f"Ошибка при удалении груза с ID {cargo_id}: {e}")
            raise