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

        # Путь к файлу managers.json
        self.managers_file = "managers.json"

    @staticmethod
    def extract_name(data):
        """Вспомогательная функция для извлечения имени из возможных вложенных структур данных."""
        if isinstance(data, dict):
            name = data.get('name')
            if isinstance(name, dict):
                return name.get('name', '').lower()  # Извлекаем строку, если 'name' — это словарь
            return name.lower() if isinstance(name, str) else ''
        return ''

    def get_all_cargo(self):
        """Получение данных о грузах из Firebase."""
        try:
            cargo_ref = self.db.reference('cargo')  # Убедитесь, что этот путь существует в вашей базе Firebase
            cargo_data = cargo_ref.get()
            if cargo_data is None:
                logging.warning("No cargo data found in Firebase.")
                return []
            return cargo_data
        except Exception as e:
            logging.error(f"Failed to fetch cargo data: {e}")
            return []

    def get_all_cases(self):
        """Получить все дела из базы данных Firebase."""
        cases = self.cases_ref.get()
        return cases if cases else {}

    def get_all_clients(self):
        """Получить всех клиентов из базы данных Firebase."""
        try:
            clients = self.clients_ref.get()
            return clients if clients else {}
        except Exception as e:
            logging.error(f"Ошибка при получении данных клиентов: {e}")
            return {}

    def get_all_proformas(self):
        """Получить все проформы из базы данных Firebase."""
        proformas = self.proformas_ref.get()
        return proformas if proformas else {}

    def get_all_suppliers(self):
        """Получить всех поставщиков из базы данных Firebase."""
        suppliers = self.suppliers_ref.get()
        return suppliers if suppliers else {}

    def get_all_managers(self):
        """Загрузка списка менеджеров из файла managers.json."""
        try:
            with open(self.managers_file, "r", encoding="utf-8") as file:
                data = json.load(file)  # Загружаем данные
                logging.debug(f"Loaded managers: {data}")
                # Извлекаем имена менеджеров из структуры {"managers": [...]}
                return [manager["name"] for manager in data.get("managers", []) if "name" in manager]
        except FileNotFoundError:
            logging.error("managers.json file not found.")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding managers.json: {e}")
            return []

    def add_case(self, case_data):
        """Добавить новое дело в базу данных Firebase."""
        cases = self.cases_ref.get()
        logging.debug(f"Current cases: {cases}")
        if not cases:
            case_id = '47000'
        else:
            case_id = str(max([int(cid) for cid in cases.keys() if cid.isdigit()] + [47000]) + 1)
        self.cases_ref.child(case_id).set(case_data)
        return case_id

    def add_client(self, name):
        """Добавить нового клиента в базу данных Firebase."""
        clients = self.get_all_clients()
        logging.debug(f"Current clients: {clients}")
        
        name_lower = name.lower()
        
        if isinstance(clients, dict):
            for client_id, client_data in clients.items():
                if self.extract_name(client_data) == name_lower:
                    return client_id  # Клиент уже существует
            client_id = str(max([int(cid) for cid in clients.keys()] + [0]) + 1)
        elif isinstance(clients, list):
            for client_data in clients:
                if client_data and self.extract_name(client_data) == name_lower:
                    return client_data['id']
            client_id = str(len(clients) + 1)
        else:
            client_id = '1'
        
        new_client_data = {'id': client_id, 'name': name}
        self.clients_ref.child(client_id).set(new_client_data)
        return client_id

    def add_proforma(self, proforma_data):
        """Добавить новую проформу в базу данных Firebase."""
        proformas = self.proformas_ref.get()
        logging.debug(f"Current proformas: {proformas}")
        if not proformas:
            proforma_id = '1000'
        else:
            proforma_id = str(max([int(pid) for pid in proformas.keys() if pid.isdigit()] + [1000]) + 1)
        self.proformas_ref.child(proforma_id).set(proforma_data)
        return proforma_id

    def add_supplier(self, supplier_data):
        """Добавить нового поставщика в базу данных Firebase."""
        suppliers = self.get_all_suppliers()
        logging.debug(f"Current suppliers: {suppliers}")
        
        supplier_name = self.extract_name(supplier_data)  # Используем функцию для извлечения имени
        
        if not supplier_name:
            logging.error("Supplier name is not a valid string.")
            return None

        if isinstance(suppliers, dict):
            for supplier_id, existing_supplier_data in suppliers.items():
                existing_supplier_name = self.extract_name(existing_supplier_data)
                if existing_supplier_name == supplier_name:
                    return supplier_id  # Поставщик уже существует
            supplier_id = str(max([int(sid) for sid in suppliers.keys()] + [0]) + 1)
        elif isinstance(suppliers, list):
            for supplier in suppliers:
                if supplier and self.extract_name(supplier) == supplier_name:
                    return supplier['id']
            supplier_id = str(len(suppliers) + 1)
        else:
            supplier_id = '1'
        
        self.suppliers_ref.child(supplier_id).set(supplier_data)
        return supplier_id

    def delete_case(self, case_id):
        """Удалить дело из базы данных Firebase."""
        if case_id:
            self.cases_ref.child(case_id).delete()

    def delete_client(self, client_id):
        """Удалить клиента из базы данных Firebase."""
        if client_id:
            self.clients_ref.child(client_id).delete()

    def delete_proforma(self, proforma_id):
        """Удалить проформу из базы данных Firebase."""
        if proforma_id:
            self.proformas_ref.child(proforma_id).delete()

    def delete_supplier(self, supplier_id):
        """Удалить поставщика из базы данных Firebase."""
        if supplier_id:
            try:
                self.suppliers_ref.child(supplier_id).delete()
                logging.info(f"Supplier with ID {supplier_id} successfully deleted.")
            except Exception as e:
                logging.error(f"Error deleting supplier with ID {supplier_id}: {e}")

    def check_and_add_client(self, name, check_only=False):
        """Проверить и добавить клиента, если его нет в базе."""
        clients = self.get_all_clients()
        logging.debug(f"Checking and adding client. Current clients: {clients}")
        name_lower = name.lower()
        
        if isinstance(clients, dict):
            for client_id, client_data in clients.items():
                if self.extract_name(client_data) == name_lower:
                    return client_id
        elif isinstance(clients, list):
            for client_data in clients:
                if client_data and self.extract_name(client_data) == name_lower:
                    return client_data['id']
        
        if check_only:
            return None  # Если клиента нет и check_only=True, не добавляем

        return self.add_client(name)
    
    def check_and_add_supplier(self, name, check_only=False):
        """Проверить и добавить поставщика, если его нет в базе."""
        suppliers = self.get_all_suppliers()
        logging.debug(f"Checking and adding supplier. Current suppliers: {suppliers}")
        name_lower = name.lower()
        
        if isinstance(suppliers, dict):
            for supplier_id, supplier_data in suppliers.items():
                if self.extract_name(supplier_data) == name_lower:
                    return supplier_id
        elif isinstance(suppliers, list):
            for supplier_data in suppliers:
                if supplier_data and self.extract_name(supplier_data) == name_lower:
                    return supplier_data['id']
        
        if check_only:
            return None  # Если поставщика нет и check_only=True, не добавляем

        return self.add_supplier({'name': name})
    
    def get_case_numbers(self):
        cases = self.get_all_cases()
        return [case_id for case_id in cases.keys()]
