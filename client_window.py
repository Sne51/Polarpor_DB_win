import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from firebase_manager import FirebaseManager

class ClientWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.db = FirebaseManager()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Clients')

        layout = QVBoxLayout()

        self.client_table = QTableWidget(self)
        layout.addWidget(self.client_table)

        self.setLayout(layout)
        self.update_client_table()

    def update_client_table(self):
        clients = self.db.get_all_clients()
        self.client_table.setRowCount(len(clients))
        self.client_table.setColumnCount(3)
        self.client_table.setHorizontalHeaderLabels(['Client ID', 'Name', 'Customer'])

        for row, client in enumerate(clients):
            self.client_table.setItem(row, 0, QTableWidgetItem(client['client_id']))
            self.client_table.setItem(row, 1, QTableWidgetItem(client['name']))
            self.client_table.setItem(row, 2, QTableWidgetItem(client['customer']))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec_())
