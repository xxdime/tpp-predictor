from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox,
    QLabel, QMessageBox,
)
from sqlalchemy.orm import Session
from app.models.measurement import Measurement
from app.models.template import TemplateParameter


class MeasurementDialog(QDialog):
    """Dialog for adding or editing a Measurement."""

    def __init__(
        self,
        session: Session,
        part_id: int,
        parameter: TemplateParameter,
        measurement: Measurement = None,
        parent=None,
    ):
        super().__init__(parent)
        self._session = session
        self._part_id = part_id
        self._parameter = parameter
        self._measurement = measurement
        self._editing = measurement is not None

        self.setWindowTitle(
            "Изменить измерение" if self._editing else "Добавить измерение"
        )
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        unit_str = f" [{parameter.unit}]" if parameter.unit else ""
        param_label = QLabel(f"<b>{parameter.name}{unit_str}</b>")
        layout.addRow("Параметр:", param_label)

        self._hours_spin = QDoubleSpinBox()
        self._hours_spin.setMinimum(0.0)
        self._hours_spin.setMaximum(9_999_999.0)
        self._hours_spin.setSingleStep(0.5)
        self._hours_spin.setDecimals(1)
        layout.addRow("Часы наработки *:", self._hours_spin)

        self._value_spin = QDoubleSpinBox()
        self._value_spin.setMinimum(-999_999.0)
        self._value_spin.setMaximum(999_999.0)
        self._value_spin.setSingleStep(0.01)
        self._value_spin.setDecimals(4)
        layout.addRow(f"Значение{unit_str} *:", self._value_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if self._editing:
            self._hours_spin.setValue(measurement.hours)
            self._value_spin.setValue(measurement.value)

    def _on_accept(self):
        hours = self._hours_spin.value()
        value = self._value_spin.value()

        if self._editing:
            self._measurement.hours = hours
            self._measurement.value = value
        else:
            self._measurement = Measurement(
                part_id=self._part_id,
                parameter_id=self._parameter.id,
                hours=hours,
                value=value,
            )
            self._session.add(self._measurement)

        self._session.commit()
        self.accept()

    @property
    def measurement(self) -> Measurement:
        return self._measurement
