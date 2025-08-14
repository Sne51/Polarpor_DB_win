# src/tabs/clients_tab.py
import logging, threading
from typing import Dict, List
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView
from src.decorators import exception_handler


class ClientsTab:
    """
    Вкладка «Клиенты»:
    - lazy activate()/deactivate()
    - SSE-подписки на /clients (и мягкая реакция на /cases — чтобы обновлять кросс‑ссылки при необходимости)
    - add/delete с лёгким обновлением
    """

    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # Прямые ссылки на виджеты главного окна
        try:
            self.clientTable = self.main_window.clientTable
            self.clientNameInput = self.main_window.clientNameInput
            self.addClientButton = self.main_window.addClientButton
            self.deleteClientButton = self.main_window.deleteClientButton
        except AttributeError as e:
            logging.error(f"[ClientsTab] UI attribute missing: {e}")

        self._active = False
        self._subs = {}        # token_name -> token
        self._initialized = False

        self._setup_ui()

    # ------------------- Public API -------------------

    def activate(self):
        if self._active:
            return
        self._active = True
        logging.debug("[ClientsTab] activate")

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
        logging.debug("[ClientsTab] deactivate")
        self._drop_subscriptions()

    # ------------------- UI setup -------------------

    def _setup_ui(self):
        try:
            headers = ["ID", "Название клиента"]
            self.clientTable.setColumnCount(len(headers))
            self.clientTable.setHorizontalHeaderLabels(headers)
            self.clientTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            logging.error(f"[ClientsTab] table setup error: {e}")

        try:
            self.addClientButton.clicked.connect(self.add_new_client)
            self.deleteClientButton.clicked.connect(self.confirm_delete_client)
        except Exception as e:
            logging.error(f"[ClientsTab] connect signals error: {e}")

    # ------------------- Realtime -------------------

    def _ensure_subscriptions(self):
        if "clients" not in self._subs:
            self._subs["clients"] = self.firebase_manager.on("clients", self._on_clients_event)
        # Не обязательно, но полезно при кросс‑обновлениях (если UI захочет что‑то отображать из дел)
        if "cases" not in self._subs:
            self._subs["cases"] = self.firebase_manager.on("cases", self._on_cases_event)

    def _drop_subscriptions(self):
        for token in list(self._subs.values()):
            try:
                self.firebase_manager.off(token)
            except Exception as e:
                logging.warning(f"[ClientsTab] off failed: {e}")
        self._subs.clear()

    # Колбэки из фонового SSE — UI обновляем через main‑thread
    def _on_clients_event(self, _payload):
        if not self._active:
            return
        QTimer.singleShot(0, self.load_client_table_data)

    def _on_cases_event(self, _payload):
        # Пока просто мягко перезагрузим таблицу клиентов — на случай зависимых отображений
        if not self._active:
            return
        QTimer.singleShot(0, self.load_client_table_data)

    # ------------------- Async loaders -------------------

    def _load_all_async(self):
        """Первая фоновая загрузка."""
        def work():
            try:
                clients = self.firebase_manager.get_all_clients() or {}
                return clients, None
            except Exception as e:
                return None, e

        def done(clients, err):
            if err:
                logging.error(f"[ClientsTab] initial load error: {err}")
                return
            self._apply_clients(clients)

        threading.Thread(target=lambda: self._thread_result(work(), done), daemon=True).start()

    def _reload_light_async(self):
        """Лёгкая фоновая перезагрузка."""
        def work():
            try:
                clients = self.firebase_manager.get_all_clients() or {}
                return clients, None
            except Exception as e:
                return None, e

        def done(clients, err):
            if err or not self._active:
                if err:
                    logging.error(f"[ClientsTab] reload error: {err}")
                return
            self._apply_clients(clients)

        threading.Thread(target=lambda: self._thread_result(work(), done), daemon=True).start()

    @staticmethod
    def _thread_result(result_tuple, done_cb):
        clients, err = result_tuple
        QTimer.singleShot(0, lambda: done_cb(clients, err))

    # ------------------- Apply helpers (main thread) -------------------

    def _apply_clients(self, clients: Dict[str, dict]):
        try:
            self.clientTable.setRowCount(0)
            if isinstance(clients, dict):
                # В RTDB иногда попадаются «мусорные» ключи, фильтруем
                rows: List[tuple] = []
                for cid, data in clients.items():
                    if not isinstance(data, dict):
                        continue
                    name = (data.get("name") or "").strip()
                    if not name:
                        continue
                    rows.append((str(cid), name))

                for cid, name in sorted(rows, key=lambda x: (x[1].lower(), x[0])):
                    row = self.clientTable.rowCount()
                    self.clientTable.insertRow(row)
                    self.clientTable.setItem(row, 0, QTableWidgetItem(cid))
                    self.clientTable.setItem(row, 1, QTableWidgetItem(name))

            logging.info("[ClientsTab] Client table data loaded")
        except Exception as e:
            logging.error(f"[ClientsTab] apply clients error: {e}")

    # ------------------- Public loaders -------------------

    @exception_handler
    def load_client_table_data(self):
        clients = self.firebase_manager.get_all_clients() or {}
        self._apply_clients(clients)

    # ------------------- Actions -------------------

    @exception_handler
    def add_new_client(self, checked: bool = False):
        name = (self.clientNameInput.text() or "").strip()
        if not name:
            QMessageBox.warning(self.main_window, "Внимание", "Имя клиента не может быть пустым")
            return

        # Проверим, есть ли уже такой клиент
        clients = self.firebase_manager.get_all_clients() or {}
        existing = None
        for cid, data in clients.items():
            if isinstance(data, dict) and (data.get("name") or "").strip().lower() == name.lower():
                existing = cid
                break

        if existing:
            QMessageBox.information(
                self.main_window, "Информация",
                f"Клиент «{name}» уже существует (ID: {existing})."
            )
            return

        # Добавляем
        new_id = self.firebase_manager.add_client({"name": name})
        logging.info(f"[ClientsTab] added client: {new_id}")
        self.clientNameInput.clear()

        # Лёгкое обновление
        self._reload_light_async()
        QMessageBox.information(self.main_window, "Успех", f"Клиент «{name}» добавлен (ID: {new_id})")

    @exception_handler
    def confirm_delete_client(self, checked: bool = False):
        row = self.clientTable.currentRow()
        if row < 0:
            QMessageBox.warning(self.main_window, "Внимание", "Выберите клиента для удаления")
            return

        cid_item = self.clientTable.item(row, 0)
        name_item = self.clientTable.item(row, 1)
        cid = (cid_item.text() if cid_item else "").strip()
        cname = (name_item.text() if name_item else "").strip()
        if not cid:
            QMessageBox.warning(self.main_window, "Ошибка", "ID клиента не найден")
            return

        resp = QMessageBox.question(
            self.main_window, "Подтверждение",
            f"Удалить клиента «{cname or cid}»?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp != QMessageBox.Yes:
            return

        # Удаляем
        self.firebase_manager.delete_client(cid)
        logging.info(f"[ClientsTab] deleted client: {cid}")

        # Лёгкое обновление
        self._reload_light_async()
        QMessageBox.information(self.main_window, "Успех", "Клиент удалён")