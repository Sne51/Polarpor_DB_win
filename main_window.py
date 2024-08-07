import sys
import json
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QMessageBox, QSplashScreen, QComboBox, QHeaderView, QLabel, QLineEdit
from PyQt5.QtCore import Qt, QTimer, QDateTime, QEvent
from PyQt5.QtGui import QPixmap, QScreen, QColor, QGuiApplication
from PyQt5 import uic
from firebase_manager import FirebaseManager
from qt_material import apply_stylesheet

# Импорт функций поиска
from search_functions import search_in_case_table, search_in_proforma_table, search_in_client_table

logging.basicConfig(level=logging.DEBUG)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.firebase_manager = FirebaseManager()

        self.setWindowTitle("База")

        self.addCaseButton.clicked.connect(self.add_new_case)
        self.deleteCaseButton.clicked.connect(self.confirm_delete_case)
        self.addProformaButton.clicked.connect(self.add_new_proforma)
        self.deleteProformaButton.clicked.connect(self.confirm_delete_proforma)
        self.addClientButton.clicked.connect(self.add_new_client)
        self.deleteClientButton.clicked.connect(self.confirm_delete_client)

        # Подключение кнопки поиска к методу search_items
        self.searchButton.clicked.connect(self.search_items)

        # Заполнение выпадающего списка
        self.searchComboBox.addItems(["Case", "Proforma", "Client"])

        self.setup_case_table()
        self.setup_proforma_table()
        self.setup_client_table()
        self.load_proforma_table_data()  # Ensure this method is called on initialization

        # Масштабирование окна в зависимости от разрешения экрана
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.6), int(screen.height() * 0.6))

        # Увеличение шрифта всех виджетов
        font = self.font()
        font.setPointSize(12)  # Здесь можно настроить нужный размер шрифта
        self.setFont(font)

        # Установка фильтра событий для отслеживания изменения размера окна
        self.installEventFilter(self)

    def search_items(self):
        search_text = self.searchInput.text().strip().lower()
        search_type = self.searchComboBox.currentText()
        if search_type == "Case":
            search_in_case_table(self.caseTable, self.firebase_manager, search_text)
        elif search_type == "Proforma":
            search_in_proforma_table(self.proformaTable, self.firebase_manager, search_text)
        elif search_type == "Client":
            search_in_client_table(self.clientTable, self.firebase_manager, search_text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Resize and source is self:
            self.resize_tables()
        return super(MainWindow, self).eventFilter(source, event)

    def resize_tables(self):
        self.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def setup_case_table(self):
        headers = ["ID", "Имя", "Клиент", "Клиент ID", "Комментарий", "Дата создания"]
        self.caseTable.setColumnCount(len(headers))
        self.caseTable.setHorizontalHeaderLabels(headers)
        self.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_case_table_data()
        self.load_unique_names()

    def setup_proforma_table(self):
        headers = ["Номер дела", "Проформа", "Имя", "Клиент", "Комментарий", "Дата создания"]
        self.proformaTable.setColumnCount(len(headers))
        self.proformaTable.setHorizontalHeaderLabels(headers)
        self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def setup_client_table(self):
        headers = ["ID", "Имя"]
        self.clientTable.setColumnCount(len(headers))
        self.clientTable.setHorizontalHeaderLabels(headers)
        self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_client_table_data()

    def load_case_table_data(self):
        logging.info("Loading case table data")
        self.caseTable.setRowCount(0)
        cases = self.firebase_manager.get_all_cases()
        logging.debug(f"Cases loaded: {cases}")
        if cases:
            for case_id, case_data in cases.items():
                if case_data:
                    row_position = self.caseTable.rowCount()
                    self.caseTable.insertRow(row_position)
                    self.caseTable.setItem(row_position, 0, QTableWidgetItem(case_id))
                    self.caseTable.setItem(row_position, 1, QTableWidgetItem(case_data.get('name', '')))
                    self.caseTable.setItem(row_position, 2, QTableWidgetItem(case_data.get('client_name', '')))
                    self.caseTable.setItem(row_position, 3, QTableWidgetItem(case_data.get('client', '')))
                    self.caseTable.setItem(row_position, 4, QTableWidgetItem(case_data.get('comment', '')))
                    self.caseTable.setItem(row_position, 5, QTableWidgetItem(case_data.get('date_created', '')))
        self.load_proforma_case_numbers()
        logging.info("Case table data loaded")

    def load_proforma_case_numbers(self):
        logging.info("Loading case numbers for proforma tab")
        self.proformaClientInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            case_numbers = [case_id for case_id in cases]
            self.proformaClientInput.addItems(case_numbers)
        logging.info("Case numbers for proforma tab loaded")

    def load_proforma_table_data(self):
        logging.info("Loading proforma table data")
        self.proformaTable.setRowCount(0)
        proformas = self.firebase_manager.get_all_proformas()
        logging.debug(f"Proformas loaded: {proformas}")
        if proformas:
            for proforma_id, proforma_data in proformas.items():
                row_position = self.proformaTable.rowCount()
                self.proformaTable.insertRow(row_position)
                self.proformaTable.setItem(row_position, 0, QTableWidgetItem(proforma_data.get('case_number', '')))
                self.proformaTable.setItem(row_position, 1, QTableWidgetItem(proforma_id))
                self.proformaTable.setItem(row_position, 2, QTableWidgetItem(proforma_data.get('name', '')))
                self.proformaTable.setItem(row_position, 3, QTableWidgetItem(proforma_data.get('client', '')))
                self.proformaTable.setItem(row_position, 4, QTableWidgetItem(proforma_data.get('comment', '')))
                self.proformaTable.setItem(row_position, 5, QTableWidgetItem(proforma_data.get('date_created', '')))

        # Load data into combo boxes
        self.proformaNameInput.clear()

        unique_proforma_names = set()

        for proforma_id, proforma_data in proformas.items():
            unique_proforma_names.add(proforma_data.get('name', ''))

        self.proformaNameInput.addItems(sorted(unique_proforma_names))
        logging.info("Proforma table data loaded")

    def load_client_table_data(self):
        logging.info("Loading client table data")
        self.clientTable.setRowCount(0)
        clients = self.firebase_manager.get_all_clients()
        logging.debug(f"Clients loaded: {clients}")
        if isinstance(clients, dict):
            for client_id, client_data in clients.items():
                row_position = self.clientTable.rowCount()
                self.clientTable.insertRow(row_position)
                self.clientTable.setItem(row_position, 0, QTableWidgetItem(client_id))
                self.clientTable.setItem(row_position, 1, QTableWidgetItem(client_data.get('name', '') if isinstance(client_data, dict) else client_data))
        elif isinstance(clients, list):
            for client_data in clients:
                if client_data:
                    row_position = self.clientTable.rowCount()
                    self.clientTable.insertRow(row_position)
                    self.clientTable.setItem(row_position, 0, QTableWidgetItem(client_data['id']))
                    self.clientTable.setItem(row_position, 1, QTableWidgetItem(client_data['name']))
        logging.info("Client table data loaded")

    def add_new_case(self):
        name = self.caseNameInput.currentText().strip()
        client_name = self.caseClientInput.currentText().strip()
        if not name or not client_name:
            QMessageBox.warning(self, "Внимание", "Имя дела и клиент не могут быть пустыми")
            return

        comment = ''
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

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
            self.load_client_table_data()
            QMessageBox.information(self, "Успех", f"Дело добавлено успешно с ID: {case_id}")
        except Exception as e:
            logging.error(f"Error adding new case: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении дела: {e}")

    def confirm_delete_case(self):
        selected_items = self.caseTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите дело для удаления")
            return

        row = selected_items[0].row()
        case_id = self.caseTable.item(row, 0).text()
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

    def confirm_delete_proforma(self):
        selected_items = self.proformaTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите проформу для удаления")
            return

        row = selected_items[0].row()
        proforma_id = self.proformaTable.item(row, 1).text()
        response = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить проформу с ID {proforma_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_proforma(proforma_id)
                self.load_proforma_table_data()
                QMessageBox.information(self, "Успех", "Проформа удалена успешно")
            except Exception as e:
                logging.error(f"Error deleting proforma: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении проформы: {e}")

    def confirm_delete_client(self):
        selected_items = self.clientTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите клиента для удаления")
            return

        row = selected_items[0].row()
        client_id = self.clientTable.item(row, 0).text()
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

    def add_new_proforma(self):
        name = self.proformaNameInput.currentText().strip()
        case_number = self.proformaClientInput.currentText().strip()
        comment = self.proformaCommentInput.text().strip()
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        if not name or not case_number:
            QMessageBox.warning(self, "Внимание", "Имя проформы и номер дела не могут быть пустыми")
            return

        try:
            new_proforma = {
                'name': name,
                'case_number': case_number,
                'comment': comment,
                'date_created': date_created
            }
            proforma_id = self.firebase_manager.add_proforma(new_proforma)
            self.load_proforma_table_data()
            QMessageBox.information(self, "Успех", f"Проформа добавлена успешно с ID: {proforma_id}")
        except Exception as e:
            logging.error(f"Error adding new proforma: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении проформы: {e}")

    def add_new_client(self):
        name = self.clientNameInput.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Имя клиента не может быть пустым")
            return

        try:
            client_id = self.firebase_manager.add_client(name)
            self.load_client_table_data()
            QMessageBox.information(self, "Успех", f"Клиент добавлен успешно с ID: {client_id}")
        except Exception as e:
            logging.error(f"Error adding client: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении клиента: {e}")

    def load_unique_names(self):
        logging.info("Loading unique names")
        self.caseNameInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            unique_names = set()
            for case_id, case_data in cases.items():
                unique_names.add(case_data.get('name', ''))
            self.caseNameInput.addItems(sorted(unique_names))
        logging.info("Unique names loaded")