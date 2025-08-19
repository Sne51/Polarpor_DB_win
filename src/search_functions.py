from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
import logging


def search_in_case_table(case_table, firebase_manager, search_text, main_window):
    """Поиск по таблице дел."""
    search_text = (search_text or "").lower().strip()
    case_table.setRowCount(0)  # Очистить таблицу перед добавлением результатов

    cases = firebase_manager.get_all_cases()
    if not cases:
        QMessageBox.warning(main_window, "Поиск", "База данных дел пуста.")
        logging.info("No cases found in database.")
        return

    found = False

    for case_id, case_data in cases.items():
        if not isinstance(case_data, dict):
            logging.debug(f"Skipping non-dict item for case: {case_id}")
            continue

        if (
            search_text in case_id.lower()
            or any(search_text in str(value).lower() for value in case_data.values())
        ):
            found = True
            row = case_table.rowCount()
            case_table.insertRow(row)
            case_table.setItem(row, 0, QTableWidgetItem(case_id))
            case_table.setItem(row, 1, QTableWidgetItem(case_data.get("name", "")))
            case_table.setItem(row, 2, QTableWidgetItem(case_data.get("client_name", "")))
            case_table.setItem(row, 3, QTableWidgetItem(case_data.get("client", "")))
            case_table.setItem(row, 4, QTableWidgetItem(case_data.get("comment", "")))
            case_table.setItem(row, 5, QTableWidgetItem(case_data.get("date_created", "")))

    if not found:
        QMessageBox.information(main_window, "Поиск", "Дело с таким номером или данными не найдено.")
        logging.info("Case search: No results found.")
    else:
        logging.info(f"Case search: Found results for '{search_text}'.")
        # ВАЖНО: правильно переключаемся на таб-виджет из main.ui -> settingsTab
        main_window.settingsTab.setCurrentIndex(0)  # вкладка "Номера дел"


def search_in_proforma_table(proforma_table, firebase_manager, search_text, main_window):
    """Поиск по таблице проформ."""
    search_text = (search_text or "").lower().strip()
    proforma_table.setRowCount(0)

    proformas = firebase_manager.get_all_proformas()
    if not proformas:
        QMessageBox.warning(main_window, "Поиск", "База данных проформ пуста.")
        logging.info("No proformas found in database.")
        return

    found = False

    for proforma_id, proforma_data in proformas.items():
        if not isinstance(proforma_data, dict):
            logging.debug(f"Skipping non-dict item for proforma: {proforma_id}")
            continue

        if (
            search_text in proforma_id.lower()
            or any(search_text in str(value).lower() for value in proforma_data.values())
        ):
            found = True
            row = proforma_table.rowCount()
            proforma_table.insertRow(row)
            proforma_table.setItem(row, 0, QTableWidgetItem(proforma_data.get("case_number", "")))
            proforma_table.setItem(row, 1, QTableWidgetItem(proforma_id))
            proforma_table.setItem(row, 2, QTableWidgetItem(proforma_data.get("name", "")))
            proforma_table.setItem(row, 3, QTableWidgetItem(proforma_data.get("client", "")))
            proforma_table.setItem(row, 4, QTableWidgetItem(proforma_data.get("comment", "")))
            proforma_table.setItem(row, 5, QTableWidgetItem(proforma_data.get("date_created", "")))

    if not found:
        QMessageBox.information(main_window, "Поиск", "Проформа с таким номером или данными не найдена.")
        logging.info("Proforma search: No results found.")
    else:
        logging.info(f"Proforma search: Found results for '{search_text}'.")
        main_window.settingsTab.setCurrentIndex(1)  # вкладка "Номера проформ"


def search_in_client_table(client_table, firebase_manager, search_text, main_window):
    """Поиск по таблице клиентов."""
    search_text = (search_text or "").lower().strip()
    client_table.setRowCount(0)

    clients = firebase_manager.get_all_clients()
    if not clients:
        QMessageBox.warning(main_window, "Поиск", "База данных клиентов пуста.")
        logging.info("No clients found in database.")
        return

    found = False

    for client_id, client_data in clients.items():
        # client_data может быть строкой или dict (на всякий случай обрабатываем оба)
        values_iterable = client_data.values() if isinstance(client_data, dict) else [client_data]
        if search_text in client_id.lower() or any(
            search_text in str(value).lower() for value in values_iterable
        ):
            found = True
            row = client_table.rowCount()
            client_table.insertRow(row)
            client_name = client_data.get("name", "") if isinstance(client_data, dict) else str(client_data)
            client_table.setItem(row, 0, QTableWidgetItem(client_id))
            client_table.setItem(row, 1, QTableWidgetItem(client_name))

    if not found:
        QMessageBox.information(main_window, "Поиск", "Клиент с таким номером или данными не найден.")
        logging.info("Client search: No results found.")
    else:
        logging.info(f"Client search: Found results for '{search_text}'.")
        main_window.settingsTab.setCurrentIndex(2)  # вкладка "Клиенты"


def handle_search_input(search_input, search_function, *args):
    """Обработка нажатия Enter для поиска."""
    search_input.returnPressed.connect(lambda: search_function(*args))