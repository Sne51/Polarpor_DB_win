# src/tabs/cargo_tab.py
import logging
from typing import Dict, Any, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
import sip

from src.decorators import exception_handler


class CargoTab(QWidget):
    """
    Вкладка «Грузы»
    - ленивое наполнение при activate()
    - realtime через FirebaseManager.on('/cargo', ...)
    - комбо «Номер дела» и «Поставщик» ищутся и привязываются при каждом activate()
    """

    STREAM_NAME = "cargo_stream"

    TK_OPTIONS = ["DHL", "TNT/FedEx", "UPS", "Bring/Posten", "Dachser", "Schenker", "DPD"]
    STATUS_OPTIONS = ["Заказано", "Поехало", "Приехало", "Вопрос"]

    STATUS_COLORS = {
        "Заказано": QColor(255, 255, 150),
        "Поехало": QColor(200, 150, 255),
        "Приехало": QColor(150, 255, 150),
        "Вопрос": QColor(255, 150, 150),
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
    COL_COMMENT = 9  # <-- новый последний столбец

    def __init__(self, main_window, firebase_manager, *, cargo_case_combo=None, cargo_supplier_combo=None):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Таблица и кнопки
        self.cargoTable = self.main_window.cargoTable
        self.addCargoButton = getattr(self.main_window, "addCargoButton", None)
        self.deleteCargoButton = getattr(self.main_window, "deleteCargoButton", None)

        # Ссылки могут быть None на старте — это ок: мы их пересвяжем в activate()
        self.cargoCaseNumberInput: QComboBox = cargo_case_combo or getattr(self.main_window, "cargoCaseNumberInput", None)
        self.cargoSupplierInput: QComboBox   = cargo_supplier_combo or getattr(self.main_window, "cargoSupplierInput", None)

        self._mute = False

        self._setup_ui()
        self._connect_signals()

    # ---------- service ----------
    def _rehook_combos(self):
        """Пере‑находим комбобоксы каждый раз (после загрузки UI/переключения вкладок)."""
        def _strict_find(name: str) -> QComboBox:
            w = self.main_window.findChild(QComboBox, name)
            if w:
                return w
            # fallback: пробегаемся по всем QComboBox в дереве
            for cb in self.main_window.findChildren(QComboBox):
                if (cb.objectName() or "").strip() == name:
                    return cb
            return None

        # если ссылок нет/мертвы — пересвязываем
        if (
            self.cargoCaseNumberInput is None
            or not isinstance(self.cargoCaseNumberInput, QComboBox)
            or sip.isdeleted(self.cargoCaseNumberInput)
        ):
            self.cargoCaseNumberInput = _strict_find("cargoCaseNumberInput")
        if (
            self.cargoSupplierInput is None
            or not isinstance(self.cargoSupplierInput, QComboBox)
            or sip.isdeleted(self.cargoSupplierInput)
        ):
            self.cargoSupplierInput = _strict_find("cargoSupplierInput")

        # диагностика: покажем все имена комбо, какие реально есть
        try:
            names = [cb.objectName() for cb in self.main_window.findChildren(QComboBox)]
            logging.debug(f"[CargoTab] QComboBox children: {names}")
        except Exception:
            pass

        logging.debug(
            f"[CargoTab] comboboxes present (after rehook): "
            f"case_is_none={self.cargoCaseNumberInput is None}, "
            f"supplier_is_none={self.cargoSupplierInput is None}"
        )

    # ---------------- UI ----------------
    def _setup_ui(self):
        headers = [
            "ID", "Номер дела", "Клиент", "Поставщик",
            "Менеджер", "Дедлайн", "ТК", "Tracking", "Статус", "Комментарий"
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

    # ---------------- Lifecycle ----------------
    def activate(self):
        """Ленивая подгрузка + включаем realtime-подписку."""
        # 1) гарантируем живые ссылки на комбо
        self._rehook_combos()

        try:
            # 2) наполняем таблицу и комбо
            self.load_cargo_table_data()
            self._load_case_numbers_into_top_combobox()
            self._load_suppliers_into_top_combobox()
            logging.debug("[CargoTab] activate() preloaded table + combos")
        except Exception as e:
            logging.debug(f"[CargoTab] activate preload error: {e}")

        # 3) realtime подписка (без несуществующего аргумента name=)
        try:
            self.firebase_manager.on("/cargo", self._on_stream_event)
        except TypeError:
            # совместимость со старой реализацией
            self.firebase_manager.on("/cargo", self._on_stream_event)

    def deactivate(self):
        try:
            self.firebase_manager.off("/cargo")
        except Exception:
            pass

    # ---------------- Helpers (cases) ----------------
    def _build_case_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает словарь по ID дела -> данные дела.
        Поддерживает как dict, так и list из Firebase.
        """
        cases = self.firebase_manager.get_all_cases()
        case_map: Dict[str, Dict[str, Any]] = {}

        if isinstance(cases, dict):
            for k, v in cases.items():
                if isinstance(v, dict) and str(k).isdigit():
                    case_map[str(k)] = v
        elif isinstance(cases, list):
            for v in cases:
                if isinstance(v, dict):
                    cid = (
                        v.get("id")
                        or v.get("case_number")
                        or v.get("number")
                        or v.get("case")
                    )
                    if cid is not None:
                        case_map[str(cid).strip()] = v

        logging.debug(f"[CargoTab] case_map built: {len(case_map)} entries")
        return case_map

    @staticmethod
    def _extract_customer_manager(case: Dict[str, Any]) -> Tuple[str, str]:
        """
        Извлекает имя клиента и менеджера из записи дела.
        Поля из ваших логов: client_name, client, manager, name.
        """
        customer = (
            (case.get("client_name") or "").strip()
            or str(case.get("client") or "").strip()
        )
        manager = (
            (case.get("manager") or "").strip()
            or (case.get("name") or "").strip()
        )
        return customer, manager

    # ---------------- Loaders ----------------
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
        combo = self.cargoCaseNumberInput
        if combo is None or sip.isdeleted(combo):
            logging.error("[CargoTab] combo 'cargoCaseNumberInput' not found")
            return

        combo.blockSignals(True)
        combo.clear()

        cases = self.firebase_manager.get_all_cases()
        logging.debug(f"[CargoTab] get_all_cases -> type={type(cases).__name__}, value_sample={str(cases)[:200]}")

        ids = []
        if isinstance(cases, dict):
            # только ключи-цифры (как в текущих данных)
            for k in cases.keys():
                k = str(k).strip()
                if k and k.isdigit():
                    ids.append(k)
        elif isinstance(cases, list):
            for item in cases:
                if isinstance(item, dict):
                    cid = item.get("id") or item.get("case_number") or item.get("number") or item.get("case")
                    if cid is not None:
                        ids.append(str(cid).strip())

        ids = sorted({x for x in ids if x})
        if ids and all(x.isdigit() for x in ids):
            ids.sort(key=lambda x: int(x))

        combo.addItems(ids)
        combo.blockSignals(False)
        logging.info(f"[CargoTab] case combobox filled: {len(ids)} items")

    @exception_handler
    def _load_suppliers_into_top_combobox(self):
        combo = self.cargoSupplierInput
        if combo is None or sip.isdeleted(combo):
            logging.error("[CargoTab] combo 'cargoSupplierInput' not found")
            return

        combo.blockSignals(True)
        combo.clear()

        suppliers = self.firebase_manager.get_all_suppliers()
        logging.debug(f"[CargoTab] get_all_suppliers -> type={type(suppliers).__name__}, value_sample={str(suppliers)[:200]}")

        names = []
        if isinstance(suppliers, dict):
            for v in suppliers.values():
                if isinstance(v, dict):
                    nm = (v.get("name") or v.get("title") or v.get("supplier") or "").strip()
                    if nm:
                        names.append(nm)
                elif isinstance(v, str) and v.strip():
                    names.append(v.strip())
        elif isinstance(suppliers, list):
            for v in suppliers:
                if isinstance(v, dict):
                    nm = (v.get("name") or v.get("title") or v.get("supplier") or "").strip()
                    if nm:
                        names.append(nm)
                elif isinstance(v, str) and v.strip():
                    names.append(v.strip())

        uniq = sorted({n for n in names if n})
        combo.addItems(uniq)
        combo.blockSignals(False)
        logging.info(f"[CargoTab] supplier combobox filled: {len(uniq)} items")

    # ---------------- Actions ----------------
    @exception_handler
    def add_cargo(self, checked=False):
        # Взяли выбранные значения из верхних комбо
        order = (
            self.cargoCaseNumberInput.currentText().strip()
            if (self.cargoCaseNumberInput is not None and not sip.isdeleted(self.cargoCaseNumberInput))
            else ""
        )
        supplier = (
            self.cargoSupplierInput.currentText().strip()
            if (self.cargoSupplierInput is not None and not sip.isdeleted(self.cargoSupplierInput))
            else ""
        )

        # Подтягиваем клиента и менеджера из дела
        customer, manager = "", ""
        if order:
            case_map = self._build_case_map()
            case = case_map.get(order)
            if case:
                customer, manager = self._extract_customer_manager(case)
        logging.debug(f"[CargoTab] add_cargo: order={order}, resolved customer='{customer}', manager='{manager}'")

        new_data = {
            "order": order,
            "customer": customer,
            "supplier": supplier,
            "manager": manager,
            "deadline": "",
            "tk": self.TK_OPTIONS[0],
            "tracking": "",
            "status": self.STATUS_OPTIONS[0],
            "comment": "",  # новое поле
        }
        new_id = self.firebase_manager.add_cargo(new_data)
        self._upsert_row(new_id, new_data)

        # --- Сообщение об успешном добавлении ---
        try:
            what = order or str(new_id)
            QMessageBox.information(self, "Грузы", f"Запись «{what}» добавлена успешно.")
        except Exception:
            pass

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

        # --- Сообщение об успешном удалении ---
        try:
            QMessageBox.information(self, "Грузы", f"Запись «{cid}» удалена успешно.")
        except Exception:
            pass

    # ---------------- Realtime ----------------
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

    # ---------------- Table helpers ----------------
    def _on_item_changed(self, item: QTableWidgetItem):
        """
        Сохраняем изменения в Firebase.
        Дополнительно: если отредактировали «Номер дела», подтянем клиента/менеджера автоматически.
        """
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
            self.COL_COMMENT: "comment",  # новое поле
        }
        key = key_map.get(col)
        if not key:
            return

        value = item.text()

        # Если изменили номер дела — подтянем клиента/менеджера из cases
        if col == self.COL_ORDER:
            case_map = self._build_case_map()
            case = case_map.get(value.strip())
            if case:
                customer, manager = self._extract_customer_manager(case)

                # локально обновим ячейки
                self._mute = True
                try:
                    self._set_cell_text(row, self.COL_CUSTOMER, customer)
                    self._set_cell_text(row, self.COL_MANAGER, manager)
                finally:
                    self._mute = False

                # и сходу запишем три поля в firebase
                self.firebase_manager.cargo_ref.child(cid).update({
                    "order": value,
                    "customer": customer,
                    "manager": manager,
                })
                return  # уже всё записали

        # Обычное обновление одного поля
        self.firebase_manager.cargo_ref.child(cid).update({key: value})

    def _set_cell_text(self, row: int, col: int, text: str):
        it = self.cargoTable.item(row, col)
        if not it:
            it = QTableWidgetItem()
            self.cargoTable.setItem(row, col, it)
        it.setText(text or "")

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

        # комментарий (просто текстовая ячейка)
        _set(self.COL_COMMENT, str(c.get("comment", "")))

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