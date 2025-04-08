import logging
from PyQt5.QtWidgets import (QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView, 
                             QTableWidget, QComboBox, QLineEdit, QPushButton)
                             
class SuppliersTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Поиск необходимых виджетов в главном окне
        self.supplierTable = self.main_window.findChild(QTableWidget, 'supplierTable')
        self.addSupplierButton = self.main_window.findChild(QPushButton, 'addSupplierButton')
        self.deleteSupplierButton = self.main_window.findChild(QPushButton, 'deleteSupplierButton')
        self.supplierNameInput = self.main_window.findChild(QLineEdit, 'supplierNameInput')

        missing_widgets = []
        if self.supplierTable is None:
            missing_widgets.append('supplierTable')
        if self.addSupplierButton is None:
            missing_widgets.append('addSupplierButton')
        if self.deleteSupplierButton is None:
            missing_widgets.append('deleteSupplierButton')
        if self.supplierNameInput is None:
            missing_widgets.append('supplierNameInput')
        if missing_widgets:
            msg = f"Отсутствуют следующие виджеты в SuppliersTab: {', '.join(missing_widgets)}"
            logging.error(msg)
            QMessageBox.critical(self.main_window, "Ошибка", msg)
            return

        # Подключаем обработчики событий к кнопкам
        self.addSupplierButton.clicked.connect(self.add_supplier)
        self.deleteSupplierButton.clicked.connect(self.confirm_delete_supplier)

        self.setup_supplier_table()

    def setup_supplier_table(self):
        headers = ["ID", "Имя поставщика"]
        self.supplierTable.setColumnCount(len(headers))
        self.supplierTable.setHorizontalHeaderLabels(headers)
        self.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_supplier_table_data()

    def load_supplier_table_data(self):
        logging.info("Loading supplier table data")
        self.supplierTable.setRowCount(0)
        suppliers = self.firebase_manager.get_all_suppliers() or {}
        logging.debug(f"Suppliers loaded: {suppliers}")
        if suppliers:
            if isinstance(suppliers, dict):
                for supplier_id, supplier_data in suppliers.items():
                    if supplier_data and isinstance(supplier_data, dict):
                        row_position = self.supplierTable.rowCount()
                        self.supplierTable.insertRow(row_position)
                        supplier_name = supplier_data.get('name', '')
                        self.supplierTable.setItem(row_position, 0, QTableWidgetItem(supplier_id))
                        self.supplierTable.setItem(row_position, 1, QTableWidgetItem(supplier_name))
            elif isinstance(suppliers, list):
                for index, supplier_data in enumerate(suppliers):
                    if supplier_data and isinstance(supplier_data, dict):
                        row_position = self.supplierTable.rowCount()
                        self.supplierTable.insertRow(row_position)
                        supplier_name = supplier_data.get('name', '')
                        self.supplierTable.setItem(row_position, 0, QTableWidgetItem(str(index + 1)))
                        self.supplierTable.setItem(row_position, 1, QTableWidgetItem(supplier_name))
        logging.info("Supplier table data loaded")

    def add_supplier(self):
        supplier_name = self.supplierNameInput.text().strip()
        if not supplier_name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя поставщика не может быть пустым")
            return
        try:
            # Проверка, существует ли уже поставщик с таким именем
            existing_suppliers = []
            for row in range(self.supplierTable.rowCount()):
                item = self.supplierTable.item(row, 1)
                if item:
                    existing_suppliers.append(item.text().lower())
            if supplier_name.lower() in existing_suppliers:
                QMessageBox.warning(self.main_window, "Ошибка", "Такой поставщик уже существует")
                return
            new_supplier = {'name': supplier_name}
            self.firebase_manager.add_supplier(new_supplier)
            self.load_supplier_table_data()
            QMessageBox.information(self.main_window, "Успех", f"Поставщик {supplier_name} добавлен успешно")
        except Exception as e:
            logging.error(f"Error adding supplier: {e}")
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при добавлении поставщика: {e}")

    def confirm_delete_supplier(self):
        selected_items = self.supplierTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите поставщика для удаления")
            return
        row = selected_items[0].row()
        supplier_id_item = self.supplierTable.item(row, 0)
        supplier_name_item = self.supplierTable.item(row, 1)
        if supplier_id_item is None or supplier_name_item is None:
            QMessageBox.warning(self.main_window, "Ошибка", "Невозможно удалить поставщика. Некорректные данные.")
            return
        supplier_id = supplier_id_item.text()
        supplier_name = supplier_name_item.text()
        response = QMessageBox.question(self.main_window, "Подтверждение удаления",
                                        f"Вы уверены, что хотите удалить поставщика {supplier_name} с ID {supplier_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_supplier(supplier_id)
                self.load_supplier_table_data()
                QMessageBox.information(self.main_window, "Успех", "Поставщик удален успешно")
            except Exception as e:
                logging.error(f"Error deleting supplier: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении поставщика: {e}")