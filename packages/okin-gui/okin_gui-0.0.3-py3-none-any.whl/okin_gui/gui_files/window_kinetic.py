from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout
import sys

from okin.base.chem_logger import chem_logger
from okin_gui.gui_files.tab_modern_kinetic import ModernKineticsLayout

class KineticTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Kinetic")
               
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        mkin_tab = ModernKineticsLayout()

        tab_widget.addTab(mkin_tab, "Mass Balance Solver")
        # tab_widget.addTab(ph_tab, "Placeholder")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)

        self.logger.debug("setup data ui")
        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KineticTab()
    window.setup_ui()
    window.resize(1000, 900)
    window.show()

    sys.exit(app.exec())