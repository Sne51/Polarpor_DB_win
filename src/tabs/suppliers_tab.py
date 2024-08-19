from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QHeaderView
import logging
from src.decorators import exception_handler

class SuppliersTab:
    def __init__(self, main_window: QMainWindow, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager
        self.main_window.addSupplierButton.clicked.connect(self.add_new_supplier)
        self.main_window.deleteSupplierButton.clicked.connect(self.confirm_delete_supplier)
        self.setup_supplier_table()

    @exception_handler
    def setup_supplier_table(self):
        headers = ["ID", "Имя"]
        self.main_window.supplierTable.setColumnCount(len(headers))
        self.main_window.supplierTable.setHorizontalHeaderLabels(headers)
        self.main_window.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_supplier_table_data()

    @exception_handler
    def load_supplier_table_data(self):
        logging.info("Loading supplier table data")
        self.main_window.supplierTable.setRowCount(0)
        suppliers = self.firebase_manager.get_all_suppliers()
        logging.debug(f"Suppliers loaded: {suppliers}")
        
        if isinstance(suppliers, dict):
            for supplier_id, supplier_data in suppliers.items():
                if supplier_data is not None:  # Игнорируем пустые записи
                    self.add_supplier_row(supplier_id, supplier_data)
        elif isinstance(suppliers, list):
            for supplier_id, supplier_data in enumerate(suppliers, start=1):
                if supplier_data is not None:  # Игнорируем пустые записи
                    self.add_supplier_row(str(supplier_id), supplier_data)
        
        logging.info("Supplier table data loaded")

    def add_supplier_row(self, supplier_id, supplier_data):
        row_position = self.main_window.supplierTable.rowCount()
        self.main_window.supplierTable.insertRow(row_position)
        self.main_window.supplierTable.setItem(row_position, 0, QTableWidgetItem(supplier_id))
        self.main_window.supplierTable.setItem(row_position, 1, QTableWidgetItem(supplier_data.get('name', '')))

    @exception_handler
    def add_new_supplier(self, event=None):  # Добавлен параметр event
        name = self.main_window.supplierNameInput.text().strip()

        if not name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя поставщика не может быть пустым")
            return

        suppliers = self.firebase_manager.get_all_suppliers()
        if isinstance(suppliers, dict):
            for supplier_id, supplier_data in suppliers.items():
                if supplier_data['name'].lower() == name.lower():
                    QMessageBox.warning(self.main_window, "Внимание", f"Поставщик с таким именем уже существует с ID {supplier_id}")
                    return
        elif isinstance(suppliers, list):
            for supplier_data in suppliers:
                if supplier_data and supplier_data['name'].lower() == name.lower():
                    QMessageBox.warning(self.main_window, "Внимание", f"Поставщик с таким именем уже существует")
                    return

        new_supplier = {'name': name}
        supplier_id = self.firebase_manager.add_supplier(new_supplier)
        self.load_supplier_table_data()
        QMessageBox.information(self.main_window, "Успех", f"Поставщик добавлен успешно с ID: {supplier_id}")

    @exception_handler
    def confirm_delete_supplier(self):
        selected_items = self.main_window.supplierTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите поставщика для удаления")
            return

        row = selected_items[0].row()
        supplier_id = self.main_window.supplierTable.item(row, 0).text()
        response = QMessageBox.question(self.main_window, "Подтверждение", f"Вы уверены, что хотите удалить поставщика с ID {supplier_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            try:
                self.firebase_manager.delete_supplier(supplier_id)
                self.load_supplier_table_data()
                QMessageBox.information(self.main_window, "Успех", "Поставщик удален успешно")
            except Exception as e:
                logging.error(f"Error deleting supplier: {e}")
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при удалении поставщика: {e}")
