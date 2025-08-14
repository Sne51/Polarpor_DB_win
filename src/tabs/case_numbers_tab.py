# /Users/sk/Documents/EDU_Python/Polarpor_DB_win/src/tabs/case_numbers_tab.py
import json
import logging
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import QDateTime
from src.decorators import exception_handler


class CaseNumbersTab(QWidget):
    """
    Вкладка «Номера дел»
    - ленивое наполнение при activate()
    - realtime через FirebaseManager.on('cases', ...)
    - корректные выпадающие списки (менеджеры, клиенты)
    """

    def __init__(self, main_window, firebase_manager):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Виджеты из main_window (как в ProformaTab)
        self.caseTable = self.main_window.caseTable
        self.caseNameInput = self.main_window.caseNameInput         # менеджеры
        self.clientInput = self.main_window.clientInput             # клиенты
        self.addCaseButton = self.main_window.addCaseButton
        self.deleteCaseButton = self.main_window.deleteCaseButton

        self._stream_token = None

        self._setup_ui()
        self._connect_signals()

    # ---------- UI ----------
    def _setup_ui(self):
        headers = ["ID", "Менеджер", "Клиент", "Клиент ID", "Комментарий", "Дата создания"]
        self.caseTable.setColumnCount(len(headers))
        self.caseTable.setHorizontalHeaderLabels(headers)
        self.caseTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _connect_signals(self):
        if self.addCaseButton:
            self.addCaseButton.clicked.connect(self.add_new_case)
        if self.deleteCaseButton:
            self.deleteCaseButton.clicked.connect(self.confirm_delete_case)

    # ---------- lifecycle ----------
    def activate(self):
        # ленивая первичная загрузка
        try:
            self.load_case_table_data()
            self.load_unique_names()         # менеджеры
            self.load_clients_into_combobox()
        except Exception as e:
            logging.debug(f"[CaseNumbersTab] activate preload error: {e}")

        # один активный стрим
        try:
            if self._stream_token:
                self.firebase_manager.off(self._stream_token)
                self._stream_token = None
            self._stream_token = self.firebase_manager.on("cases", self._on_stream_raw)
            logging.debug("[CaseNumbersTab] activate (subscribed)")
        except Exception as e:
            logging.error(f"[CaseNumbersTab] subscribe error: {e}")

    def deactivate(self):
        try:
            if self._stream_token:
                self.firebase_manager.off(self._stream_token)
                self._stream_token = None
                logging.debug("[CaseNumbersTab] deactivate (unsubscribed)")
        except Exception as e:
            logging.error(f"[CaseNumbersTab] deactivate error: {e}")

    # ---------- loaders ----------
    @exception_handler
    def load_case_table_data(self):
        self.caseTable.setRowCount(0)
        cases = self.firebase_manager.get_all_cases() or {}

        # сортируем по числовому id и игнорим нечисловые ключи (типа 'cargos')
        def _key_ok(k):
            try:
                int(k); return True
            except Exception:
                return False

        for cid in sorted([k for k in cases.keys() if _key_ok(k)], key=lambda x: int(x)):
            c = cases.get(cid) or {}
            if not isinstance(c, dict):
                continue
            row = self.caseTable.rowCount()
            self.caseTable.insertRow(row)

            manager = c.get("manager", c.get("name", ""))
            client = c.get("client_name", "")
            client_id = c.get("client", "")
            comment = c.get("comment", "")
            date_created = c.get("date_created", "")

            self.caseTable.setItem(row, 0, QTableWidgetItem(str(cid)))
            self.caseTable.setItem(row, 1, QTableWidgetItem(str(manager)))
            self.caseTable.setItem(row, 2, QTableWidgetItem(str(client)))
            self.caseTable.setItem(row, 3, QTableWidgetItem(str(client_id)))
            self.caseTable.setItem(row, 4, QTableWidgetItem(str(comment)))
            self.caseTable.setItem(row, 5, QTableWidgetItem(str(date_created)))

        logging.info(f"Case table data loaded (rows: {self.caseTable.rowCount()})")

    @exception_handler
    def load_unique_names(self):
        """загрузка списка менеджеров в combo (как в ProformaTab: прямое наполнение)"""
        self.caseNameInput.clear()
        names = self.firebase_manager.get_all_managers() or []
        names = [n for n in names if isinstance(n, str)]
        self.caseNameInput.addItems(sorted(set(names)))

    @exception_handler
    def load_clients_into_combobox(self):
        """загрузка списка клиентов в combo"""
        self.clientInput.clear()
        clients = self.firebase_manager.get_all_clients() or {}
        if not isinstance(clients, dict):
            return
        # упорядочим по имени, выводим только имя
        pairs = []
        for cid, data in clients.items():
            if isinstance(data, dict):
                name = (data.get("name") or "").strip()
                if name:
                    pairs.append((cid, name))
        pairs.sort(key=lambda x: x[1].lower())
        for _cid, name in pairs:
            self.clientInput.addItem(name)

    # ---------- actions ----------
    @exception_handler
    def add_new_case(self, checked: bool = False):
        manager_name = (self.caseNameInput.currentText() or "").strip()
        client_name = (self.clientInput.currentText() or "").strip()

        if not manager_name or not client_name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя менеджера и клиента не могут быть пустыми")
            return

        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        # клиент: проверить/добавить
        client_id = self.firebase_manager.check_and_add_client(client_name)

        new_case = {
            "manager": manager_name,
            "client_name": client_name,
            "client": client_id,
            "comment": "",
            "date_created": date_created,
        }
        case_id = self.firebase_manager.add_case(new_case)

        # моментально показать строку (даже если SSE задержится)
        self._upsert_row(case_id, new_case)

        QMessageBox.information(self.main_window, "Успех", f"Дело добавлено успешно с ID: {case_id}")

    @exception_handler
    def confirm_delete_case(self, checked: bool = False):
        row = self.caseTable.currentRow()
        if row < 0:
            QMessageBox.warning(self.main_window, "Внимание", "Пожалуйста, выберите дело для удаления")
            return
        id_item = self.caseTable.item(row, 0)
        if not id_item:
            QMessageBox.warning(self.main_window, "Ошибка", "ID дела не найден")
            return
        case_id = (id_item.text() or "").strip()
        if not case_id:
            QMessageBox.warning(self.main_window, "Ошибка", "Некорректный ID дела")
            return

        # сервер
        self.firebase_manager.delete_case(case_id)
        # локально сразу убираем
        self.caseTable.removeRow(row)
        QMessageBox.information(self.main_window, "Успех", f"Дело {case_id} удалено")

    # ---------- realtime glue ----------
    def _on_stream_raw(self, raw: str):
        try:
            payload = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if isinstance(payload, dict):
                self._on_stream_event(payload)
        except Exception as e:
            logging.debug(f"[CaseNumbersTab] stream parse error: {e}")

    def _on_stream_event(self, payload: dict):
        # {"path":"/", "data":{...}} или {"path":"/<id>", "data":{...|null}}
        try:
            path = payload.get("path")
            data = payload.get("data")

            # полный снапшот
            if path == "/" and isinstance(data, dict):
                self.load_case_table_data()
                # и перезаполним комбики (чтобы появлялись новые менеджеры/клиенты)
                self.load_unique_names()
                self.load_clients_into_combobox()
                return

            # частичное обновление по ID
            if isinstance(path, str) and path.startswith("/") and len(path) > 1:
                cid = path[1:]
                if data is None:
                    self._remove_row_by_id(cid)
                elif isinstance(data, dict):
                    self._upsert_row(cid, data)
        except Exception as e:
            logging.debug(f"[CaseNumbersTab] stream event error: {e}")

    # ---------- table helpers ----------
    def _find_row_by_id(self, cid: str) -> int:
        for r in range(self.caseTable.rowCount()):
            it = self.caseTable.item(r, 0)
            if it and it.text() == cid:
                return r
        return -1

    def _remove_row_by_id(self, cid: str):
        r = self._find_row_by_id(cid)
        if r >= 0:
            self.caseTable.removeRow(r)

    def _upsert_row(self, cid: str, c: dict):
        row = self._find_row_by_id(cid)
        if row == -1:
            row = self.caseTable.rowCount()
            self.caseTable.insertRow(row)

        def _set(col: int, val: str):
            self.caseTable.setItem(row, col, QTableWidgetItem(val if val is not None else ""))

        manager = c.get("manager", c.get("name", ""))
        client = c.get("client_name", "")
        client_id = c.get("client", "")
        comment = c.get("comment", "")
        date_created = c.get("date_created", "")

        _set(0, str(cid))
        _set(1, str(manager))
        _set(2, str(client))
        _set(3, str(client_id))
        _set(4, str(comment))
        _set(5, str(date_created))