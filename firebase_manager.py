import logging
from firebase_admin import credentials, initialize_app, db
import os

class FirebaseManager:
    def __init__(self):
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
        self.cases_ref = db.reference('cases')
        self.clients_ref = db.reference('clients')
        self.proformas_ref = db.reference('proformas')
    
    def get_all_cases(self):
        cases = self.cases_ref.get()
        return cases if cases else {}

    def get_all_clients(self):
        clients = self.clients_ref.get()
        return clients if clients else {}

    def get_all_proformas(self):
        proformas = self.proformas_ref.get()
        return proformas if proformas else {}

    def add_case(self, case_data):
        cases = self.cases_ref.get()
        logging.debug(f"Current cases: {cases}")
        if not cases:
            case_id = '47000'
        else:
            case_id = str(max([int(cid) for cid in cases.keys() if cid.isdigit()] + [47000]) + 1)
        self.cases_ref.child(case_id).set(case_data)
        return case_id

    def add_client(self, name):
        clients = self.get_all_clients()
        logging.debug(f"Current clients: {clients}")
        if isinstance(clients, dict):
            client_id = str(max([int(cid) for cid in clients.keys()] + [0]) + 1)
        elif isinstance(clients, list):
            client_id = str(len(clients) + 1)
        else:
            client_id = '1'
        new_client_data = {'id': client_id, 'name': name}
        self.clients_ref.child(client_id).set(new_client_data)
        return client_id

    def delete_case(self, case_id):
        if case_id:
            self.cases_ref.child(case_id).delete()

    def delete_client(self, client_id):
        if client_id:
            self.clients_ref.child(client_id).delete()

    def check_and_add_client(self, name):
        clients = self.get_all_clients()
        logging.debug(f"Checking and adding client. Current clients: {clients}")
        if isinstance(clients, dict):
            for client_id, client_data in clients.items():
                if client_data['name'] == name:
                    return client_id
        elif isinstance(clients, list):
            for client_data in clients:
                if client_data and client_data['name'] == name:
                    return client_data['id']
        return self.add_client(name)
