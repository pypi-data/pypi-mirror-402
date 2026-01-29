from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout
import sys

from okin.base.chem_logger import chem_logger
from okin_gui.gui_files.tab_sim import SimulationTab
from okin_gui.gui_files.wgt_sb_string import SbStringWidget

class SimulationTab_(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Simulation")
               
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        sim_tab = SimulationTab() # simulation input
    
        sb_tab = SbStringWidget() # Sb string to edit

        # inf_tab = ModernKineticsLayout() # data set generator
        # inf_tab.setup_ui()

        sim_tab.get_sb.connect(sb_tab.set_sb_string)
        sb_tab.sb_change.connect(sim_tab.update_sb_string)

        tab_widget.addTab(sim_tab, "Simulator")
        tab_widget.addTab(sb_tab, "Sb String")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)
        self.logger.debug("setup sim ui")
        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimulationTab_()
    window.setup_ui()
    window.resize(1000, 850)
    window.show()

    sys.exit(app.exec())