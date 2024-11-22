from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import QDateTime
import logging
from src.search_functions import search_in_case_table  # Обновляем путь для импорта
from src.decorators import exception_handler  # Обновляем путь для импорта

class CaseNumbersTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.main_window.addCaseButton.clicked.connect(self.add_new_case)
        self.main_window.deleteCaseButton.clicked.connect(self.confirm_delete_case)
        self.setup_case_table()

    @exception_handler
    def setup_case_table(self):
        headers = ["ID", "Имя", "Клиент", "Клиент ID", "Комментарий", "Дата создания"]
        self.main_window.caseTable.setColumnCount(len(headers))
        self.main_window.caseTable.setHorizontalHeaderLabels(headers)
        self.main_window.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_case_table_data()
        self.load_unique_names()
        self.load_clients_into_combobox()

    @exception_handler
    def load_case_table_data(self):
        logging.info("Loading case table data")
        self.main_window.caseTable.setRowCount(0)
        cases = self.firebase_manager.get_all_cases()
        logging.debug(f"Cases loaded: {cases}")
        
        if cases:
            for case_id, case_data in cases.items():
                if not case_id.isdigit():
                    logging.debug(f"Skipping non-case item: {case_id}")
                    continue
                
                if case_data:
                    row_position = self.main_window.caseTable.rowCount()
                    self.main_window.caseTable.insertRow(row_position)
                    self.main_window.caseTable.setItem(row_position, 0, QTableWidgetItem(case_id))
                    self.main_window.caseTable.setItem(row_position, 1, QTableWidgetItem(case_data.get('name', '')))
                    self.main_window.caseTable.setItem(row_position, 2, QTableWidgetItem(case_data.get('client_name', '')))
                    self.main_window.caseTable.setItem(row_position, 3, QTableWidgetItem(case_data.get('client', '')))
                    self.main_window.caseTable.setItem(row_position, 4, QTableWidgetItem(case_data.get('comment', '')))
                    self.main_window.caseTable.setItem(row_position, 5, QTableWidgetItem(case_data.get('date_created', '')))
        logging.info("Case table data loaded")

    def load_unique_names(self):
        logging.info("Loading unique names")
        self.main_window.caseNameInput.clear()
        
        # Получаем список менеджеров из FirebaseManager
        try:
            managers = self.firebase_manager.get_all_managers()
            if managers:
                self.main_window.caseNameInput.addItems(sorted(managers))
            logging.info("Unique names loaded")
        except Exception as e:
            logging.error(f"Error loading unique names: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", "Не удалось загрузить список менеджеров.")

    def load_clients_into_combobox(self):
        logging.info("Loading clients into combobox")
        self.main_window.clientInput.clear()
        clients = self.firebase_manager.get_all_clients()
        if clients:
            for client_id, client_data in clients.items():
                client_name = client_data.get('name', '') if isinstance(client_data, dict) else client_data
                self.main_window.clientInput.addItem(client_name)
        logging.info("Clients loaded into combobox")

    def add_new_case(self):
        manager_name = self.main_window.caseNameInput.currentText().strip()
        client_name = self.main_window.clientInput.currentText().strip()

        if not manager_name or not client_name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя менеджера и клиента не могут быть пустыми")
            return

        comment = ''
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        try:
            client_id = self.firebase_manager.check_and_add_client(client_name)

            if manager_name not in [self.main_window.caseNameInput.itemText(i) for i in range(self.main_window.caseNameInput.count())]:
                self.main_window.caseNameInput.addItem(manager_name)

            new_case = {
                'name': manager_name,
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
            self.load_clients_into_combobox()
            QMessageBox.information(self.main_window, "Успех", f"Дело добавлено успешно с ID: {case_id}")
        except Exception as e:
            logging.error(f"Error adding new case: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении дела: {e}")

    def confirm_delete_case(self):
        selected_items = self.main_window.caseTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите дело для удаления")
            return

        row = selected_items[0].row()
        case_id = self.main_window.caseTable.item(row, 0).text()
        response = QMessageBox.question(self.main_window, "Подтверждение", f"Вы уверены, что хотите удалить дело с ID {case_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_case(case_id)
                self.load_case_table_data()
                self.load_unique_names()
                self.load_clients_into_combobox()
                QMessageBox.information(self.main_window, "Успех", "Дело удалено успешно")
            except Exception as e:
                logging.error(f"Error deleting case: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении дела: {e}")

    def filter_case_names(self, text):
        self.main_window.caseNameInput.clear()
        cases = self.firebase_manager.get_all_cases()
        if cases:
            unique_names = set()
            for case_id, case_data in cases.items():
                name = case_data.get('name', '')
                if isinstance(name, str) and text.lower() in name.lower():
                    unique_names.add(name)
            self.main_window.caseNameInput.addItems(sorted(unique_names))
            self.main_window.caseNameInput.setCurrentText(text)
