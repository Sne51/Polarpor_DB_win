from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
import logging
from src.decorators import exception_handler  # Обновляем путь для импорта


class ClientsTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.main_window.addClientButton.clicked.connect(self.add_new_client)
        self.main_window.deleteClientButton.clicked.connect(self.confirm_delete_client)
        self.setup_client_table()

    @exception_handler
    def setup_client_table(self):
        headers = ["ID", "Имя клиента"]
        self.main_window.clientTable.setColumnCount(len(headers))
        self.main_window.clientTable.setHorizontalHeaderLabels(headers)
        self.main_window.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_client_table_data()

    @exception_handler
    def load_client_table_data(self):
        logging.info("Loading client table data")
        self.main_window.clientTable.setRowCount(0)
        clients = self.firebase_manager.get_all_clients()
        logging.debug(f"Clients loaded: {clients}")
        if clients:
            for client_id, client_data in clients.items():
                row_position = self.main_window.clientTable.rowCount()
                self.main_window.clientTable.insertRow(row_position)
                self.main_window.clientTable.setItem(row_position, 0, QTableWidgetItem(client_id))
                self.main_window.clientTable.setItem(row_position, 1, QTableWidgetItem(client_data.get('name', '')))
        logging.info("Client table data loaded")

    @exception_handler
    def add_new_client(self, event=None):
        client_name = self.main_window.clientNameInput.text().strip()

        if not client_name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя клиента не может быть пустым")
            return

        # Проверка на дублирование клиента
        existing_client_id = self.firebase_manager.check_and_add_client(client_name, check_only=True)
        if existing_client_id:
            QMessageBox.warning(self.main_window, "Внимание", f"Клиент с таким именем уже существует. Его ID: {existing_client_id}")
            return

        try:
            new_client_id = self.firebase_manager.add_client(client_name)
            logging.debug(f"New client ID: {new_client_id}")
            self.load_client_table_data()
            QMessageBox.information(self.main_window, "Успех", f"Клиент добавлен успешно с ID: {new_client_id}")
        except Exception as e:
            logging.error(f"Error adding new client: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении клиента: {e}")

    @exception_handler
    def confirm_delete_client(self, event=None):
        selected_items = self.main_window.clientTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите клиента для удаления")
            return

        row = selected_items[0].row()
        client_id = self.main_window.clientTable.item(row, 0).text()
        response = QMessageBox.question(self.main_window, "Подтверждение", f"Вы уверены, что хотите удалить клиента с ID {client_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_client(client_id)
                self.load_client_table_data()
                QMessageBox.information(self.main_window, "Успех", "Клиент удален успешно")
            except Exception as e:
                logging.error(f"Error deleting client: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении клиента: {e}")
