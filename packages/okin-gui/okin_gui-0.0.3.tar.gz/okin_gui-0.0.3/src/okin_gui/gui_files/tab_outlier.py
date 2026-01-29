from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout
from PySide6.QtCore import  Slot, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit
from PySide6.QtWidgets import QWidget,QSpinBox,QPushButton,QHBoxLayout,QVBoxLayout, QComboBox
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from okin_gui.gui_files.wgt_df import DataFrameWidget
from okin_gui.gui_files.wgt_table import TableWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.gui_files.wgt_save import SavingWidget
from okin_gui.utils.convert_to_df import load_file_to_df
from okin_gui.utils.storage_paths import temp_file_path
from okin.base.chem_logger import chem_logger
from okin.base.chem_plot_utils import apply_acs_layout

class OutlierTab(QMainWindow):
    changed_csv = Signal(pd.DataFrame)
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.outlier_settings = {"to_plot": {"QElem": "", "value": ""}, "species": {"QElem": "", "value": ""}, "detector": {"QElem": "", "value": ""}, "window": {"QElem": "", "value": ""}, "thresh": {"QElem": "", "value": ""}}
        self.img_path = f"{temp_file_path}\data_widget.png"

        self.setup_ui()
               
    def setup_ui(self):
        outlier_tab = QWidget()
        self.setCentralWidget(outlier_tab)
        outlier_lyt = QVBoxLayout(outlier_tab)
               
        # input layout
        input_lyt = QHBoxLayout()
        
        table_list = [{"name": "csv_file", "width_%": 0.97, "enable_dragdrop": True}]
        self.csv_wgt = TableWidget(table_list=table_list, num_row=5)
        self.csv_wgt.MAGIC_TABLE_PADDING = 0

        self.csv_wgt.new_selected.connect(self.on_new_selected)
        self.csv_wgt.double_click_trigger.connect(self.run_outlier)

        selector_wgt = self.get_selector_wgt()
        
        input_lyt.addWidget(self.csv_wgt, stretch=7.5)
        input_lyt.addWidget(selector_wgt, 2.5)

        run_data_b = QPushButton("Plot")
        run_data_b.clicked.connect(self.run_outlier)
        
        self.img_wgt = ImageWidget(parent=outlier_lyt, initial_width=1000)
        self.img_wgt.setStyleSheet("background-color: (12, 24, 100, 128)")

        self.save_wgt = SavingWidget(parent=self, button_names=["Save Data without Outliers", "Save Image"])

        outlier_lyt.addLayout(input_lyt)
        outlier_lyt.addWidget(run_data_b)
        outlier_lyt.addWidget(self.img_wgt)
        outlier_lyt.addWidget(self.save_wgt)

    def get_raw_data_tab(self):
        raw_data_tab = QWidget()
        raw_data_layout = QVBoxLayout(raw_data_tab)
        
        # __NEXT TAB__ Create and add DataFrameWidget to the "Raw Data" tab
        self.results = DataFrameWidget()
        raw_data_layout.addWidget(self.results)
        return raw_data_tab

    def get_selector_wgt(self):
        selector_lyt = QVBoxLayout()
        
        to_plot_l = QLabel("To Plot:")
        to_plot_ql = QLineEdit("all")

        outlier_species_l = QLabel("Outlier for:")
        outlier_species_ql = QLineEdit("")

        detector_l = QLabel("Detector")
        detector_cb = QComboBox()
        detector_cb.addItems(["euclidean", "z-score"])

        window_l = QLabel("Window:")
        window_sb = QSpinBox()
        window_sb.setRange(0, 100)  # Set the range of values
        window_sb.setValue(5)

        thresh_l = QLabel("Threshhold:")
        thresh_ql = QLineEdit("0.05")

        wgts = []
        wgts.append(to_plot_ql)
        wgts.append(outlier_species_ql)
        wgts.append(detector_cb)
        wgts.append(window_sb)
        wgts.append(thresh_ql)

        labels = []
        labels.append(to_plot_l)
        labels.append(outlier_species_l)
        labels.append(detector_l)
        labels.append(window_l)
        labels.append(thresh_l)
                
        for lbl, wgt, key in zip(labels, wgts, self.outlier_settings.keys()):
            h_lyt = QHBoxLayout()
            lbl.setFixedWidth(61)
            wgt.setFixedWidth(90)
            h_lyt.addWidget(lbl)
            h_lyt.addWidget(wgt)
            selector_lyt.addLayout(h_lyt)

            self.outlier_settings[key]["QElem"] = wgt

        selector_lyt.addStretch(1)
        selector_lyt.setContentsMargins(0, 0, 0, 0)
        selector_lyt.setSpacing(0)

        selector_wgt = QWidget()
        selector_wgt.setLayout(selector_lyt)
        self.set_dict_values()
        return selector_wgt

    def set_dict_values(self):
        for key, wgt_dct in self.outlier_settings.items():
            widget = wgt_dct["QElem"]
            if isinstance(widget, QComboBox):
                val = widget.currentText()
            else:
                val = widget.text()

                if key == "window" or key == "thresh":
                    val = float(val)
                
            self.outlier_settings[key]["value"] = val

    def parse_str_to_list(self, list_str):
        # empty list = all species
        if not list_str:
            list_str = "all"

        if list_str == "all":
            list_ = [s for s in self.df.columns if not s.startswith("time") and not s.endswith("Outlier")]
        else:
            list_ = [s.strip() for s in list_str.split(",")]
        return list_

    def run_outlier(self):  
        self.logger.debug(f"run_outlier is triggered.")
        self.set_dict_values()

        self.outlier_species = self.parse_str_to_list(self.outlier_settings["species"]["value"]) 
        self.to_plot = self.parse_str_to_list(self.outlier_settings["to_plot"]["value"]) 
        rolling_window = int(self.outlier_settings["window"]["value"] )
        method = self.outlier_settings["detector"]["value"]     
        thresh = self.outlier_settings["thresh"]["value"] 

        filtered_columns = ["time"] + [col for col in self.df.columns if col in self.outlier_species] 
        self.df = self.df[filtered_columns]

        if method == "z-score":
            self.moving_z_score_outliers(rolling_window=rolling_window, threshold=thresh)

        elif method == "euclidean":
           self.distances(threshold=thresh)

        # print(self.df)
        self.plot_species()
        self.create_results_df()

    def moving_z_score_outliers(self, rolling_window, threshold=0.5):
        for species in self.outlier_species:
            data = self.df[species]
            data = data / data.max()
            r = data.rolling(window=rolling_window)
            m = r.mean().shift(1)
            s = r.std(ddof=0).shift(1)
            z = ((data - m) / s).abs()
            mask = z > threshold
            self.df[f"{species}_isOutlier"] = mask.astype(bool)

    def distances(self, threshold=0.03):
        for species in self.outlier_species:
            data = self.df[species]
            # Convert to a Pandas Series
            data = data / data.max()

            left_distances = np.abs(np.diff(data, prepend=data.iloc[0]))
            right_distances = np.abs(np.diff(data, append=data.iloc[-1]))

            mask = (left_distances > threshold) & (right_distances > threshold)
            self.df.loc[:, f"{species}_isOutlier"] = mask.astype(bool)

    def plot_species(self):
        print(f"{self.to_plot = }")
        # Iterate over each species in self.to_plot
        for species in self.to_plot:
            # Plot the species values
            plt.scatter(self.df["time"], self.df[species], label=species)
            
            # Check if an outlier mask exists for the current species
            outlier_column = f"{species}_isOutlier"
            if outlier_column in self.df.columns:
                # Get the outlier mask
                outlier_mask = self.df[outlier_column]
                
                # Plot outliers in red
                plt.scatter(self.df["time"][outlier_mask], self.df[species][outlier_mask], color='red')

        # Set plot labels and legend
        plt.xlabel("Time")
        plt.ylabel("Value")
        apply_acs_layout()
        plt.savefig(self.img_path, dpi=500)
        plt.clf()
        self.img_wgt.set_image_path(self.img_path)
    
    @Slot(list)
    def on_new_selected(self, selected_row):
        self.logger.debug(f"Received {selected_row = }")
        try:
            df = load_file_to_df(selected_row[0])
        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            df = pd.DataFrame()

        self.changed_csv.emit(df)
        self.df = df
            
    def create_results_df(self):
        filtered_dfs = []

        for column in self.df.columns:
            # Check if the column name contains "_isOutlier" indicating it's a mask header
            if column.endswith("_isOutlier"):
                # Get the§ corresponding original header name
                species = column.split("_")[0]
                # Filter the original data based on the mask
                filtered_df = self.df.loc[~self.df[column].astype(bool), [species]]

                # Add the filtered DataFrame to the list
                filtered_dfs.append(filtered_df)
                print(filtered_df.columns)
            if column.startswith("time"):
                filtered_dfs.append(self.df["time"])

        # Concatenate the filtered DataFrames along columns
        self.results_df = pd.concat(filtered_dfs, axis=1)
        # # Save the combined DataFrame to a CSV file
        # combined_df.to_csv('filtered_data.csv', index=False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OutlierTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())