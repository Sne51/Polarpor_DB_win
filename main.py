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
                    format='%(name)s - %(levelname)s - %(message)s')

# Инициализация Firebase
firebase_manager = FirebaseManager()


def load_initial_case_id():
    base_path = getattr(sys, '_MEIPASS', '.')
    config_path = os.path.join(base_path, 'config.json')
    with open(config_path, 'r') as file:
        data = json.load(file)
        return data['initial_case_id']

def load_initial_proforma_number():
    base_path = getattr(sys, '_MEIPASS', '.')
    config_path = os.path.join(base_path, 'config.json')
    with open(config_path, 'r') as file:
        data = json.load(file)
        return int(data['initial_proforma_number'])

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

    def setup_case_table_headers(self):
        self.case_table.setColumnCount(5)
        self.case_table.setHorizontalHeaderLabels(["ID", "Имя", "Заказчик", "Комментарий", "Дата создания"])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def setup_case_numbers_tab(self):
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

    def setup_proforma_numbers_tab(self):
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

    def add_proforma_number(self):
        try:
            case_number = self.case_numbers_combobox.currentText()
            name = self.names_combobox.currentText()
            comment = self.proforma_comment_input.text
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

        row_position = self.proforma_table.rowCount()
        self.proforma_table.insertRow(row_position)
        self.proforma_table.setItem(row_position, 0, QTableWidgetItem(case_number))
        self.proforma_table.setItem(row_position, 1, QTableWidgetItem(name))
        self.proforma_table.setItem(row_position, 2, QTableWidgetItem(proforma_number))
        self.proforma_table.setItem(row_position, 3, QTableWidgetItem(comment))

    def populate_names_combobox(self):
        cases = firebase_manager.get_all_cases()
        names = [case['name'] for case in cases.values()]
        self.names_combobox.addItems(names)

    def populate_case_numbers_combobox(self):
        cases = firebase_manager.get_all_cases()
        for case_id, case in cases.items():
            self.case_numbers_combobox.addItem(case_id)

    def generate_proforma_number(self):
        last_proforma = self.get_last_proforma_number()
        if last_proforma is None:
            new_proforma_number = str(self.initial_proforma_number)
        else:
            new_proforma_number = str(int(last_proforma) + 1)
        return new_proforma_number

    def load_case_table_data(self):
        self.case_table.setRowCount(0)
        self.case_table.setColumnCount(5)
        self.case_table.setHorizontalHeaderLabels(["Имя", "Заказчик", "Комментарий", "Дата создания", "ID"])

        cases = firebase_manager.get_all_cases()
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

    def load_proforma_table_data(self):
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

    def confirm_delete_case(self):
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

    def confirm_delete_proforma(self):
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

    def get_last_proforma_number(self):
        proformas = firebase_manager.get_all_proformas()
        proforma_numbers = [int(proforma['proforma_number']) for proforma in proformas.values() if 'proforma_number' in proforma]
        return max(proforma_numbers) if proforma_numbers else None


def main():
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    login = LoginWindow()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        splash.finish(window)

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
