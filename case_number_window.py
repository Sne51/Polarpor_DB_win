import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal
from firebase_manager import FirebaseManager

class CaseNumberWindow(QWidget):
    client_added_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.db = FirebaseManager()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Case Numbers')

        layout = QVBoxLayout()

        self.client_dropdown = QComboBox(self)
        self.client_dropdown.setMaxVisibleItems(10)
        self.update_client_dropdown()
        layout.addWidget(self.client_dropdown)

        self.client_input = QLineEdit(self)
        self.client_input.setPlaceholderText('Enter new client ID')
        layout.addWidget(self.client_input)

        self.add_button = QPushButton('Add Client', self)
        self.add_button.clicked.connect(self.add_client)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def update_client_dropdown(self):
        clients = self.db.get_all_clients()
        self.client_dropdown.clear()
        for client in clients:
            self.client_dropdown.addItem(client['client_id'])

    def add_client(self):
        client_id = self.client_input.text()
        if client_id:
            client_data = {'client_id': client_id}
            if self.db.add_client(client_id, client_id, client_id):
                QMessageBox.information(self, 'Success', 'Client added successfully!')
                self.update_client_dropdown()
                self.client_added_signal.emit()
            else:
                QMessageBox.warning(self, 'Error', 'Client already exists!')
        else:
            QMessageBox.warning(self, 'Error', 'Client ID cannot be empty!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CaseNumberWindow()
    window.show()
    sys.exit(app.exec_())
