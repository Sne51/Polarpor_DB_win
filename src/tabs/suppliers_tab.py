# src/tabs/suppliers_tab.py
import logging, threading
from typing import Dict, List, Tuple, Optional, Any
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView
from src.decorators import exception_handler


class SuppliersTab:
    """
    Вкладка «Поставщики»:
    - lazy activate()/deactivate()
    - SSE-подписка на /suppliers (и, опционально, /cargo)
    - add/delete с лёгкой перезагрузкой
    - устойчивость к «грязным» данным RTDB (list с None/True, dict/str)
    """

    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Прямые ссылки на виджеты
        try:
            self.supplierTable = self.main_window.supplierTable           # QTableWidget
            self.supplierNameInput = self.main_window.supplierNameInput   # QLineEdit
            self.addSupplierButton = self.main_window.addSupplierButton   # QPushButton
            self.deleteSupplierButton = self.main_window.deleteSupplierButton  # QPushButton
        except AttributeError as e:
            logging.error(f"[SuppliersTab] UI attribute missing: {e}")
            # Не падаем — но без виджетов дальше смысла нет
            raise

        self._active = False
        self._initialized = False
        self._subs = {}  # name -> token

        self._setup_ui()

    # --------------- Public API ---------------

    @exception_handler
    def activate(self):
        """Вызывается при переходе на вкладку."""
        if self._active:
            # Даже если активна — форсим лёгкую подгрузку (на случай, если пришли изменения в фоне)
            self._reload_light_async()
            return

        self._active = True
        logging.debug("[SuppliersTab] activate")

        if not self._initialized:
            self._initialized = True
            self._load_all_async()
        else:
            self._reload_light_async()

        self._ensure_subscriptions()

    def deactivate(self):
        if not self._active:
            return
        self._active = False
        logging.debug("[SuppliersTab] deactivate")
        self._drop_subscriptions()

    # --------------- UI ---------------

    def _setup_ui(self):
        try:
            headers = ["ID", "Поставщик"]
            self.supplierTable.setColumnCount(len(headers))
            self.supplierTable.setHorizontalHeaderLabels(headers)
            self.supplierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            logging.error(f"[SuppliersTab] table setup error: {e}")

        try:
            self.addSupplierButton.clicked.connect(self.add_supplier)
            self.deleteSupplierButton.clicked.connect(self.delete_supplier)
        except Exception as e:
            logging.error(f"[SuppliersTab] connect signals error: {e}")

    # --------------- Realtime ---------------

    def _ensure_subscriptions(self):
        if "suppliers" not in self._subs:
            self._subs["suppliers"] = self.firebase_manager.on("suppliers", self._on_suppliers_event)
        # Если где-то есть кросс‑зависимость — можно слушать и cargo
        if "cargo" not in self._subs:
            self._subs["cargo"] = self.firebase_manager.on("cargo", self._on_cargo_event)

    def _drop_subscriptions(self):
        for token in list(self._subs.values()):
            try:
                self.firebase_manager.off(token)
            except Exception as e:
                logging.warning(f"[SuppliersTab] off failed: {e}")
        self._subs.clear()

    def _on_suppliers_event(self, _payload):
        if not self._active:
            return
        QTimer.singleShot(0, self.load_supplier_table_data)

    def _on_cargo_event(self, _payload):
        if not self._active:
            return
        # Мягкая перезагрузка (на случай, если список поставщиков где-то ещё показан)
        QTimer.singleShot(0, self.load_supplier_table_data)

    # --------------- Async loaders ---------------

    def _load_all_async(self):
        def work():
            try:
                suppliers = self.firebase_manager.get_all_suppliers()  # dict | list | None | мусор
                return suppliers, None
            except Exception as e:
                return None, e

        def done(suppliers, err):
            if err:
                logging.error(f"[SuppliersTab] initial load error: {err}")
                return
            logging.debug(f"[SuppliersTab] initial suppliers type={type(suppliers).__name__}")
            self._apply_suppliers(suppliers)

        threading.Thread(target=lambda: self._thread_result(work(), done), daemon=True).start()

    def _reload_light_async(self):
        def work():
            try:
                suppliers = self.firebase_manager.get_all_suppliers()
                return suppliers, None
            except Exception as e:
                return None, e

        def done(suppliers, err):
            if err or not self._active:
                if err:
                    logging.error(f"[SuppliersTab] reload error: {err}")
                return
            logging.debug(f"[SuppliersTab] reload suppliers type={type(suppliers).__name__}")
            self._apply_suppliers(suppliers)

        threading.Thread(target=lambda: self._thread_result(work(), done), daemon=True).start()

    @staticmethod
    def _thread_result(result_tuple, done_cb):
        suppliers, err = result_tuple
        QTimer.singleShot(0, lambda: done_cb(suppliers, err))

    # --------------- Normalize & Apply ---------------

    def _normalize_suppliers(self, raw: Any) -> List[Tuple[str, str]]:
        """
        Возвращает список (id, name). Терпимо к:
        - dict: { "11": {"name":"ABB"}, "12": "VTE", "bad": True }
        - list: [None, {"name":"ABB"}, True, "VTE"]
        - None/пустое -> []
        """
        rows: List[Tuple[str, str]] = []

        if not raw:
            return rows

        if isinstance(raw, dict):
            for sid, item in raw.items():
                if item is None or isinstance(item, bool):
                    continue
                if isinstance(item, dict):
                    name = (item.get("name") or "").strip()
                    if name:
                        rows.append((str(sid), name))
                elif isinstance(item, str):
                    name = item.strip()
                    if name:
                        rows.append((str(sid), name))
            return rows

        if isinstance(raw, list):
            for idx, item in enumerate(raw):
                if item is None or isinstance(item, bool):
                    continue
                if isinstance(item, dict):
                    name = (item.get("name") or "").strip()
                    if name:
                        rows.append((str(idx), name))
                elif isinstance(item, str):
                    name = item.strip()
                    if name:
                        rows.append((str(idx), name))
            return rows

        # Неизвестный тип — ничего
        return rows

    def _apply_suppliers(self, suppliers_raw: Any):
        try:
            rows = self._normalize_suppliers(suppliers_raw)
            logging.debug(f"[SuppliersTab] normalized suppliers count={len(rows)}")
            self.supplierTable.setRowCount(0)
            for sid, name in sorted(rows, key=lambda x: (x[1].lower(), x[0])):
                row = self.supplierTable.rowCount()
                self.supplierTable.insertRow(row)
                self.supplierTable.setItem(row, 0, QTableWidgetItem(sid))
                self.supplierTable.setItem(row, 1, QTableWidgetItem(name))
            logging.info("[SuppliersTab] Supplier table data loaded")
        except Exception as e:
            logging.error(f"[SuppliersTab] apply suppliers error: {e}")

    # --------------- Public loader ---------------

    @exception_handler
    def load_supplier_table_data(self):
        data = self.firebase_manager.get_all_suppliers()
        logging.debug(f"[SuppliersTab] load table suppliers type={type(data).__name__}")
        self._apply_suppliers(data)

    # --------------- Actions ---------------

    @exception_handler
    def add_supplier(self, checked: bool = False):
        name = (self.supplierNameInput.text() or "").strip()
        if not name:
            QMessageBox.warning(self.main_window, "Внимание", "Название поставщика не может быть пустым")
            return

        # Дубликаты (без регистра)
        raw = self.firebase_manager.get_all_suppliers()
        rows = self._normalize_suppliers(raw)
        if any(n.lower() == name.lower() for _, n in rows):
            QMessageBox.information(self.main_window, "Информация", f"Поставщик «{name}» уже существует.")
            return

        new_id = self.firebase_manager.add_supplier({"name": name})
        logging.info(f"[SuppliersTab] added supplier: {new_id}")
        self.supplierNameInput.clear()

        self._reload_light_async()
        QMessageBox.information(self.main_window, "Успех", f"Поставщик «{name}» добавлен (ID: {new_id})")

    @exception_handler
    def delete_supplier(self, checked: bool = False):
        row = self.supplierTable.currentRow()
        if row < 0:
            QMessageBox.warning(self.main_window, "Внимание", "Выберите поставщика для удаления")
            return

        sid_item = self.supplierTable.item(row, 0)
        name_item = self.supplierTable.item(row, 1)
        sid = (sid_item.text() if sid_item else "").strip()
        sname = (name_item.text() if name_item else "").strip()
        if not sid:
            QMessageBox.warning(self.main_window, "Ошибка", "ID поставщика не найден")
            return

        resp = QMessageBox.question(
            self.main_window, "Подтверждение",
            f"Удалить поставщика «{sname or sid}»?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        self.firebase_manager.delete_supplier(sid)
        logging.info(f"[SuppliersTab] deleted supplier: {sid}")
        self._reload_light_async()
        QMessageBox.information(self.main_window, "Успех", "Поставщик удалён")