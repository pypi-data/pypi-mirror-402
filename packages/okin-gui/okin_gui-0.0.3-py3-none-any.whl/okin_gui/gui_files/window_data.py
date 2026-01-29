from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout

import sys

from okin_gui.gui_files.tab_outlier import OutlierTab
from okin_gui.gui_files.tab_viewer import DataViewerWidget
from okin.base.chem_logger import chem_logger

class DataTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        # self.setup_ui()
        self.setWindowTitle("Data")
               
    def setup_ui(self):
        layout_widget = QWidget()
        layout = QVBoxLayout(layout_widget)
        tab_widget = QTabWidget()

        outlier_tab = OutlierTab()
        raw_data_tab = DataViewerWidget()

        outlier_tab.changed_csv.connect(raw_data_tab.df_wgt.set_data_frame)
        
        tab_widget.addTab(outlier_tab, "Outlier")
        tab_widget.addTab(raw_data_tab, "Data Viewer")

        layout.addWidget(tab_widget)
        self.setCentralWidget(layout_widget)

        self.logger.debug("setup data tab")        
        return layout_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())