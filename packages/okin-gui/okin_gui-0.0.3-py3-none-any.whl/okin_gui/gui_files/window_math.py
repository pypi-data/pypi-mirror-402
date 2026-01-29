from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout,QTabWidget, QWidget

import sys

from okin.base.chem_logger import chem_logger
from okin_gui.gui_files.tab_fitting import FittingTab
from okin_gui.gui_files.tab_rate_eq import RateEquationTab

class MathTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Math")
        
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        fitting_tab = FittingTab()
        rate_eq_tab = RateEquationTab()

        tab_widget.addTab(fitting_tab, "c(t)")
        tab_widget.addTab(rate_eq_tab, "Steady-State Solver")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)
        self.logger.debug("setup math ui")
        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MathTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())