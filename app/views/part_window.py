from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QComboBox, QLabel, QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt

import numpy as np

from app.database.engine import get_session
from app.models.part import Part
from app.models.measurement import Measurement
from app.models.forecast_settings import ForecastSettings
from app.views.widgets.forecast_plot import ForecastPlotWidget
from app.views.dialogs.measurement_dialog import MeasurementDialog
from app.services import forecast_service


class PartWindow(QMainWindow):
    """Window showing detail info and measurements for a single Part."""

    def __init__(self, part_id: int, parent=None):
        super().__init__(parent)
        self._part_id = part_id
        self._session = get_session()
        self._part = self._session.get(Part, part_id)

        self.setWindowTitle(f"Деталь: {self._part.name}")
        self.setMinimumSize(1000, 650)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # --- Header ---
        header_layout = QHBoxLayout()
        sn = f" [с/н: {self._part.serial_number}]" if self._part.serial_number else ""
        self._header_label = QLabel(f"<b>{self._part.name}</b>{sn}")
        header_layout.addWidget(self._header_label)

        header_layout.addStretch()

        header_layout.addWidget(QLabel("Параметр:"))
        self._param_combo = QComboBox()
        self._param_combo.setMinimumWidth(200)
        header_layout.addWidget(self._param_combo)
        root_layout.addLayout(header_layout)

        # --- Splitter: table | plot ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: table + measurement buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Часы наработки", "Значение"])
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self._table)

        meas_btn_layout = QHBoxLayout()
        self._btn_add_meas = QPushButton("Добавить")
        self._btn_add_meas.clicked.connect(self._on_add_measurement)
        meas_btn_layout.addWidget(self._btn_add_meas)

        self._btn_edit_meas = QPushButton("Изменить")
        self._btn_edit_meas.clicked.connect(self._on_edit_measurement)
        meas_btn_layout.addWidget(self._btn_edit_meas)

        self._btn_delete_meas = QPushButton("Удалить")
        self._btn_delete_meas.clicked.connect(self._on_delete_measurement)
        meas_btn_layout.addWidget(self._btn_delete_meas)

        left_layout.addLayout(meas_btn_layout)
        left_widget.setMinimumWidth(300)
        left_widget.setMaximumWidth(400)

        splitter.addWidget(left_widget)

        # Right: plot
        self._plot_widget = ForecastPlotWidget()
        splitter.addWidget(self._plot_widget)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)

        # --- Update forecast button ---
        btn_forecast_layout = QHBoxLayout()
        btn_forecast_layout.addStretch()
        self._btn_update_forecast = QPushButton("Обновить прогноз")
        self._btn_update_forecast.clicked.connect(self._on_update_forecast)
        btn_forecast_layout.addWidget(self._btn_update_forecast)
        root_layout.addLayout(btn_forecast_layout)

        # --- Status labels ---
        self._status_label_param = QLabel("—")
        self._status_label_critical = QLabel("—")
        root_layout.addWidget(self._status_label_param)
        root_layout.addWidget(self._status_label_critical)

        # --- Load data ---
        self._load_parameters()
        self._param_combo.currentIndexChanged.connect(self._on_param_changed)

    # ------------------------------------------------------------------
    def _current_parameter(self):
        idx = self._param_combo.currentIndex()
        if idx < 0:
            return None
        return self._param_combo.itemData(idx)

    def _load_parameters(self):
        self._param_combo.blockSignals(True)
        self._param_combo.clear()
        for param in self._part.template.parameters:
            unit_str = f" [{param.unit}]" if param.unit else ""
            self._param_combo.addItem(f"{param.name}{unit_str}", param)
        self._param_combo.blockSignals(False)
        self._load_measurements()

    def _on_param_changed(self):
        self._load_measurements()
        # Do NOT recalculate forecast — only refresh table

    def _load_measurements(self):
        param = self._current_parameter()
        if param is None:
            self._table.setRowCount(0)
            return

        unit_str = f" [{param.unit}]" if param.unit else ""
        self._table.setHorizontalHeaderLabels(
            ["Часы наработки", f"Значение{unit_str}"]
        )

        measurements = (
            self._session.query(Measurement)
            .filter(
                Measurement.part_id == self._part_id,
                Measurement.parameter_id == param.id,
            )
            .order_by(Measurement.hours)
            .all()
        )

        self._table.setRowCount(len(measurements))
        for row, m in enumerate(measurements):
            self._table.setItem(row, 0, QTableWidgetItem(str(m.hours)))
            self._table.setItem(row, 1, QTableWidgetItem(str(m.value)))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, m.id)

    # ------------------------------------------------------------------
    def _on_add_measurement(self):
        param = self._current_parameter()
        if param is None:
            return
        dlg = MeasurementDialog(self._session, self._part_id, param, parent=self)
        if dlg.exec():
            self._load_measurements()

    def _on_edit_measurement(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Информация", "Выберите измерение.")
            return
        meas_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        meas = self._session.get(Measurement, meas_id)
        if meas is None:
            return
        param = self._current_parameter()
        dlg = MeasurementDialog(
            self._session, self._part_id, param, measurement=meas, parent=self
        )
        if dlg.exec():
            self._load_measurements()

    def _on_delete_measurement(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Информация", "Выберите измерение.")
            return
        meas_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        meas = self._session.get(Measurement, meas_id)
        if meas is None:
            return
        answer = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранное измерение?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._session.delete(meas)
            self._session.commit()
            self._load_measurements()

    # ------------------------------------------------------------------
    def _on_update_forecast(self):
        param = self._current_parameter()
        if param is None:
            self._plot_widget.clear_plot()
            return

        measurements = (
            self._session.query(Measurement)
            .filter(
                Measurement.part_id == self._part_id,
                Measurement.parameter_id == param.id,
            )
            .order_by(Measurement.hours)
            .all()
        )

        if len(measurements) < 2:
            self._plot_widget.clear_plot()
            self._status_label_param.setText("Недостаточно данных для прогноза")
            self._status_label_critical.setText("")
            return

        hours = [m.hours for m in measurements]
        values = [m.value for m in measurements]

        # Get or create forecast settings
        settings = param.forecast_settings
        if settings is None:
            settings = ForecastSettings(parameter_id=param.id)
            self._session.add(settings)
            self._session.commit()
            self._session.refresh(param)
            settings = param.forecast_settings

        # Fit LSM
        try:
            popt, pcov, lsm_func = forecast_service.fit_lsm(
                hours, values, settings.lsm_function_type
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Ошибка МНК",
                f"Не удалось подобрать кривую МНК:\n{exc}",
            )
            self._plot_widget.clear_plot()
            return

        # Extended x range for plotting
        x_max = max(hours) * 1.5
        critical_hours_lsm = forecast_service.find_critical_hours_lsm(
            lsm_func, popt, param.critical_value, param.is_decreasing
        )
        if critical_hours_lsm is not None:
            x_max = max(x_max, critical_hours_lsm * 1.1)
        x_extended = np.linspace(min(hours), x_max, 300)

        # Fit GPR
        try:
            gpr = forecast_service.fit_gpr(hours, values, settings)
            gpr_mean, gpr_lower, gpr_upper = forecast_service.predict_gpr(
                gpr, x_extended, settings.confidence_level
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Ошибка GPR",
                f"Не удалось обучить GPR:\n{exc}",
            )
            self._plot_widget.clear_plot()
            return

        self._plot_widget.update_plot(
            hours=hours,
            values=values,
            lsm_func=lsm_func,
            popt=popt,
            gpr_mean=gpr_mean,
            gpr_lower=gpr_lower,
            gpr_upper=gpr_upper,
            x_extended=x_extended,
            critical_value=param.critical_value,
            parameter_name=param.name,
            unit=param.unit or "",
        )

        # Update status labels
        if critical_hours_lsm is not None:
            self._status_label_param.setText(
                f"По параметру '{param.name}': достигнет критического значения "
                f"через ~{critical_hours_lsm:.0f} ч. наработки"
            )
        else:
            self._status_label_param.setText(
                f"По параметру '{param.name}': "
                "критическое значение не достигается в заданном диапазоне"
            )

        # Find most critical parameter across all parameters
        self._update_most_critical_label()

    def _update_most_critical_label(self):
        """Find which parameter will reach its critical value soonest."""
        min_hours = None
        min_param_name = None

        for param in self._part.template.parameters:
            measurements = (
                self._session.query(Measurement)
                .filter(
                    Measurement.part_id == self._part_id,
                    Measurement.parameter_id == param.id,
                )
                .order_by(Measurement.hours)
                .all()
            )
            if len(measurements) < 2:
                continue

            hours = [m.hours for m in measurements]
            values = [m.value for m in measurements]

            settings = param.forecast_settings
            if settings is None:
                continue

            try:
                popt, _, lsm_func = forecast_service.fit_lsm(
                    hours, values, settings.lsm_function_type
                )
                crit_h = forecast_service.find_critical_hours_lsm(
                    lsm_func, popt, param.critical_value, param.is_decreasing
                )
            except Exception:
                continue

            if crit_h is not None:
                if min_hours is None or crit_h < min_hours:
                    min_hours = crit_h
                    min_param_name = param.name

        if min_hours is not None:
            self._status_label_critical.setText(
                f"Наиболее критичный параметр: '{min_param_name}' — "
                f"через ~{min_hours:.0f} ч. наработки"
            )
        else:
            self._status_label_critical.setText(
                "Наиболее критичный параметр: нет данных"
            )

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self._session.close()
        super().closeEvent(event)
