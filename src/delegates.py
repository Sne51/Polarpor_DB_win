from PyQt5.QtWidgets import QStyledItemDelegate, QDateEdit
from PyQt5.QtCore import Qt, QDate

class QDateEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, date_format="dd-MM-yy"):
        super().__init__(parent)
        self.date_format = date_format

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setDisplayFormat(self.date_format)
        editor.setCalendarPopup(True)
        return editor

    def setEditorData(self, editor, index):
        date_str = index.model().data(index, Qt.EditRole)
        if date_str:
            date = QDate.fromString(date_str, self.date_format)
            if date.isValid():
                editor.setDate(date)
            else:
                editor.setDate(QDate.currentDate())
        else:
            editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        date = editor.date()
        model.setData(index, date.toString(self.date_format), Qt.EditRole)