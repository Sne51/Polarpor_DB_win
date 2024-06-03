import sys
import json
import os
import logging
from datetime import datetime
from firebase_manager import FirebaseManager
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QComboBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)
from PyQt5.QtCore import Qt

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
        self.setGeometry(100, 100, 800, 600)
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.initial_case_id = load_initial_case_id()  # Загрузка начального ID дел
        self.initial_proforma_number = load_initial_proforma_number()  # Загрузка начального номера проформы
        self.setup_case_numbers_tab()
        self.setup_proforma_numbers_tab()

    def setup_case_table_headers(self):
        self.case_table.setColumnCount(5)  # Устанавливаем количество столбцов
        # Устанавливаем заголовки столбцов с ID на первом месте
        self.case_table.setHorizontalHeaderLabels(
            ["ID", "Имя", "Заказчик", "Комментарий", "Дата создания"]
        )
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Растягиваем столбцы для заполнения пространства таблицы

    def setup_case_numbers_tab(self):
        self.case_numbers_tab = QWidget()
        self.tabs.addTab(self.case_numbers_tab, "Номера дел")
        layout = QVBoxLayout()
        self.case_table = QTableWidget()
        self.case_table.setColumnCount(5)
        self.case_table.setHorizontalHeaderLabels(
            ["Имя", "Заказчик", "Комментарий", "Дата создания", "ID"]
        )
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
        self.proforma_comment_input = QLineEdit()  # Убрано ограничение высоты

        self.populate_names_combobox()  # Заполняем комбобокс именами
        self.populate_case_numbers_combobox()  # Заполняем комбобокс номерами дел

        layout.addWidget(self.proforma_table)
        layout.addWidget(QLabel("Выберите имя из вкладки 'Номера дел':"))
        layout.addWidget(self.names_combobox)
        layout.addWidget(QLabel("Выберите номер дела:"))
        layout.addWidget(self.case_numbers_combobox)
        layout.addWidget(QLabel("Комментарий:"))  # Перемещение комментария на последнее место
        layout.addWidget(self.proforma_comment_input)

        self.add_proforma_button = QPushButton("Добавить проформу")
        self.add_proforma_button.clicked.connect(self.add_proforma_number)
        self.delete_proforma_button = QPushButton("Удалить проформу")
        self.delete_proforma_button.clicked.connect(self.confirm_delete_proforma)

        layout.addWidget(self.add_proforma_button)
        layout.addWidget(self.delete_proforma_button)

        self.proforma_numbers_tab.setLayout(layout)
        self.load_proforma_table_data()  # Загрузка данных проформ при инициализации

    def add_proforma_number(self):
        try:
            case_number = self.case_numbers_combobox.currentText()
            name = self.names_combobox.currentText()
            comment = self.proforma_comment_input.text()
            proforma_number = self.generate_proforma_number()

            firebase_manager.add_proforma(proforma_number, {
                'case_number': case_number,
                'name': name,
                'proforma_number': proforma_number,
                'comment': comment,
                'creation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Обновите ваш GUI здесь

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

        # Добавляем проформу в таблицу интерфейса
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

    def add_new_case(self):
        name = self.name_input.currentText().strip()
        customer = self.customer_input.currentText().strip()
        comment = self.comment_input.text().strip()

        if name:
            try:
                case_id = str(self.initial_case_id + len(firebase_manager.get_all_cases()))
                firebase_manager.add_case(case_id, {
                    'name': name,
                    'customer': customer,
                    'comment': comment,
                    'creation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.load_case_table_data()
                self.name_input.setCurrentIndex(-1)
                self.customer_input.setCurrentIndex(-1)
                self.comment_input.clear()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
        else:
            QMessageBox.warning(self, "Ошибка ввода", "Поле 'Имя' должно быть заполнено.")

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
                case_id = self.case_table.item(selected_row, 0).text()
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

    def populate_customers(self):
        cases = firebase_manager.get_all_cases()
        customers = [case['customer'] for case in cases.values()]
        self.customer_input.addItems(customers)

    def populate_names(self):
        cases = firebase_manager.get_all_cases()
        names = [case['name'] for case in cases.values()]
        self.name_input.addItems(names)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
