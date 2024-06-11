import sys
import json
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QSplashScreen, QTabWidget, QWidget, QVBoxLayout, QComboBox, QLineEdit, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from splash_screen import SplashScreen
from firebase_manager import FirebaseManager
from login_window import LoginWindow

# Установка пути для плагинов Qt
plugin_path = "/Users/sk/Documents/EDU_Python/PPT_BD/Polarpor_DB_win_clean/venv/lib/python3.12/site-packages/PyQt5/Qt5/plugins"
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

# Проверка установки пути
if not os.path.isdir(plugin_path):
    print(f"Путь к плагинам Qt не существует: {plugin_path}")
    sys.exit(1)
else:
    print(f"Путь к плагинам Qt установлен: {plugin_path}")

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Инициализация Firebase
try:
    firebase_manager = FirebaseManager()
    logging.info("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Firebase: {str(e)}")
    sys.exit(1)


def load_initial_case_id():
    try:
        base_path = getattr(sys, '_MEIPASS', '.')
        config_path = os.path.join(base_path, 'config.json')
        with open(config_path, 'r') as file:
            data = json.load(file)
            return data['initial_case_id']
    except Exception as e:
        logging.error(f"Error loading initial case ID: {str(e)}")
        return None


def load_initial_proforma_number():
    try:
        base_path = getattr(sys, '_MEIPASS', '.')
        config_path = os.path.join(base_path, 'config.json')
        with open(config_path, 'r') as file:
            data = json.load(file)
            return int(data['initial_proforma_number'])
    except Exception as e:
        logging.error(f"Error loading initial proforma number: {str(e)}")
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система Управления")
        self.setGeometry(100, 100, 1200, 800)  # Установите подходящий размер окна
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.initial_case_id = load_initial_case_id()
        self.initial_proforma_number = load_initial_proforma_number()
        self.setup_case_numbers_tab()
        self.setup_proforma_numbers_tab()

    def add_new_case(self):
        try:
            name = self.name_input.currentText()
            customer = self.customer_input.currentText()
            comment = self.comment_input.text()
            creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_case_id = self.generate_case_id()
            firebase_manager.add_case(new_case_id, name, customer, comment, creation_date)
            logging.info(f"New case added with ID: {new_case_id}")
            self.load_case_table_data()
        except Exception as e:
            logging.error(f"Error adding new case: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при добавлении нового дела: {str(e)}")

    def generate_case_id(self):
        last_case_id = self.get_last_case_id()
        if last_case_id is None:
            new_case_id = str(self.initial_case_id)
        else:
            new_case_id = str(int(last_case_id) + 1)
        return new_case_id

    def get_last_case_id(self):
        cases = firebase_manager.get_all_cases()
        case_ids = [int(case_id) for case_id in cases.keys()]
        return max(case_ids) if case_ids else None

    def setup_case_table_headers(self):
        self.case_table.setColumnCount(5)
        self.case_table.setHorizontalHeaderLabels(["ID", "Имя", "Заказчик", "Комментарий", "Дата создания"])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def setup_case_numbers_tab(self):
        try:
            logging.info("Setting up case numbers tab")
            self.case_numbers_tab = QWidget()
            self.tabs.addTab(self.case_numbers_tab, "Номера дел")
            layout = QVBoxLayout()
            self.case_table = QTableWidget()
            self.case_table.setColumnCount(5)
            self.case_table.setHorizontalHeaderLabels(["Имя", "Заказчик", "Комментарий", "Дата создания", "ID"])
            self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.load_case_table_data()
            self.name_input = QComboBox()
            self.name_input.setEditable(True)
            self.customer_input = QComboBox()
            self.customer_input.setEditable(True)
            self.comment_input = QLineEdit()
            self.add_button = QPushButton("Добавить дело")
            self.add_button.clicked.connect(self.add_new_case)
            self.delete_button = QPushButton("Удалить дело")
            self.delete_button.clicked.connect(self.confirm_delete_case)
            layout.addWidget(self.case_table)
            layout.addWidget(QLabel("Имя:"))
            layout.addWidget(self.name_input)
            layout.addWidget(QLabel("Заказчик:"))
            layout.addWidget(self.customer_input)
            layout.addWidget(QLabel("Комментарий:"))
            layout.addWidget(self.comment_input)
            layout.addWidget(self.add_button)
            layout.addWidget(self.delete_button)
            self.case_numbers_tab.setLayout(layout)
            self.populate_customers()
            self.populate_names()
            logging.info("Case numbers tab setup completed")
        except Exception as e:
            logging.error(f"Error setting up case numbers tab: {str(e)}")

    def load_case_table_data(self):
        try:
            logging.info("Loading case table data")
            self.case_table.setRowCount(0)
            self.case_table.setColumnCount(5)
            self.case_table.setHorizontalHeaderLabels(["Имя", "Заказчик", "Комментарий", "Дата создания", "ID"])

            cases = firebase_manager.get_all_cases()
            logging.debug(f"Cases retrieved: {cases}")
            if cases:
                for case_id, case in cases.items():
                    row_position = self.case_table.rowCount()
                    self.case_table.insertRow(row_position)
                    formatted_date = case.get('creation_date', 'N/A')
                    adjusted_id = int(case_id)
                    self.case_table.setItem(row_position, 4, QTableWidgetItem(str(adjusted_id)))
                    self.case_table.setItem(row_position, 0, QTableWidgetItem(case['name']))
                    self.case_table.setItem(row_position, 1, QTableWidgetItem(case['customer']))
                    self.case_table.setItem(row_position, 2, QTableWidgetItem(case['comment']))
                    self.case_table.setItem(row_position, 3, QTableWidgetItem(formatted_date))
            logging.info("Case table data loaded")
        except Exception as e:
            logging.error(f"Error loading case table data: {str(e)}")

    def setup_proforma_numbers_tab(self):
        try:
            self.proforma_numbers_tab = QWidget()
            self.tabs.addTab(self.proforma_numbers_tab, "Номера проформ")
            layout = QVBoxLayout()
            self.proforma_table = QTableWidget()
            self.proforma_table.setColumnCount(4)
            self.proforma_table.setHorizontalHeaderLabels(["Номер дела", "Имя", "Номер проформы", "Комментарий"])

            self.names_combobox = QComboBox()
            self.case_numbers_combobox = QComboBox()
            self.proforma_comment_input = QLineEdit()

            self.populate_names_combobox()
            self.populate_case_numbers_combobox()

            layout.addWidget(self.proforma_table)
            layout.addWidget(QLabel("Выберите имя из вкладки 'Номера дел':"))
            layout.addWidget(self.names_combobox)
            layout.addWidget(QLabel("Выберите номер дела:"))
            layout.addWidget(self.case_numbers_combobox)
            layout.addWidget(QLabel("Комментарий:"))
            layout.addWidget(self.proforma_comment_input)

            self.add_proforma_button = QPushButton("Добавить проформу")
            self.add_proforma_button.clicked.connect(self.add_proforma_number)
            self.delete_proforma_button = QPushButton("Удалить проформу")
            self.delete_proforma_button.clicked.connect(self.confirm_delete_proforma)

            layout.addWidget(self.add_proforma_button)
            layout.addWidget(self.delete_proforma_button)

            self.proforma_numbers_tab.setLayout(layout)
            self.load_proforma_table_data()
        except Exception as e:
            logging.error(f"Error setting up proforma numbers tab: {str(e)}")

    def add_proforma_number(self):
        try:
            case_number = self.case_numbers_combobox.currentText()
            name = self.names_combobox.currentText()
            comment = self.proforma_comment_input.text()
            proforma_number = self.generate_proforma_number()
            firebase_manager.add_proforma(case_number, name, proforma_number, comment)
            logging.info(f"Proforma number {proforma_number} added for case {case_number}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
            logging.error(f"Error adding proforma number: {str(e)}")

        row_position = self.proforma_table.rowCount()
        self.proforma_table.insertRow(row_position)
        self.proforma_table.setItem(row_position, 0, QTableWidgetItem(case_number))
        self.proforma_table.setItem(row_position, 1, QTableWidgetItem(name))
        self.proforma_table.setItem(row_position, 2, QTableWidgetItem(proforma_number))
        self.proforma_table.setItem(row_position, 3, QTableWidgetItem(comment))

    def populate_names_combobox(self):
        try:
            cases = firebase_manager.get_all_cases()
            names = [case['name'] for case in cases.values()]
            self.names_combobox.addItems(names)
        except Exception as e:
            logging.error(f"Error populating names combobox: {str(e)}")

    def populate_case_numbers_combobox(self):
        try:
            cases = firebase_manager.get_all_cases()
            for case_id, case in cases.items():
                self.case_numbers_combobox.addItem(case_id)
        except Exception as e:
            logging.error(f"Error populating case numbers combobox: {str(e)}")

    def generate_proforma_number(self):
        try:
            last_proforma = self.get_last_proforma_number()
            if last_proforma is None:
                new_proforma_number = str(self.initial_proforma_number)
            else:
                new_proforma_number = str(int(last_proforma) + 1)
            return new_proforma_number
        except Exception as e:
            logging.error(f"Error generating proforma number: {str(e)}")
            return None

    def load_proforma_table_data(self):
        try:
            self.proforma_table.setRowCount(0)
            proformas = firebase_manager.get_all_proformas()
            if proformas:
                for proforma_id, proforma in proformas.items():
                    row_position = self.proforma_table.rowCount()
                    self.proforma_table.insertRow(row_position)
                    self.proforma_table.setItem(row_position, 0, QTableWidgetItem(proforma['case_number']))
                    self.proforma_table.setItem(row_position, 1, QTableWidgetItem(proforma['name']))
                    self.proforma_table.setItem(row_position, 2, QTableWidgetItem(proforma['proforma_number']))
                    self.proforma_table.setItem(row_position, 3, QTableWidgetItem(proforma['comment']))
        except Exception as e:
            logging.error(f"Error loading proforma table data: {str(e)}")

    def confirm_delete_case(self):
        try:
            selected_row = self.case_table.currentRow()
            if selected_row != -1:
                reply = QMessageBox.question(
                    self,
                    "Подтвердить удаление",
                    "Вы уверены, что хотите удалить это дело?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    case_id = self.case_table.item(selected_row, 4).text()
                    firebase_manager.delete_case(case_id)
                    self.load_case_table_data()
        except Exception as e:
            logging.error(f"Error confirming case deletion: {str(e)}")

    def confirm_delete_proforma(self):
        try:
            selected_row = self.proforma_table.currentRow()
            if selected_row != -1:
                reply = QMessageBox.question(
                    self,
                    "Подтвердить удаление",
                    "Вы уверены, что хотите удалить эту проформу?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    proforma_id = self.proforma_table.item(selected_row, 2).text()
                    firebase_manager.delete_proforma(proforma_id)
                    self.load_proforma_table_data()
        except Exception as e:
            logging.error(f"Error confirming proforma deletion: {str(e)}")

    def get_last_proforma_number(self):
        try:
            proformas = firebase_manager.get_all_proformas()
            proforma_numbers = [int(proforma['proforma_number']) for proforma in proformas.values() if 'proforma_number' in proforma]
            return max(proforma_numbers) if proforma_numbers else None
        except Exception as e:
            logging.error(f"Error getting last proforma number: {str(e)}")
            return None

def main():
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    login = LoginWindow()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        splash.finish(window)
        logging.info("Application started successfully")

        sys.exit(app.exec_())
    else:
        logging.info("Login failed or was cancelled")


if __name__ == "__main__":
    main()


