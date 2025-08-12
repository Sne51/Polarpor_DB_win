import logging
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QHeaderView
from src.decorators import exception_handler


class ProformaTab:
    """
    Вкладка «Номера проформ» — как CaseNumbersTab:
    работаем напрямую через атрибуты main_window (без findChild).
    """

    def __init__(self, main_window, firebase_manager):
        self.main_window = main_window
        self.firebase_manager = firebase_manager

        # --- Прямой доступ к виджетам, как в CaseNumbersTab ---
        try:
            self.proformaTable = self.main_window.proformaTable                # QTableWidget
            self.proformaClientInput = self.main_window.proformaClientInput    # QComboBox (номер дела)
            self.proformaNameInput = self.main_window.proformaNameInput        # QComboBox (менеджер)
            self.proformaCommentInput = self.main_window.proformaCommentInput  # QLineEdit
            self.addProformaButton = self.main_window.addProformaButton        # QPushButton
            self.deleteProformaButton = self.main_window.deleteProformaButton  # QPushButton
        except AttributeError as e:
            logging.error(f"[ProformaTab] Не найден атрибут UI: {e}")

        self.setup_proforma_tab()

    # -------------------- Setup --------------------
    @exception_handler
    def setup_proforma_tab(self):
        # Таблица и заголовки
        headers = ["ID", "Номер дела", "Имя", "Комментарий", "Создано"]
        try:
            self.proformaTable.setColumnCount(len(headers))
            self.proformaTable.setHorizontalHeaderLabels(headers)
            self.proformaTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        except Exception as e:
            logging.error(f"[ProformaTab] Ошибка подготовки таблицы: {e}")

        # Сигналы
        try:
            self.addProformaButton.clicked.connect(self.add_proforma)
            self.deleteProformaButton.clicked.connect(self.delete_proforma)
        except Exception as e:
            logging.error(f"[ProformaTab] Ошибка подключения сигналов: {e}")

        # Первая загрузка — как в CaseNumbersTab
        self.load_proforma_table_data()
        self.load_case_numbers_for_proforma()
        self.load_managers_into_combobox()

    # -------------------- Helpers --------------------
    @staticmethod
    def _normalize_manager_names(raw):
        """Принимает dict/list/строки и возвращает список имён менеджеров."""
        names = []
        if raw is None:
            return names

        # {"managers": [...]} -> ...
        if isinstance(raw, dict) and 'managers' in raw:
            raw = raw.get('managers')

        # dict id->{name:..} | list
        iterable = raw.values() if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
        for item in iterable:
            if isinstance(item, str):
                name = item.strip()
            elif isinstance(item, dict):
                name = (
                    item.get('name')
                    or item.get('full_name')
                    or item.get('title')
                    or item.get('manager')
                    or ''
                ).strip()
            else:
                name = ''
            if name and name not in names:
                names.append(name)
        return names

    # -------------------- Loaders --------------------
    @exception_handler
    def load_proforma_table_data(self):
        try:
            self.proformaTable.setRowCount(0)
        except Exception:
            return

        data = self.firebase_manager.get_all_proformas() or {}
        logging.debug(f"Proformas loaded: {data}")

        if isinstance(data, dict):
            for pid, p in data.items():
                if not isinstance(p, dict):
                    continue
                row = self.proformaTable.rowCount()
                self.proformaTable.insertRow(row)
                self.proformaTable.setItem(row, 0, QTableWidgetItem(str(pid)))
                self.proformaTable.setItem(row, 1, QTableWidgetItem(str(p.get('case_number', ''))))
                self.proformaTable.setItem(row, 2, QTableWidgetItem(str(p.get('name', ''))))
                self.proformaTable.setItem(row, 3, QTableWidgetItem(str(p.get('comment', ''))))
                self.proformaTable.setItem(row, 4, QTableWidgetItem(str(p.get('date_created', ''))))
        logging.info("Proforma table data loaded")

    @exception_handler
    def load_case_numbers_for_proforma(self):
        # ТАК ЖЕ, как в CaseNumbersTab: чистим и добавляем только числовые ID
        try:
            self.proformaClientInput.clear()
        except Exception:
            return

        cases = self.firebase_manager.get_all_cases() or {}
        case_ids = []
        if isinstance(cases, dict):
            case_ids = [
                cid for cid, c in cases.items()
                if isinstance(cid, str) and cid.isdigit() and isinstance(c, dict)
            ]
            case_ids.sort(key=lambda x: int(x))
        self.proformaClientInput.addItems(case_ids)
        logging.debug(f"Case IDs loaded into combobox: {case_ids}")

    @exception_handler
    def load_managers_into_combobox(self):
        try:
            self.proformaNameInput.clear()
        except Exception:
            return

        raw = self.firebase_manager.get_all_managers()
        names = list(raw) if isinstance(raw, list) and all(isinstance(x, str) for x in raw) else self._normalize_manager_names(raw)
        names_sorted = sorted(names)
        self.proformaNameInput.addItems(names_sorted)
        logging.debug(f"Managers loaded into combobox: {names_sorted}")

    # -------------------- Actions --------------------
    @exception_handler
    def add_proforma(self, checked: bool = False):
        try:
            name = (self.proformaNameInput.currentText() or '').strip()
            case_number = (self.proformaClientInput.currentText() or '').strip()
            comment = (self.proformaCommentInput.text() or '').strip()
        except Exception:
            QMessageBox.warning(self.main_window, "Ошибка", "Элементы формы не найдены")
            return

        if not name and not case_number:
            QMessageBox.warning(self.main_window, "Внимание", "Укажите минимум имя или номер дела")
            return

        # --- Проверка: номер дела не должен уже использоваться в другой проформе ---
        if case_number:
            try:
                existing = self.firebase_manager.get_all_proformas() or {}
                used_case_numbers = {
                    str(p.get('case_number')).strip()
                    for p in existing.values()
                    if isinstance(p, dict) and p.get('case_number') is not None
                }
                if case_number in used_case_numbers:
                    QMessageBox.warning(
                        self.main_window,
                        "Внимание",
                        f"Номер дела {case_number} уже используется в другой проформе. "
                        "Выберите другой номер дела."
                    )
                    return
            except Exception as e:
                logging.error(f"[ProformaTab] Ошибка проверки уникальности номера дела: {e}")

        new_id = self.firebase_manager.add_proforma({
            'name': name,
            'case_number': case_number,
            'comment': comment,
        })
        logging.info(f"Добавлена проформа: {new_id}")
        QMessageBox.information(self.main_window, "Успех", f"Проформа добавлена успешно с ID: {new_id}")
        try:
            self.proformaCommentInput.clear()
        except Exception:
            pass

        # Обновление, чтобы в списках был актуал
        self.load_proforma_table_data()
        self.load_case_numbers_for_proforma()
        self.load_managers_into_combobox()

    @exception_handler
    def delete_proforma(self, checked: bool = False):
        try:
            row = self.proformaTable.currentRow()
        except Exception:
            return
        if row < 0:
            QMessageBox.warning(self.main_window, "Внимание", "Выберите строку для удаления")
            return
        id_item = self.proformaTable.item(row, 0)
        if not id_item:
            QMessageBox.warning(self.main_window, "Ошибка", "ID проформы не найден в строке")
            return
        pid = (id_item.text() or '').strip()
        if not pid:
            QMessageBox.warning(self.main_window, "Ошибка", "Некорректный ID проформы")
            return

        self.firebase_manager.delete_proforma(pid)
        logging.info(f"Проформа удалена: {pid}")

        # Обновление после удаления
        self.load_proforma_table_data()
        self.load_case_numbers_for_proforma()
        self.load_managers_into_combobox()