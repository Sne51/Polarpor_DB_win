# /Users/sk/Documents/EDU_Python/Polarpor_DB_win/src/tabs/proforma_tab.py
import json
import logging
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtCore import QDateTime
from src.decorators import exception_handler


class ProformaTab(QWidget):
    """
    Вкладка «Номера проформ»:
    - Прямая работа с виджетами main_window
    - Реалтайм через FirebaseManager.on('proformas', ...)
    - Корректная обработка удаления (data == null в SSE)
    """

    def __init__(self, main_window, firebase_manager):
        super().__init__(parent=main_window)
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Прямые ссылки на виджеты
        self.proformaTable = self.main_window.proformaTable
        self.proformaClientInput = self.main_window.proformaClientInput
        self.proformaNameInput = self.main_window.proformaNameInput
        self.proformaCommentInput = self.main_window.proformaCommentInput
        self.addProformaButton = self.main_window.addProformaButton
        self.deleteProformaButton = self.main_window.deleteProformaButton

        # токен активной SSE-подписки (None, если не активна)
        self._stream_token = None

        self._setup_ui()
        self._connect_signals()

    # ---------------- UI ----------------
    def _setup_ui(self):
        headers = ["ID", "Номер дела", "Имя", "Комментарий", "Создано"]
        self.proformaTable.setColumnCount(len(headers))
        self.proformaTable.setHorizontalHeaderLabels(headers)
        self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _connect_signals(self):
        if self.addProformaButton:
            self.addProformaButton.clicked.connect(self.add_proforma)
        if self.deleteProformaButton:
            self.deleteProformaButton.clicked.connect(self.delete_proforma)

    # ---------------- Lifecycle ----------------
    def activate(self):
        """Ленивая подгрузка и включение realtime-подписки."""
        try:
            self.load_proforma_table_data()
            self.load_case_numbers_for_proforma()
            self.load_managers_into_combobox()
        except Exception as e:
            logging.debug(f"[ProformaTab] activate preload error: {e}")

        # одна активная подписка на вкладку
        try:
            if self._stream_token:
                self.firebase_manager.off(self._stream_token)
                self._stream_token = None
            # ВАЖНО: путь без ведущего слэша и коллбэк принимает raw JSON-строку
            self._stream_token = self.firebase_manager.on("proformas", self._on_stream_raw)
            logging.debug("[ProformaTab] activate (subscribed)")
        except Exception as e:
            logging.error(f"[ProformaTab] subscribe error: {e}")

    def deactivate(self):
        """Выключаем стрим."""
        try:
            if self._stream_token:
                self.firebase_manager.off(self._stream_token)
                self._stream_token = None
                logging.debug("[ProformaTab] deactivate (unsubscribed)")
        except Exception as e:
            logging.error(f"[ProformaTab] deactivate error: {e}")

    # ---------------- Loaders ----------------
    @exception_handler
    def load_proforma_table_data(self):
        self.proformaTable.setRowCount(0)
        data = self.firebase_manager.get_all_proformas() or {}
        if isinstance(data, dict):
            # сортировка по числовому id
            def _k(x):
                try:
                    return int(x)
                except Exception:
                    return 10**9
            for pid in sorted(list(data.keys()), key=_k):
                p = data.get(pid)
                if isinstance(p, dict):
                    self._upsert_row(pid, p)
        logging.info(f"Proforma table data loaded (rows: {self.proformaTable.rowCount()})")

    @exception_handler
    def load_case_numbers_for_proforma(self):
        """Заполняем выпадающий список номерами дел (как в CaseNumbersTab)."""
        self.proformaClientInput.clear()
        cases = self.firebase_manager.get_all_cases() or {}
        if not isinstance(cases, dict):
            return
        case_ids = [
            cid for cid, c in cases.items()
            if isinstance(cid, str) and cid.isdigit() and isinstance(c, dict)
        ]
        case_ids.sort(key=lambda x: int(x))
        self.proformaClientInput.addItems(case_ids)
        logging.debug(f"[ProformaTab] cases->combobox: {case_ids}")

    @exception_handler
    def load_managers_into_combobox(self):
        self.proformaNameInput.clear()
        raw = self.firebase_manager.get_all_managers() or []
        # В твоём FirebaseManager.get_all_managers возвращается list[str]
        names = [n for n in raw if isinstance(n, str)]
        names.sort()
        self.proformaNameInput.addItems(names)
        logging.debug(f"[ProformaTab] managers->combobox: {names}")

    # ---------------- Actions ----------------
    @exception_handler
    def add_proforma(self, checked: bool = False):
        name = (self.proformaNameInput.currentText() or "").strip()
        case_number = (self.proformaClientInput.currentText() or "").strip()
        comment = (self.proformaCommentInput.text() or "").strip()

        if not name and not case_number:
            QMessageBox.warning(self.main_window, "Внимание", "Укажите минимум имя или номер дела")
            return

        # Проверка уникальности номера дела среди проформ
        if case_number:
            existing = self.firebase_manager.get_all_proformas() or {}
            used = {
                str(p.get("case_number")).strip()
                for p in existing.values()
                if isinstance(p, dict) and p.get("case_number") is not None
            }
            if case_number in used:
                QMessageBox.warning(
                    self.main_window, "Внимание",
                    f"Номер дела {case_number} уже используется в другой проформе."
                )
                return

        # Сразу проставим date_created (чтобы сервер и локальная таблица совпадали)
        date_created = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        new_id = self.firebase_manager.add_proforma({
            "name": name,
            "case_number": case_number,
            "comment": comment,
            "date_created": date_created,
        })
        logging.info(f"[ProformaTab] added proforma: {new_id}")
        QMessageBox.information(self.main_window, "Успех", f"Проформа добавлена успешно с ID: {new_id}")

        # Локальный быстрый апдейт (на случай задержки SSE)
        self._upsert_row(new_id, {
            "name": name,
            "case_number": case_number,
            "comment": comment,
            "date_created": date_created,
        })
        self.proformaCommentInput.clear()

    @exception_handler
    def delete_proforma(self, checked: bool = False):
        row = self.proformaTable.currentRow()
        if row < 0:
            QMessageBox.warning(self.main_window, "Внимание", "Выберите строку для удаления")
            return
        id_item = self.proformaTable.item(row, 0)
        if not id_item:
            QMessageBox.warning(self.main_window, "Ошибка", "ID проформы не найден")
            return
        pid = (id_item.text() or "").strip()
        if not pid:
            QMessageBox.warning(self.main_window, "Ошибка", "Некорректный ID проформы")
            return

        # удаляем на сервере
        self.firebase_manager.delete_proforma(pid)

        # мгновенно убираем из таблицы (даже если SSE придёт позже)
        self.proformaTable.removeRow(row)
        logging.info(f"[ProformaTab] deleted proforma: {pid}")
        QMessageBox.information(self.main_window, "Готово", f"Проформа {pid} удалена.")

    # ---------------- Stream glue ----------------
    def _on_stream_raw(self, raw: str):
        """
        Коллбэк из FirebaseManager.on — приходит raw JSON-строка.
        Пример: {"path":"/1010","data":{...}} или {"path":"/1010","data":null}
        """
        try:
            payload = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if not isinstance(payload, dict):
                return
            self._on_stream_event(payload)
        except Exception as e:
            logging.debug(f"[ProformaTab] stream parse error: {e}")

    # ---------------- Stream handler ----------------
    def _on_stream_event(self, payload: dict):
        """
        payload: {"path":"/", "data":{...}} или {"path":"/<id>", "data":{...|null}}
        """
        try:
            path = payload.get("path")
            data = payload.get("data")

            # Полный снапшот
            if path == "/" and isinstance(data, dict):
                self.proformaTable.setRowCount(0)
                for pid, p in data.items():
                    if isinstance(p, dict):
                        self._upsert_row(pid, p)
                return

            # Частичное обновление по ID
            if isinstance(path, str) and path.startswith("/") and len(path) > 1:
                pid = path[1:]
                if data is None:
                    # УДАЛЕНИЕ
                    self._remove_row_by_id(pid)
                elif isinstance(data, dict):
                    # UPSERT
                    self._upsert_row(pid, data)
        except Exception as e:
            logging.debug(f"[ProformaTab] stream event error: {e}")

    # ---------------- Table helpers ----------------
    def _find_row_by_id(self, pid: str) -> int:
        for r in range(self.proformaTable.rowCount()):
            it = self.proformaTable.item(r, 0)
            if it and it.text() == pid:
                return r
        return -1

    def _remove_row_by_id(self, pid: str):
        r = self._find_row_by_id(pid)
        if r >= 0:
            self.proformaTable.removeRow(r)

    def _upsert_row(self, pid: str, p: dict):
        # если строка есть — обновим, иначе добавим
        row = self._find_row_by_id(pid)
        if row == -1:
            row = self.proformaTable.rowCount()
            self.proformaTable.insertRow(row)

        def _set(col: int, val: str):
            self.proformaTable.setItem(row, col, QTableWidgetItem(val if val is not None else ""))

        _set(0, str(pid))
        _set(1, str(p.get("case_number", "")))
        _set(2, str(p.get("name", "")))
        _set(3, str(p.get("comment", "")))
        _set(4, str(p.get("date_created", "")))