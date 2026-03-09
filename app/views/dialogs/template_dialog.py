from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QTextEdit, QMessageBox,
)
from sqlalchemy.orm import Session
from app.models.template import Template


class TemplateDialog(QDialog):
    """Dialog for adding or editing a Template."""

    def __init__(self, session: Session, template: Template = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._template = template
        self._editing = template is not None

        self.setWindowTitle("Изменить шаблон" if self._editing else "Добавить шаблон")
        self.setMinimumWidth(380)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit()
        layout.addRow("Название *:", self._name_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        layout.addRow("Описание:", self._desc_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if self._editing:
            self._name_edit.setText(template.name or "")
            self._desc_edit.setPlainText(template.description or "")

    def _on_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Поле 'Название' обязательно для заполнения.")
            return

        # Check uniqueness
        existing = (
            self._session.query(Template)
            .filter(Template.name == name)
            .first()
        )
        if existing and (not self._editing or existing.id != self._template.id):
            QMessageBox.warning(
                self, "Ошибка", f"Шаблон с именем '{name}' уже существует."
            )
            return

        if self._editing:
            self._template.name = name
            self._template.description = (
                self._desc_edit.toPlainText().strip() or None
            )
        else:
            self._template = Template(
                name=name,
                description=self._desc_edit.toPlainText().strip() or None,
            )
            self._session.add(self._template)

        self._session.commit()
        self.accept()

    @property
    def template(self) -> Template:
        return self._template
