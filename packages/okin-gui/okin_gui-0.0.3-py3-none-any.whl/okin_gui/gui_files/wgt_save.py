from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from okin.base.chem_logger import chem_logger
import shutil

class SavingWidget(QWidget):
    KEY_WIDTH = 50

    def __init__(self, parent, button_names:list):
        self.button_names = button_names
        self.parent = parent
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.logger.debug(f"Setting up a SavingWidget.")

        layout = QHBoxLayout()
        
        self.save_csv_b = QPushButton(self.button_names[0])
        self.save_csv_b.clicked.connect(self.save_csv)

        self.save_img_b = QPushButton(self.button_names[1])
        self.save_img_b.clicked.connect(self.save_img)

       


        layout.addWidget(self.save_csv_b)
        layout.addWidget(self.save_img_b)

        if len(self.button_names) == 3:
            self.custom_save_b = QPushButton(self.button_names[2])
            layout.addWidget(self.custom_save_b)
            # self.save_csv_b.clicked.connect(self.save_csv)
           
        layout.setAlignment(Qt.AlignCenter)


        
        self.setLayout(layout)
        self.logger.debug("setup done")

    def save_csv(self):
        print(self.parent)
        options = QFileDialog.Options()
        # default_name = f"{self.parent.data_path}"
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV File", "data", "CSV Files (*.csv)", options=options)
        if file_name:
            self.parent.results_df.to_csv(file_name, index=False)
        
    def save_img(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image File", "image", "Images (*.png)", options=options)
        
        if file_name:
           shutil.copy(self.parent.img_path, file_name)
    

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Example usage
    info_dict = [
        {"key": "Key1", "value": 1.0, "val_width_px": 30},
        {"key": "Key2", "value": "hello cat", "val_width_px": 90},
        {"key": "Key3", "value": 3.0, "val_width_px": 40}
    ]
    left_to_right_widget = SavingWidget()
    left_to_right_widget.show()


    sys.exit(app.exec())
