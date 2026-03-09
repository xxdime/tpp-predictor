from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QMessageBox, QLabel,
)
from sqlalchemy.orm import Session
from app.models.template import Template
from app.models.part import Part


class PartDialog(QDialog):
    """Dialog for adding or editing a Part."""

    def __init__(self, session: Session, part: Part = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._part = part
        self._editing = part is not None

        self.setWindowTitle("Изменить деталь" if self._editing else "Добавить деталь")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit()
        layout.addRow("Название *:", self._name_edit)

        self._serial_edit = QLineEdit()
        layout.addRow("Серийный номер:", self._serial_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        layout.addRow("Описание:", self._desc_edit)

        self._template_combo = QComboBox()
        self._load_templates()
        layout.addRow("Шаблон *:", self._template_combo)

        if self._editing:
            self._template_combo.setEnabled(False)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if self._editing:
            self._name_edit.setText(part.name or "")
            self._serial_edit.setText(part.serial_number or "")
            self._desc_edit.setPlainText(part.description or "")
            # Select current template
            for i in range(self._template_combo.count()):
                if self._template_combo.itemData(i) == part.template_id:
                    self._template_combo.setCurrentIndex(i)
                    break

    def _load_templates(self):
        templates = self._session.query(Template).order_by(Template.name).all()
        for t in templates:
            self._template_combo.addItem(t.name, t.id)

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно для заполнения.")
            return

        if self._template_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет доступных шаблонов. Сначала создайте шаблон.")
            return

        template_id = self._template_combo.currentData()

        if self._editing:
            self._part.name = name
            self._part.serial_number = self._serial_edit.text().strip() or None
            self._part.description = self._desc_edit.toPlainText().strip() or None
        else:
            self._part = Part(
                name=name,
                serial_number=self._serial_edit.text().strip() or None,
                description=self._desc_edit.toPlainText().strip() or None,
                template_id=template_id,
            )
            self._session.add(self._part)

        self._session.commit()
        self.accept()

    @property
    def part(self) -> Part:
        return self._part
