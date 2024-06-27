import firebase_admin
from firebase_admin import credentials, db
import logging
import os
import platform

class FirebaseManager:
    def __init__(self):
        try:
            if platform.system() == "Windows":
                cred_path = "C:/Users/Usr/Documents/Polarpor_DB_win/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"
            else:
                cred_path = "/Users/sk/Documents/EDU_Python/PPT_do_quick/polapordb-firebase-adminsdk-5hp8q-9a328b73d0.json"

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app/'
            })
            self.cases_ref = db.reference('cases')
            self.proformas_ref = db.reference('proformas')
            self.clients_ref = db.reference('clients')
            logging.info("Firebase initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Firebase: {e}")

    def get_all_cases(self):
        try:q
            return self.cases_ref.get() or {}
        except Exception as e:
            logging.error(f"Error retrieving cases: {e}")
            return {}

    def add_case(self, case_data):
        try:
            self.cases_ref.push(case_data)
        except Exception as e:
            logging.error(f"Error adding case: {e}")

    def delete_case(self, case_id):
        try:
            self.cases_ref.child(case_id).delete()
        except Exception as e:
            logging.error(f"Error deleting case: {e}")

    def get_all_proformas(self):
        try:
            return self.proformas_ref.get() or {}
        except Exception as e:
            logging.error(f"Error retrieving proformas: {e}")
            return {}

    def add_proforma(self, proforma_data):
        try:
            self.proformas_ref.push(proforma_data)
        except Exception as e:
            logging.error(f"Error adding proforma: {e}")

    def delete_proforma(self, proforma_id):
        try:
            self.proformas_ref.child(proforma_id).delete()
        except Exception as e:
            logging.error(f"Error deleting proforma: {e}")

    def get_all_clients(self):
        try:
            clients = self.clients_ref.get()
            if clients is None:
                return {}
            elif isinstance(clients, list):
                return {str(i): client for i, client in enumerate(clients) if client is not None}
            else:
                return clients
        except Exception as e:
            logging.error(f"Error retrieving clients: {e}")
            return {}

    def add_client(self, name):
        try:
            clients = self.get_all_clients()
            if name in [client_data['name'] for client_data in clients.values()]:
                raise ValueError("Клиент с таким именем уже существует")
            client_id = max([int(cid) for cid in clients.keys()] or [0]) + 1
            self.clients_ref.child(str(client_id)).set({'name': name})
        except Exception as e:
            logging.error(f"Error adding client: {e}")

    def delete_client(self, client_id):
        try:
            self.clients_ref.child(client_id).delete()
        except Exception as e:
            logging.error(f"Error deleting client: {e}")

    def check_and_add_client(self, client_name):
        clients = self.get_all_clients()
        for client_id, client_data in clients.items():
            if client_data['name'] == client_name:
                return client_id
        self.add_client(client_name)
        clients = self.get_all_clients()
        for client_id, client_data in clients.items():
            if client_data['name'] == client_name:
                return client_id
        raise ValueError("Не удалось добавить клиента")
