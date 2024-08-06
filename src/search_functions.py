# search_functions.py
from PyQt5.QtWidgets import QTableWidgetItem


def search_in_case_table(caseTable, firebase_manager, search_text):
    caseTable.setRowCount(0)
    cases = firebase_manager.get_all_cases()
    for case_id, case_data in cases.items():
        if search_text in case_id.lower() or \
           any(search_text in str(value).lower() for value in case_data.values()):
            row_position = caseTable.rowCount()
            caseTable.insertRow(row_position)
            caseTable.setItem(row_position, 0, QTableWidgetItem(case_id))
            caseTable.setItem(row_position, 1, QTableWidgetItem(case_data.get('name', '')))
            caseTable.setItem(row_position, 2, QTableWidgetItem(case_data.get('client_name', '')))
            caseTable.setItem(row_position, 3, QTableWidgetItem(case_data.get('client', '')))
            caseTable.setItem(row_position, 4, QTableWidgetItem(case_data.get('comment', '')))
            caseTable.setItem(row_position, 5, QTableWidgetItem(case_data.get('date_created', '')))


def search_in_proforma_table(proformaTable, firebase_manager, search_text):
    proformaTable.setRowCount(0)
    proformas = firebase_manager.get_all_proformas()
    for proforma_id, proforma_data in proformas.items():
        if search_text in proforma_id.lower() or \
           any(search_text in str(value).lower() for value in proforma_data.values()):
            row_position = proformaTable.rowCount()
            proformaTable.insertRow(row_position)
            proformaTable.setItem(row_position, 0, QTableWidgetItem(proforma_data.get('case_number', '')))
            proformaTable.setItem(row_position, 1, QTableWidgetItem(proforma_id))
            proformaTable.setItem(row_position, 2, QTableWidgetItem(proforma_data.get('name', '')))
            proformaTable.setItem(row_position, 3, QTableWidgetItem(proforma_data.get('client', '')))
            proformaTable.setItem(row_position, 4, QTableWidgetItem(proforma_data.get('comment', '')))
            proformaTable.setItem(row_position, 5, QTableWidgetItem(proforma_data.get('date_created', '')))


def search_in_client_table(clientTable, firebase_manager, search_text):
    clientTable.setRowCount(0)
    clients = firebase_manager.get_all_clients()
    for client_id, client_data in clients.items():
        if search_text in client_id.lower() or \
           any(search_text in str(value).lower() for value in client_data.values()):
            row_position = clientTable.rowCount()
            clientTable.insertRow(row_position)
            clientTable.setItem(row_position, 0, QTableWidgetItem(client_id))
            clientTable.setItem(row_position, 1, QTableWidgetItem(client_data.get('name', '') if isinstance(client_data, dict) else client_data))
