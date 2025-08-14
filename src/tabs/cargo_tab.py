# /Users/sk/Documents/EDU_Python/Polarpor_DB_win/src/tabs/cargo_tab.py
import logging
from typing import Dict, Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QComboBox,
)

from src.decorators import exception_handler


class CargoTab(QWidget):
    STREAM_NAME = "cargo_stream"

    TK_OPTIONS = ["DHL", "TNT/FedEx", "UPS", "Bring/Posten", "Dachser", "Schenker", "DPD"]
    STATUS_OPTIONS = ["Заказано", "Поехало", "Приехало", "Вопрос"]

    STATUS_COLORS = {
        "Заказано": QColor(255, 255, 150),   # жёлтый
        "Поехало": QColor(200, 150, 255),    # фиолетовый
        "Приехало": QColor(150, 255, 150),   # зелёный
        "Вопрос": QColor(255, 150, 150),     # красный
    }

    COL_ID = 0
    COL_ORDER = 1
    COL_CUSTOMER = 2
    COL_SUPPLIER = 3
    COL_MANAGER = 4
    COL_DEADLINE = 5
    COL_TK = 6
    COL_TRACKING = 7
    COL_STATUS = 8

    def __init__(self, main_window, firebase_manager):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        self.cargoTable = self.main_window.cargoTable
        self.addCargoButton = getattr(self.main_window, "addCargoButton", None)
        self.deleteCargoButton = getattr(self.main_window, "deleteCargoButton", None)

        self.cargoCaseNumberInput = getattr(self.main_window, "cargoCaseNumberInput", None)
        self.cargoSupplierInput = getattr(self.main_window, "cargoSupplierInput", None)

        self._mute = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        headers = [
            "ID", "Номер дела", "Клиент", "Поставщик",
            "Менеджер", "Дедлайн", "ТК", "Tracking", "Статус"
        ]
        self.cargoTable.setColumnCount(len(headers))
        self.cargoTable.setHorizontalHeaderLabels(headers)
        self.cargoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cargoTable.itemChanged.connect(self._on_item_changed)

    def _connect_signals(self):
        if self.addCargoButton:
            self.addCargoButton.clicked.connect(self.add_cargo)
        if self.deleteCargoButton:
            self.deleteCargoButton.clicked.connect(self.delete_cargo)

    def activate(self):
        try:
            self.load_cargo_table_data()
            self._load_case_numbers_into_top_combobox()
            self._load_suppliers_into_top_combobox()
        except Exception as e:
            logging.debug(f"[CargoTab] activate preload error: {e}")
        self.firebase_manager.on("/cargo", self._on_stream_event, name=self.STREAM_NAME)

    def deactivate(self):
        self.firebase_manager.off(self.STREAM_NAME)

    @exception_handler
    def load_cargo_table_data(self):
        data = self.firebase_manager.get_all_cargo()
        self._mute = True
        try:
            self.cargoTable.setRowCount(0)
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        self._upsert_row(str(idx), item)
            elif isinstance(data, dict):
                for cid, item in data.items():
                    if isinstance(item, dict):
                        self._upsert_row(str(cid), item)
        finally:
            self._mute = False

    @exception_handler
    def _load_case_numbers_into_top_combobox(self):
        if not self.cargoCaseNumberInput:
            return
        self.cargoCaseNumberInput.clear()
        cases = self.firebase_manager.get_all_cases() or {}
        ids = [cid for cid in cases.keys() if isinstance(cid, str) and cid.isdigit()]
        ids.sort(key=lambda x: int(x))
        self.cargoCaseNumberInput.addItems(ids)

    @exception_handler
    def _load_suppliers_into_top_combobox(self):
        if not self.cargoSupplierInput:
            return
        self.cargoSupplierInput.clear()
        suppliers = self.firebase_manager.get_all_suppliers()
        names = []
        if isinstance(suppliers, dict):
            for v in suppliers.values():
                if isinstance(v, dict):
                    nm = (v.get("name") or "").strip()
                    if nm:
                        names.append(nm)
        elif isinstance(suppliers, list):
            for v in suppliers:
                if isinstance(v, dict):
                    nm = (v.get("name") or "").strip()
                    if nm:
                        names.append(nm)
        self.cargoSupplierInput.addItems(sorted(set(names)))

    @exception_handler
    def add_cargo(self, checked=False):
        order = (self.cargoCaseNumberInput.currentText() if self.cargoCaseNumberInput else "").strip()
        supplier = (self.cargoSupplierInput.currentText() if self.cargoSupplierInput else "").strip()
        new_data = {
            "order": order,
            "customer": "",
            "supplier": supplier,
            "manager": "",
            "deadline": "",
            "tk": self.TK_OPTIONS[0],
            "tracking": "",
            "status": self.STATUS_OPTIONS[0],
        }
        new_id = self.firebase_manager.add_cargo(new_data)
        self._upsert_row(new_id, new_data)

    @exception_handler
    def delete_cargo(self, checked=False):
        row = self.cargoTable.currentRow()
        if row < 0:
            return
        id_item = self.cargoTable.item(row, self.COL_ID)
        if not id_item:
            return
        cid = id_item.text().strip()
        if not cid:
            return
        self.firebase_manager.delete_cargo(cid)
        self.cargoTable.removeRow(row)

    def _on_stream_event(self, payload: Dict[str, Any]):
        try:
            path = payload.get("path")
            data = payload.get("data")
            self._mute = True
            try:
                if path == "/" and isinstance(data, dict):
                    self.cargoTable.setRowCount(0)
                    for cid, c in data.items():
                        if isinstance(c, dict):
                            self._upsert_row(str(cid), c)
                    return
                if isinstance(path, str) and path.startswith("/") and len(path) > 1:
                    cid = path[1:]
                    if data is None:
                        self._remove_row_by_id(cid)
                    elif isinstance(data, dict):
                        self._upsert_row(cid, data)
            finally:
                self._mute = False
        except Exception as e:
            logging.debug(f"[CargoTab] stream event error: {e}")

    def _on_item_changed(self, item: QTableWidgetItem):
        if self._mute:
            return
        row = item.row()
        col = item.column()
        id_item = self.cargoTable.item(row, self.COL_ID)
        if not id_item:
            return
        cid = id_item.text().strip()
        if not cid:
            return
        key_map = {
            self.COL_ORDER: "order",
            self.COL_CUSTOMER: "customer",
            self.COL_SUPPLIER: "supplier",
            self.COL_MANAGER: "manager",
            self.COL_DEADLINE: "deadline",
            self.COL_TRACKING: "tracking",
        }
        key = key_map.get(col)
        if not key:
            return
        value = item.text()
        self.firebase_manager.cargo_ref.child(cid).update({key: value})

    def _find_row_by_id(self, cid: str) -> int:
        for r in range(self.cargoTable.rowCount()):
            it = self.cargoTable.item(r, self.COL_ID)
            if it and it.text() == cid:
                return r
        return -1

    def _remove_row_by_id(self, cid: str):
        r = self._find_row_by_id(cid)
        if r >= 0:
            self.cargoTable.removeRow(r)

    def _upsert_row(self, cid: str, c: Dict[str, Any]):
        row = self._find_row_by_id(cid)
        if row == -1:
            row = self.cargoTable.rowCount()
            self.cargoTable.insertRow(row)

        def _set(col: int, val: str):
            it = QTableWidgetItem(val if val is not None else "")
            if col == self.COL_ID:
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.cargoTable.setItem(row, col, it)

        _set(self.COL_ID, str(cid))
        _set(self.COL_ORDER, str(c.get("order", "")))
        _set(self.COL_CUSTOMER, str(c.get("customer", "")))
        _set(self.COL_SUPPLIER, str(c.get("supplier", "")))
        _set(self.COL_MANAGER, str(c.get("manager", "")))
        _set(self.COL_DEADLINE, str(c.get("deadline", "")))
        _set(self.COL_TRACKING, str(c.get("tracking", "")))

        tk_combo = self._make_combo(self.TK_OPTIONS, (c.get("tk") or "").strip(), cid, "tk")
        self.cargoTable.setCellWidget(row, self.COL_TK, tk_combo)

        status_combo = self._make_combo(self.STATUS_OPTIONS, (c.get("status") or "").strip(), cid, "status")
        self.cargoTable.setCellWidget(row, self.COL_STATUS, status_combo)

        self._color_row_by_status(row, c.get("status", ""))

    def _make_combo(self, options, current_value: str, cargo_id: str, key: str) -> QComboBox:
        combo = QComboBox(self.cargoTable)
        combo.addItems(options)
        idx = next((i for i, v in enumerate(options) if v == current_value), 0)
        combo.setCurrentIndex(idx)
        combo.setProperty("cargo_id", cargo_id)
        combo.setProperty("cargo_key", key)

        def on_changed(_index: int):
            if self._mute:
                return
            cid = combo.property("cargo_id")
            k = combo.property("cargo_key")
            val = combo.currentText()
            self.firebase_manager.cargo_ref.child(str(cid)).update({str(k): val})
            if k == "status":
                row = self._find_row_by_id(cid)
                if row >= 0:
                    self._color_row_by_status(row, val)

        combo.currentIndexChanged.connect(on_changed)
        return combo

    def _color_row_by_status(self, row: int, status: str):
        color = self.STATUS_COLORS.get(status)
        if not color:
            return
        for col in range(self.cargoTable.columnCount()):
            item = self.cargoTable.item(row, col)
            if not item:
                item = QTableWidgetItem("")
                self.cargoTable.setItem(row, col, item)
            item.setBackground(color)