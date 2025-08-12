import logging
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QMessageBox, QHeaderView

class SuppliersTab(QWidget):
    def __init__(self, main_window, firebase_manager):
        super().__init__()
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Прямое обращение к атрибутам main_window (как в CaseNumbersTab)
        self.supplierTable: QTableWidget = self.main_window.supplierTable
        self.supplierNameInput: QLineEdit = self.main_window.supplierNameInput
        self.addSupplierButton: QPushButton = self.main_window.addSupplierButton
        self.deleteSupplierButton: QPushButton = self.main_window.deleteSupplierButton

        if not self.supplierTable:
            logging.error("supplierTable не найден в UI. Проверь objectName в main.ui.")
        else:
            self.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        if self.addSupplierButton:
            self.addSupplierButton.clicked.connect(self.add_supplier)
        if self.deleteSupplierButton:
            self.deleteSupplierButton.clicked.connect(self.delete_supplier)

        self.load_supplier_table_data()

    def load_supplier_table_data(self):
        if not self.supplierTable:
            return
        self.supplierTable.setRowCount(0)
        try:
            suppliers = self.firebase_manager.get_all_suppliers()
            logging.debug(f"Suppliers loaded: {suppliers}")

            if isinstance(suppliers, dict):
                for sid, sdata in suppliers.items():
                    if not isinstance(sdata, dict) or not sdata.get("name"):
                        continue
                    row = self.supplierTable.rowCount()
                    self.supplierTable.insertRow(row)
                    self.supplierTable.setItem(row, 0, QTableWidgetItem(str(sid)))
                    self.supplierTable.setItem(row, 1, QTableWidgetItem(sdata["name"]))
            elif isinstance(suppliers, list):
                for idx, sdata in enumerate(suppliers):
                    if not isinstance(sdata, dict) or not sdata.get("name"):
                        continue
                    row = self.supplierTable.rowCount()
                    self.supplierTable.insertRow(row)
                    self.supplierTable.setItem(row, 0, QTableWidgetItem(str(idx)))
                    self.supplierTable.setItem(row, 1, QTableWidgetItem(sdata["name"]))
        except Exception as e:
            logging.error(f"Ошибка загрузки поставщиков: {e}")

    def add_supplier(self, checked: bool = False):
        if not self.supplierNameInput:
            return
        name = self.supplierNameInput.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя поставщика")
            return
        try:
            self.firebase_manager.add_supplier({"name": name})
            self.supplierNameInput.clear()
            self.load_supplier_table_data()
        except Exception as e:
            logging.error(f"Ошибка при добавлении поставщика: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def delete_supplier(self, checked: bool = False):
        if not self.supplierTable:
            return
        row = self.supplierTable.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите поставщика для удаления")
            return
        id_item = self.supplierTable.item(row, 0)
        if not id_item:
            QMessageBox.warning(self, "Ошибка", "Некорректный ID поставщика")
            return
        supplier_id = id_item.text().strip()
        try:
            self.firebase_manager.delete_supplier(supplier_id)
            self.load_supplier_table_data()
        except Exception as e:
            logging.error(f"Ошибка при удалении поставщика: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))