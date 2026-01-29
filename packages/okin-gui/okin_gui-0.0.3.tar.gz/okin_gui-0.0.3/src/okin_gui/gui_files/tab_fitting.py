from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QSpinBox, QPushButton, QHBoxLayout, QVBoxLayout, QComboBox

import sys
from math import e
import re
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
from scipy.optimize import curve_fit, OptimizeWarning

from okin_gui.gui_files.wgt_table import TableWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.gui_files.wgt_save import SavingWidget
from okin_gui.utils.custom_r2 import calculate_r_squared
from okin_gui.utils.convert_to_df import load_file_to_df
from okin.base.chem_logger import chem_logger
from okin.base.chem_plot_utils import apply_acs_layout

from okin_gui.utils.storage_paths import temp_file_path


class FittingTab(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.fitting_func_dict = {"exponential": "a * exp(b * t)", "sigmoidal": "a / (1 + exp(-b * (t - c)))", "linear": "m * t + b", "n-th poly": "", "custom": ""}
        self.fitting_settings = {"species": {"QElem": "", "value": ""}, "func_type": {"QElem": "", "value": ""}, "func": {"QElem": "", "value": ""}, "nth_poly": {"QElem": "", "value": ""}, "symbol_func": {"QElem": "", "value": ""}}
        self.fitting_outputs = {"r2": {"QElem": "", "value": ""}, "fitted_func": {"QElem": "", "value": ""}}
        self.img_path = f"{temp_file_path}\\fitting.png"
        self.maxfev = 20000
        self.setup_ui()
        
        
    def setup_ui(self):
        fitting_tab = QWidget()
        self.setCentralWidget(fitting_tab)
        fitting_lyt = QVBoxLayout(fitting_tab)

        # # input layout
        input_lyt = QHBoxLayout()
        table_list = [{"name": "csv_file", "width_%": 0.97, "enable_dragdrop": True}]
        self.csv_wgt = TableWidget(table_list=table_list, num_row=5)
        self.csv_wgt.MAGIC_TABLE_PADDING = 0

        self.csv_wgt.new_selected.connect(self.on_new_selected)
        self.csv_wgt.double_click_trigger.connect(self.run_fitting)

        txt_input_wgt = self.get_fitting_input_wgt()
        
        input_lyt.addWidget(self.csv_wgt, stretch=7.5)
        input_lyt.addWidget(txt_input_wgt, 2.5)

        run_fitting_b = QPushButton("Do Math")
        run_fitting_b.clicked.connect(self.run_fitting)
        
        # results_lyt = QHBoxLayout()
        result_lyt = self.get_output_lyt()
        result_lyt.setContentsMargins(200, 0, 200, 0)
        result_lyt.setAlignment(Qt.AlignCenter)
        
        # img_layout = QVBoxLayout()
        self.img_wgt = ImageWidget(parent=fitting_lyt, initial_width=1000)
        self.save_wgt = SavingWidget(parent=self, button_names=["Save Fitting Results", "Save Image"])

        fitting_lyt.addLayout(input_lyt)
        fitting_lyt.addWidget(run_fitting_b)
        fitting_lyt.addLayout(result_lyt)
        fitting_lyt.addWidget(self.img_wgt)
        fitting_lyt.addWidget(self.save_wgt)
        self.update_func()
        return fitting_tab

    def get_species(self):
        self.fitting_settings["species"]["QElem"].clear()
        now_cols = [c for c in self.fitting_df.columns if not c.startswith("time")]
        self.fitting_settings["species"]["QElem"].addItems(now_cols)
    
    def get_output_lyt(self):
        layout = QHBoxLayout()
        func_l = QLabel("c(t) =")
        func_ql = QLineEdit("")
        func_ql.setFixedWidth(400)
        func_ql.returnPressed.connect(self.func_change)

        r2_l = QLabel("r2")
        r2_ql = QLineEdit("0")
        r2_ql.setReadOnly(True)
        # r2_ql.setFixedWidth(40)


        layout.addWidget(func_l)
        layout.addWidget(func_ql)
        layout.addWidget(r2_l)
        layout.addWidget(r2_ql)

        self.fitting_outputs["fitted_func"]["QElem"] = func_ql
        self.fitting_outputs["r2"]["QElem"] = r2_ql

        return layout

    def func_change(self):
        self.logger.debug(f"func_change is triggered.")

        species = self.fitting_settings["species"]["value"]
        time_column = [col for col in self.fitting_df.columns if col.startswith('time')][0]
        ts = np.array(self.fitting_df[time_column]).copy() / self.fitting_df[time_column].max()
        ys = np.array(self.fitting_df[species]).copy() / self.fitting_df[species].max()

        fitted_func_str = self.fitting_outputs["fitted_func"]["QElem"].text()
        self.fitting_outputs["fitted_func"]["value"] = fitted_func_str 

        fitted_func, _ = self.generate_lambda(fitted_func_str)
        ys_fitted = np.array([fitted_func(t) for t in ts])

        self.fitting_df[f"{species} = {fitted_func_str}"] = ys_fitted * self.fitting_df[species].max()

        r2 = round(calculate_r_squared(ys, ys_fitted), 8)
        self.fitting_outputs["r2"]["QElem"].setText(str(r2))
        self.fitting_outputs["r2"]["value"] = r2
        # plot results
        self.plot_fitting_results(ts=ts, ys=ys, ys_fitted=ys_fitted)

        self.create_results_df()

    def get_fitting_input_wgt(self):
        fitting_lyt = QVBoxLayout()
        
        species_l = QLabel("Species")
        species_cb =  QComboBox()

        func_type_l = QLabel("Type")
        func_type_cb =  QComboBox()
        func_type_cb.addItems(self.fitting_func_dict.keys())

        nth_poly_l = QLabel("n = ")
        nth_poly_sb = QSpinBox()
        nth_poly_sb.setRange(0, 9)  # Set the range of values
        nth_poly_sb.setValue(3)

        func_l = QLabel("c(t) =")
        func_ql = QLineEdit("")
        func_ql.setReadOnly(True)

        sym_func_l = QLabel("c(t, …) =")
        sym_func_ql = QLineEdit("Do not use.")

        # connections
        func_type_cb.currentIndexChanged.connect(self.update_func)
        nth_poly_sb.valueChanged.connect(self.update_func)


        # populate layout
        labels = []
        labels.append(species_l)
        labels.append(func_type_l)
        labels.append(nth_poly_l)
        labels.append(func_l)
        labels.append(sym_func_l)

        wgts = []
        wgts.append(species_cb)
        wgts.append(func_type_cb)
        wgts.append(nth_poly_sb)
        wgts.append(func_ql)
        wgts.append(sym_func_ql)

        keys = ["species", "func_type", "nth_poly", "func", "symbol_func"]

        for lbl, wgt, key in zip(labels, wgts, keys):
            h_lyt = QHBoxLayout()
            lbl.setFixedWidth(40)
            wgt.setFixedWidth(170)
            h_lyt.addWidget(lbl)
            h_lyt.addWidget(wgt)
            fitting_lyt.addLayout(h_lyt)

            self.fitting_settings[key]["QElem"] = wgt

        fitting_lyt.addStretch(1)
        fitting_lyt.setContentsMargins(0, 0, 0, 0)
        fitting_lyt.setSpacing(0)

        fitting_wgt = QWidget()
        fitting_wgt.setLayout(fitting_lyt)

        return fitting_wgt

    def update_func(self):
        self.set_dict_values(self.fitting_settings)

        func_type = self.fitting_settings["func_type"]["value"]
        if func_type == "custom":
            self.fitting_settings["func"]["QElem"].setReadOnly(False)
            return
        
        elif func_type == "n-th poly":
            nth_poly = int(self.fitting_settings["nth_poly"]["value"])
            func_str = " + ".join([f"a{n}*t**{n}" for n in range(nth_poly, -1, -1)])

        else:
            func_str = self.fitting_func_dict[func_type]

        self.fitting_settings["func"]["QElem"].setText(func_str)

    def set_dict_values(self, settings_dict):
        for key, wgt_dct in settings_dict.items():
            widget = wgt_dct["QElem"]

            if isinstance(widget, QComboBox):
                val = widget.currentText()
            else:
                val = widget.text()
            settings_dict[key]["value"] = val

    def run_fitting(self):  
        self.logger.debug(f"run_fitting is triggered.")
        self.read_curr_csv()
        self.set_dict_values(self.fitting_settings)

        species = self.fitting_settings["species"]["value"]
        func_str = self.fitting_settings["func"]["value"]
        time_column = [col for col in self.fitting_df.columns if col.startswith('time')][0]

        ts = np.array(self.fitting_df[time_column]).copy() / self.fitting_df[time_column].max()
        ys = np.array(self.fitting_df[species]).copy() / self.fitting_df[species].max()


        # create lambda function from string
        lamb_func, vars = self.generate_lambda(eq_str=func_str)

        # fit function
        with warnings.catch_warnings():
            warnings.simplefilter("error", OptimizeWarning)
            try:
                popt, _ = curve_fit(lamb_func, ts, ys, maxfev=self.maxfev)
                ys_fitted = [lamb_func(t, *popt) for t in ts]
                self.fitting_outputs["r2"]["QElem"].setStyleSheet(f"background-color: rgba(255, 255, 255, 25);")
            except OptimizeWarning:
                self.fitting_outputs["fitted_func"]["QElem"].setText("Function to far from data.")
                return

            except RuntimeError:
                self.fitting_outputs["r2"]["QElem"].setText("-∞")
                self.fitting_outputs["r2"]["QElem"].setStyleSheet(f"background-color: rgba(255, 0, 0, 25);")

        # update results section
        self.update_fitting_results(ys, ys_fitted, func_str=func_str, popt=popt, vars=vars)
        
    def update_fitting_results(self, ys, ys_fitted, func_str, popt, vars):
        # r2 = round(calculate_r_squared(ys, ys_fitted), 8)
        for var_, p in zip(vars, popt):
            p = round(p, 4)
            func_str = func_str.replace(str(var_), str(p))
        
        func_str = func_str.replace("- -", "+").replace("--", "+").replace("- +", "-").replace("+ -", "-").replace("+ +", "+").replace("+ +", "+").replace("-+", "-").replace("+-", "-")

        self.fitting_outputs["fitted_func"]["value"] = func_str
        self.fitting_outputs["fitted_func"]["QElem"].setText(func_str)
        self.func_change()
        
    def plot_fitting_results(self, ts, ys, ys_fitted):
        plt.scatter(ts, ys, label='Original Data')
        plt.plot(ts, ys_fitted, label='Fitted Curve', color='red')
        plt.xlabel('time')
        plt.ylabel(self.fitting_settings["species"]["value"])
        apply_acs_layout()
        plt.savefig(self.img_path)
        self.img_wgt.set_image_path(self.img_path)
        plt.clf()
    
    def read_curr_csv(self):
        try:
            df = load_file_to_df(self.fitting_curr_row[0])
        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            df = pd.DataFrame()

        self.fitting_df = df

    @Slot(list)
    def on_new_selected(self, selected_row):
        self.fitting_curr_row = selected_row
        self.logger.debug(f"Received {selected_row = }")
        try:
            df = load_file_to_df(selected_row[0])
        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            df = pd.DataFrame()

        self.fitting_df = df
        self.get_species()
   
    def create_results_df(self):
        self.results_df = self.fitting_df.copy()

    def generate_lambda(self, eq_str):
        # this is absolutely insane.
        eq_str = eq_str.replace("exp", f"{e}^").replace("e", str(e)).replace("^", "**")

        # Find all variables in the equation string
        variables = [v for v in set(re.findall(r'\b(?<!\bx\b)[a-zA-Z]\w{0,1}\b', eq_str)) if v != "t"]
        variables_str = ', '.join(variables)
        lambda_str = f"lambda t, {variables_str}: {eq_str}"
        print(lambda_str)
        return eval(lambda_str), variables



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FittingTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())