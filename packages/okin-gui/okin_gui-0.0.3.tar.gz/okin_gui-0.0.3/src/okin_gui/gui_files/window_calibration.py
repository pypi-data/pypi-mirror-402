from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout
import sys
from okin_gui.gui_files.tab_mb_solver import MBSolverTab
from okin_gui.gui_files.tab_calibration import CalibrationTab
from okin.base.chem_logger import chem_logger

class ConversionTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Conversion")
               
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        mb_tab = MBSolverTab()
        ph_tab = CalibrationTab()

        tab_widget.addTab(mb_tab, "Mass Balance Solver")
        tab_widget.addTab(ph_tab, "Placeholder")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)
        self.resize(1024, 720)
        self.logger.debug("setup conversion ui")

        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConversionTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())