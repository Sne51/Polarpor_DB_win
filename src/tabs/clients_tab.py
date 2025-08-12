import logging
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView, QTableWidget
from src.decorators import exception_handler


class ClientsTab:
    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Ищем таблицу
        self.clientTable = self.main_window.findChild(QTableWidget, 'clientTable')
        if self.clientTable is None:
            logging.error("Виджет 'clientTable' не найден в интерфейсе!")
            QMessageBox.critical(self.main_window, "Ошибка", "Виджет 'clientTable' не найден в main.ui")
            return

        # Кнопки
        self.main_window.addClientButton.clicked.connect(self.add_new_client)
        self.main_window.deleteClientButton.clicked.connect(self.confirm_delete_client)

        self.setup_client_table()

    @exception_handler
    def setup_client_table(self):
        headers = ["ID", "Имя клиента"]
        self.clientTable.setColumnCount(len(headers))
        self.clientTable.setHorizontalHeaderLabels(headers)
        self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_client_table_data()

    @exception_handler
    def load_client_table_data(self):
        logging.info("Loading client table data")
        self.clientTable.setRowCount(0)
        clients = self.firebase_manager.get_all_clients()
        logging.debug(f"Clients loaded: {clients}")
        if clients:
            for client_id, client_data in clients.items():
                if not isinstance(client_data, dict):
                    logging.warning(f"Некорректная запись клиента: {client_id} -> {client_data}")
                    continue
                row_position = self.clientTable.rowCount()
                self.clientTable.insertRow(row_position)
                self.clientTable.setItem(row_position, 0, QTableWidgetItem(str(client_id)))
                self.clientTable.setItem(row_position, 1, QTableWidgetItem(client_data.get('name', '')))
        logging.info("Client table data loaded")

    @exception_handler
    def add_new_client(self, checked: bool = False):
        name = self.main_window.clientNameInput.text().strip()
        if not name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя клиента не может быть пустым")
            return

        # Проверяем, есть ли уже клиент с таким именем
        existing_id = self.firebase_manager.check_and_add_client(client_name=name, check_only=True)
        if existing_id:
            QMessageBox.warning(self.main_window, "Внимание",
                                f"Клиент с таким именем уже существует (ID: {existing_id}).")
            return

        try:
            new_client_id = self.firebase_manager.add_client(name)
            logging.debug(f"New client ID: {new_client_id}")
            self.load_client_table_data()
            QMessageBox.information(self.main_window, "Успех", f"Клиент добавлен. ID: {new_client_id}")
        except Exception as e:
            logging.error(f"Error adding new client: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении клиента: {e}")

    @exception_handler
    def confirm_delete_client(self, checked: bool = False):
        selected_items = self.clientTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите клиента для удаления")
            return

        row = selected_items[0].row()
        id_item = self.clientTable.item(row, 0)
        if id_item is None:
            QMessageBox.warning(self.main_window, "Ошибка", "Не удалось определить ID клиента.")
            return

        client_id = id_item.text()
        resp = QMessageBox.question(
            self.main_window,
            "Подтверждение удаления",
            f"Удалить клиента с ID {client_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_client(client_id)
                self.load_client_table_data()
                QMessageBox.information(self.main_window, "Успех", "Клиент удалён")
            except Exception as e:
                logging.error(f"Error deleting client: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении клиента: {e}")