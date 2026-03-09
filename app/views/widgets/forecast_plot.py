import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class ForecastPlotWidget(QWidget):
    """Widget that displays measurement data together with LSM and GPR forecasts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._layout.addWidget(self._plot_widget)

        self._no_data_label = QLabel("Нет данных для отображения")
        self._no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setStyleSheet("font-size: 14px; color: gray;")
        self._layout.addWidget(self._no_data_label)

        self._plot_widget.hide()
        self._no_data_label.show()

        # Items that need cleanup between updates
        self._fill_item = None
        self._critical_line = None

    # ------------------------------------------------------------------
    def clear_plot(self):
        """Clear the plot and show the 'no data' label."""
        self._plot_widget.clear()
        # Items are already removed by clear(); just reset references
        self._fill_item = None
        self._critical_line = None
        self._plot_widget.hide()
        self._no_data_label.show()

    # ------------------------------------------------------------------
    def update_plot(
        self,
        hours,
        values,
        lsm_func,
        popt,
        gpr_mean,
        gpr_lower,
        gpr_upper,
        x_extended,
        critical_value,
        parameter_name: str,
        unit: str,
    ):
        """
        Render the plot with:
        - Scatter plot of raw measurements
        - LSM trend line (extended to critical value)
        - GPR confidence interval (shaded band)
        - GPR mean line (dashed cyan)
        - Horizontal dashed red line at critical_value
        """
        # Clean previous content — clear() removes all items including fill and infinite line
        self._plot_widget.clear()
        self._fill_item = None
        self._critical_line = None

        self._no_data_label.hide()
        self._plot_widget.show()

        plot = self._plot_widget
        plot.setLabel("bottom", "Часы наработки")
        y_label = parameter_name
        if unit:
            y_label = f"{parameter_name}, {unit}"
        plot.setLabel("left", y_label)
        plot.showGrid(x=True, y=True, alpha=0.3)

        legend = plot.addLegend()

        x_arr = np.asarray(hours, dtype=float)
        y_arr = np.asarray(values, dtype=float)
        x_ext = np.asarray(x_extended, dtype=float)

        # --- 1. GPR confidence interval (fill between) ---
        gpr_m = np.asarray(gpr_mean, dtype=float)
        gpr_lo = np.asarray(gpr_lower, dtype=float)
        gpr_hi = np.asarray(gpr_upper, dtype=float)

        curve_lower = plot.plot(
            x_ext, gpr_lo,
            pen=pg.mkPen(color=(100, 200, 255, 0)),
        )
        curve_upper = plot.plot(
            x_ext, gpr_hi,
            pen=pg.mkPen(color=(100, 200, 255, 0)),
        )
        self._fill_item = pg.FillBetweenItem(
            curve_lower, curve_upper,
            brush=pg.mkBrush(100, 200, 255, 60),
        )
        plot.addItem(self._fill_item)

        # Dummy item for legend entry for confidence interval
        legend.addItem(
            pg.PlotDataItem(pen=pg.mkPen(color=(100, 200, 255, 150), width=4)),
            "GPR доверительный интервал",
        )

        # --- 2. GPR mean line (dashed cyan) ---
        plot.plot(
            x_ext, gpr_m,
            pen=pg.mkPen(color=(0, 200, 255), width=2, style=Qt.PenStyle.DashLine),
            name="GPR среднее",
        )

        # --- 3. LSM trend line (solid blue) ---
        y_lsm = lsm_func(x_ext, *popt)
        plot.plot(
            x_ext, y_lsm,
            pen=pg.mkPen(color=(50, 100, 255), width=2),
            name="МНК тренд",
        )

        # --- 4. Critical value horizontal line ---
        self._critical_line = pg.InfiniteLine(
            pos=critical_value,
            angle=0,
            pen=pg.mkPen(color=(255, 60, 60), width=1.5, style=Qt.PenStyle.DashLine),
            label=f"Крит.: {critical_value}",
            labelOpts={"color": (255, 60, 60)},
        )
        plot.addItem(self._critical_line)
        legend.addItem(
            pg.PlotDataItem(
                pen=pg.mkPen(color=(255, 60, 60), width=1.5, style=Qt.PenStyle.DashLine)
            ),
            "Критическое значение",
        )

        # --- 5. Scatter plot of raw measurements (on top) ---
        scatter = pg.ScatterPlotItem(
            x=x_arr,
            y=y_arr,
            symbol="o",
            size=8,
            pen=pg.mkPen(color=(0, 0, 0), width=1),
            brush=pg.mkBrush(240, 240, 240, 220),
        )
        plot.addItem(scatter)
        legend.addItem(scatter, "Измерения")
