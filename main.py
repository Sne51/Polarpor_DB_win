import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QPushButton, QLabel, QMessageBox, QComboBox
from PyQt5.QtCore import Qt
from datetime import datetime
from firebase_admin import credentials, initialize_app, db
import os

# Установка уровня логирования
logging.basicConfig(level=logging.DEBUG)

# Инициализация Firebase
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление делами")
        self.setGeometry(100, 100, 800, 600)
        self.firebase_manager = FirebaseManager()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setup_case_numbers_tab()
        self.setup_proforma_numbers_tab()
        self.setup_clients_tab()

    def setup_case_numbers_tab(self):
        logging.info("Setting up case numbers tab")
        self.case_numbers_tab = QWidget()
        self.tabs.addTab(self.case_numbers_tab, "Номера дел")
        layout = QVBoxLayout()
        self.case_table = QTableWidget()
        self.setup_case_table_headers()
        self.load_case_table_data()
        layout.addWidget(self.case_table)

        self.case_name_input = QComboBox()
        self.case_name_input.setEditable(True)
        self.case_client_input = QComboBox()
        self.case_client_input.setEditable(True)
        self.case_add_button = QPushButton("Добавить дело")
        self.case_add_button.clicked.connect(self.add_new_case)
        self.case_delete_button = QPushButton("Удалить дело")
        self.case_delete_button.clicked.connect(self.confirm_delete_case)

        layout.addWidget(QLabel("Имя:"))
        layout.addWidget(self.case_name_input)
        layout.addWidget(QLabel("Клиент:"))
        layout.addWidget(self.case_client_input)
        layout.addWidget(self.case_add_button)
        layout.addWidget(self.case_delete_button)

        self.case_numbers_tab.setLayout(layout)
        self.load_unique_names()
        logging.info("Case numbers tab setup completed")

    def setup_case_table_headers(self):
        headers = ["ID", "Имя", "Клиент", "Клиент ID", "Комментарий", "Дата создания"]
        self.case_table.setColumnCount(len(headers))
        self.case_table.setHorizontalHeaderLabels(headers)
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_case_table_data(self):
        logging.info("Loading case table data")
        self.case_table.setRowCount(0)
        cases = self.firebase_manager.get_all_cases()
        logging.debug(f"Cases loaded: {cases}")
        if cases:
            for case_id, case_data in cases.items():
                if case_data:
                    row_position = self.case_table.rowCount()
                    self.case_table.insertRow(row_position)
                    self.case_table.setItem(row_position, 0, QTableWidgetItem(case_id))
                    self.case_table.setItem(row_position, 1, QTableWidgetItem(case_data.get('name', '')))
                    self.case_table.setItem(row_position, 2, QTableWidgetItem(case_data.get('client_name', '')))
                    self.case_table.setItem(row_position, 3, QTableWidgetItem(case_data.get('client', '')))
                    self.case_table.setItem(row_position, 4, QTableWidgetItem(case_data.get('comment', '')))
                    self.case_table.setItem(row_position, 5, QTableWidgetItem(case_data.get('date_created', '')))
        logging.info("Case table data loaded")

    def load_unique_names(self):
        logging.info("Loading unique names")
        self.case_name_input.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            unique_names = set()
            for case_id, case_data in cases.items():
                unique_names.add(case_data.get('name', ''))
            self.case_name_input.addItems(sorted(unique_names))
        logging.info("Unique names loaded")

    def add_new_case(self):
        name = self.case_name_input.currentText().strip()
        client_name = self.case_client_input.currentText().strip()
        if not name or not client_name:
            QMessageBox.warning(self, "Внимание", "Имя дела и клиент не могут быть пустыми")
            return

        comment = ''
        date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            client_id = self.firebase_manager.check_and_add_client(client_name)
            new_case = {
                'name': name,
                'client_name': client_name,
                'client': client_id,
                'comment': comment,
                'date_created': date_created
            }
            logging.debug(f"New case data: {new_case}")
            case_id = self.firebase_manager.add_case(new_case)
            logging.debug(f"New case ID: {case_id}")
            self.load_case_table_data()
            self.load_unique_names()
            self.load_client_table_data()  # Add this line to reload the client table after adding a new client
            QMessageBox.information(self, "Успех", f"Дело добавлено успешно с ID: {case_id}")
        except Exception as e:
            logging.error(f"Error adding new case: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении дела: {e}")

    def confirm_delete_case(self):
        selected_items = self.case_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите дело для удаления")
            return

        row = selected_items[0].row()
        case_id = self.case_table.item(row, 0).text()
        response = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить дело с ID {case_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_case(case_id)
                self.load_case_table_data()
                self.load_unique_names()
                QMessageBox.information(self, "Успех", "Дело удалено успешно")
            except Exception as e:
                logging.error(f"Error deleting case: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении дела: {e}")

    def setup_proforma_numbers_tab(self):
        logging.info("Setting up proforma numbers tab")
        self.proforma_numbers_tab = QWidget()
        self.tabs.addTab(self.proforma_numbers_tab, "Номера проформ")
        layout = QVBoxLayout()
        self.proforma_table = QTableWidget()
        self.setup_proforma_table_headers()
        self.load_proforma_table_data()
        layout.addWidget(self.proforma_table)

        self.proforma_name_input = QComboBox()
        self.proforma_name_input.setEditable(True)
        self.proforma_client_input = QComboBox()
        self.proforma_client_input.setEditable(True)
        self.proforma_comment_input = QLineEdit()
        self.proforma_add_button = QPushButton("Добавить проформу")
        self.proforma_add_button.clicked.connect(self.add_new_proforma)
        self.proforma_delete_button = QPushButton("Удалить проформу")
        self.proforma_delete_button.clicked.connect(self.confirm_delete_proforma)

        layout.addWidget(QLabel("Имя:"))
        layout.addWidget(self.proforma_name_input)
        layout.addWidget(QLabel("Клиент:"))
        layout.addWidget(self.proforma_client_input)
        layout.addWidget(QLabel("Комментарий:"))
        layout.addWidget(self.proforma_comment_input)
        layout.addWidget(self.proforma_add_button)
        layout.addWidget(self.proforma_delete_button)

        self.proforma_numbers_tab.setLayout(layout)
        logging.info("Proforma numbers tab setup completed")

    def setup_proforma_table_headers(self):
        headers = ["ID", "Имя", "Клиент", "Комментарий", "Дата создания"]
        self.proforma_table.setColumnCount(len(headers))
        self.proforma_table.setHorizontalHeaderLabels(headers)
        self.proforma_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_proforma_table_data(self):
        logging.info("Loading proforma table data")
        self.proforma_table.setRowCount(0)
        proformas = self.firebase_manager.get_all_proformas()
        logging.debug(f"Proformas loaded: {proformas}")
        if proformas:
            for proforma_id, proforma_data in proformas.items():
                row_position = self.proforma_table.rowCount()
                self.proforma_table.insertRow(row_position)
                self.proforma_table.setItem(row_position, 0, QTableWidgetItem(proforma_id))
                self.proforma_table.setItem(row_position, 1, QTableWidgetItem(proforma_data.get('name', '')))
                self.proforma_table.setItem(row_position, 2, QTableWidgetItem(proforma_data.get('client', '')))
                self.proforma_table.setItem(row_position, 3, QTableWidgetItem(proforma_data.get('comment', '')))
                self.proforma_table.setItem(row_position, 4, QTableWidgetItem(proforma_data.get('date_created', '')))
        logging.info("Proforma table data loaded")

    def add_new_proforma(self):
        name = self.proforma_name_input.currentText().strip()
        client = self.proforma_client_input.currentText().strip()
        comment = self.proforma_comment_input.text().strip()
        date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not name or not client:
            QMessageBox.warning(self, "Внимание", "Имя проформы и клиент не могут быть пустыми")
            return

        try:
            new_proforma = {
                'name': name,
                'client': client,
                'comment': comment,
                'date_created': date_created
            }
            proforma_id = self.firebase_manager.proformas_ref.push(new_proforma).key
            self.load_proforma_table_data()
            QMessageBox.information(self, "Успех", f"Проформа добавлена успешно с ID: {proforma_id}")
        except Exception as e:
            logging.error(f"Error adding new proforma: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении проформы: {e}")

    def confirm_delete_proforma(self):
        selected_items = self.proforma_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите проформу для удаления")
            return

        proforma_id = selected_items[0].text()
        response = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить проформу с ID {proforma_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.proformas_ref.child(proforma_id).delete()
                self.load_proforma_table_data()
                QMessageBox.information(self, "Успех", "Проформа удалена успешно")
            except Exception as e:
                logging.error(f"Error deleting proforma: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении проформы: {e}")

    def setup_clients_tab(self):
        logging.info("Setting up clients tab")
        self.clients_tab = QWidget()
        self.tabs.addTab(self.clients_tab, "Клиенты")
        layout = QVBoxLayout()
        self.client_table = QTableWidget()
        self.setup_client_table_headers()
        self.load_client_table_data()
        layout.addWidget(self.client_table)

        self.client_name_input = QLineEdit()
        self.client_add_button = QPushButton("Добавить клиента")
        self.client_add_button.clicked.connect(self.add_new_client)
        self.client_delete_button = QPushButton("Удалить клиента")
        self.client_delete_button.clicked.connect(self.confirm_delete_client)

        layout.addWidget(QLabel("Имя:"))
        layout.addWidget(self.client_name_input)
        layout.addWidget(self.client_add_button)
        layout.addWidget(self.client_delete_button)

        self.clients_tab.setLayout(layout)
        logging.info("Clients tab setup completed")

    def setup_client_table_headers(self):
        headers = ["ID", "Имя"]
        self.client_table.setColumnCount(len(headers))
        self.client_table.setHorizontalHeaderLabels(headers)
        self.client_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_client_table_data(self):
        logging.info("Loading client table data")
        self.client_table.setRowCount(0)
        clients = self.firebase_manager.get_all_clients()
        logging.debug(f"Clients loaded: {clients}")
        if isinstance(clients, dict):
            for client_id, client_data in clients.items():
                row_position = self.client_table.rowCount()
                self.client_table.insertRow(row_position)
                self.client_table.setItem(row_position, 0, QTableWidgetItem(client_id))
                self.client_table.setItem(row_position, 1, QTableWidgetItem(client_data.get('name', '') if isinstance(client_data, dict) else client_data))
        elif isinstance(clients, list):
            for client_data in clients:
                if client_data:
                    row_position = self.client_table.rowCount()
                    self.client_table.insertRow(row_position)
                    self.client_table.setItem(row_position, 0, QTableWidgetItem(client_data['id']))
                    self.client_table.setItem(row_position, 1, QTableWidgetItem(client_data['name']))
        logging.info("Client table data loaded")

    def add_new_client(self):
        name = self.client_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Имя клиента не может быть пустым")
            return

        try:
            client_id = self.firebase_manager.add_client(name)
            self.load_client_table_data()  # Add this line to reload the client table after adding a new client
            QMessageBox.information(self, "Успех", f"Клиент добавлен успешно с ID: {client_id}")
        except Exception as e:
            logging.error(f"Error adding client: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении клиента: {e}")

    def confirm_delete_client(self):
        selected_items = self.client_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите клиента для удаления")
            return

        row = selected_items[0].row()
        client_id = self.client_table.item(row, 0).text()
        response = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить клиента с ID {client_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_client(client_id)
                self.load_client_table_data()
                QMessageBox.information(self, "Успех", "Клиент удален успешно")
            except Exception as e:
                logging.error(f"Error deleting client: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении клиента: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
