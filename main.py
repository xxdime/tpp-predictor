import sys
from PySide6.QtWidgets import QApplication
from app.database.engine import init_db
from app.views.main_window import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("TPP Predictor")
    app.setOrganizationName("TPP")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
