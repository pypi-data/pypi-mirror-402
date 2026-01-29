from PySide6.QtWidgets import QWidget, QApplication, QMainWindow, QVBoxLayout

import sys
from okin_gui.gui_files.wgt_df import DataFrameWidget
from okin.base.chem_logger import chem_logger

class DataViewerWidget(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setWindowTitle("Data")
        self.setup_ui()
                       
    def setup_ui(self):
        raw_data_tab = QWidget()
        self.setCentralWidget(raw_data_tab)
        raw_data_lyt = QVBoxLayout(raw_data_tab)
      
        self.df_wgt = DataFrameWidget()
        raw_data_lyt.addWidget(self.df_wgt)

        self.setCentralWidget(raw_data_tab)

        self.logger.debug("setup data viewer widget")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataViewerWidget()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())