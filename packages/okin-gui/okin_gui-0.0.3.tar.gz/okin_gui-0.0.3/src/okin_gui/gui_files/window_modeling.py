from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout,QTabWidget, QWidget
import sys

from okin.base.chem_logger import chem_logger

from okin_gui.gui_files.wgt_sb_string import SbStringWidget
from okin_gui.gui_files.wgt_df import DataFrameWidget
from okin_gui.gui_files.tab_kopt import KOptTab

class ModelingTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()
        # self.setWindowTitle("KOpt")
        
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        modeling_tab = KOptTab()
        sb_tab = SbStringWidget()

        modeling_tab.get_sb.connect(sb_tab.set_sb_string)
        sb_tab.sb_change.connect(modeling_tab.update_sb_string)


        results_tab = DataFrameWidget(round_to=8)
        modeling_tab.set_results.connect(results_tab.set_data_frame) # if results are ready send them to the df tab
        results_tab.row_selected.connect(lambda r: modeling_tab.new_results_selected(results_row=r))

        tab_widget.addTab(modeling_tab, "k-Optimizer")
        tab_widget.addTab(sb_tab, "Sb String")
        tab_widget.addTab(results_tab, "k-values")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)

        self.logger.debug("setup KOpt ui")
        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModelingTab()
    window.setup_ui()
    window.resize(1000, 850)
    window.show()

    sys.exit(app.exec())