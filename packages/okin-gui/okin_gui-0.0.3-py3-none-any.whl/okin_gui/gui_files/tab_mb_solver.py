import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QComboBox, QFileDialog, QPushButton,QHBoxLayout,QVBoxLayout

from scipy.optimize import minimize, differential_evolution
import matplotlib.pyplot as plt
import os, logging
import pandas as pd
import numpy as np

from okin_gui.gui_files.wgt_save import SavingWidget
from okin_gui.gui_files.wgt_table import TableWidget
from okin_gui.gui_files.wgt_df import DataFrameWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.utils.convert_to_df import load_file_to_df
from okin_gui.utils.storage_paths import temp_file_path
from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_logger import chem_logger



class MBSolverTab(QMainWindow):
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__()
        self.setWindowTitle("Mass Balance Solver")
        self.mb_settings = {"to_sum": {"QElem": "", "value": ""}, "algo": {"QElem": "", "value": ""}}
        self.mb_outputs = {"total_error": {"QElem": "", "value": ""}, "algo": {"QElem": "", "value": ""}}
        self.img_path = f"{temp_file_path}\\MBSolver.png"
        self.results_df = None
        self.setup_ui()

    def setup_ui(self):
        mb_tab = QWidget()
        self.setCentralWidget(mb_tab)
        mb_lyt = QVBoxLayout(mb_tab)
        self.resize(800, 600)
         
        input_layout = QHBoxLayout()

        table_list = [{"name": "CSV file", "width_%": 0.7, "enable_dragdrop": True}, {"name": "Max. Concentration", "width_%": 0.3, "enable_dragdrop": False}]
        self.table = TableWidget(table_list=table_list, allow_edit=True)
        self.table.new_selected.connect(self.on_new_selected)
        self.table.double_click_trigger.connect(self.display_selected)

        input_wgt = self.get_input_wgt()
        input_layout.addWidget(self.table, 7)
        input_layout.addWidget(input_wgt, 3)

        solve_b = QPushButton("Solve")
        solve_b.clicked.connect(self.solve)

        output_lyt = self.get_ouput_lyt()
        output_lyt.setContentsMargins(400, 0, 400, 0)
        output_lyt.setAlignment(Qt.AlignCenter)

        self.img_wgt = ImageWidget(parent=mb_lyt, initial_width=1500)
        self.save_wgt = SavingWidget(parent=self, button_names=["Save Selected", "Save Image", "Save All"])
        self.save_wgt.custom_save_b.clicked.connect(self.save_all)

        mb_lyt.addLayout(input_layout)
        mb_lyt.addWidget(solve_b)
        mb_lyt.addLayout(output_lyt)
        mb_lyt.addWidget(self.img_wgt)
        mb_lyt.addWidget(self.save_wgt)

    def get_input_wgt(self):
        lyt = QVBoxLayout()
        
        to_sum_l = QLabel("To sum:")
        to_sum_ql = QLineEdit("[SM], [P]")

        algo_l = QLabel("Algorithm")
        algo_cb = QComboBox()
        algo_cb.addItems(["local", "global"])

        wgts = []
        wgts.append(to_sum_ql)
        wgts.append(algo_cb)

        labels = []
        labels.append(to_sum_l)
        labels.append(algo_l)
                
        for lbl, wgt, key in zip(labels, wgts, self.mb_settings.keys()):
            h_lyt = QHBoxLayout()
            lbl.setFixedWidth(61)
            wgt.setFixedWidth(90)
            h_lyt.addWidget(lbl)
            h_lyt.addWidget(wgt)
            lyt.addLayout(h_lyt)

            self.mb_settings[key]["QElem"] = wgt

        # eps_table_list = [{"name": "Species", "width_%": 0.5, "enable_dragdrop": False}, {"name": "ε", "width_%": 0.5, "enable_dragdrop": False}]
        # self.eps_table = TableWidget(table_list=eps_table_list, num_row=3)
        self.eps_results = DataFrameWidget(round_to=10)
        # self.eps_table.MAGIC_TABLE_PADDING = 138
        self.eps_results.setFixedSize(170, 140)
        # self.eps_table.move(50, 50)

        lyt.addWidget(self.eps_results)
        # self.table = TableWidget(table_list=table_list, allow_edit=True)


        lyt.addStretch(1)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.setSpacing(0)


        wgt = QWidget()
        wgt.setLayout(lyt)
        # self.read_detector_values()


        return wgt

    def get_ouput_lyt(self):
        layout = QHBoxLayout()
        func_l = QLabel("Error")
        func_ql = QLineEdit("")
        func_ql.setFixedWidth(200)


        layout.addWidget(func_l)
        layout.addWidget(func_ql)
        # layout.addWidget(r2_l)
        # layout.addWidget(r2_ql)

        self.mb_outputs["total_error"]["QElem"] = func_ql
        # self.mb_outputs["r2"]["QElem"] = r2_ql

        return layout

    def solve(self):
        self.set_dict_values()
        self.to_sum = [s.strip() for s in self.mb_settings["to_sum"]["value"].split(",")]
        algo = self.mb_settings["algo"]["value"]

        self.max_concs, self.dfs = self.read_data()
        # time,SM,P


        best_guess = np.full(len(self.to_sum), 0.1)
        if algo == "local":
            self.result = minimize(self.mass_balance_error, best_guess, method="Nelder-Mead", tol=10e-6)

        elif algo == "global":
            # magic numbers ftw
            max_k = 200_000
            bounds = [(0, max(2, max_k))] * len(self.to_sum)
            self.result = differential_evolution(self.mass_balance_error, bounds=bounds, x0=best_guess, atol=10e-3)

        self.create_result_df()

        self.display_selected()

        self.update_eps()

    def update_eps(self):
        eps_df = pd.DataFrame()
        eps_df["species"] = self.to_sum
        eps_df["ε"] = self.result["x"]
        # someone explain why: pd.DataFrame(my_dict) is not working here??


        self.eps_results.set_data_frame(eps_df)

    def read_data(self):
        table_df = self.table.get_df()
        max_concs = table_df["Max. Concentration"].astype(float)
        csv_files = table_df["CSV file"]

        dfs = []
        for path in csv_files:
            df = load_file_to_df(path)
            dfs.append(df)
        
        return max_concs, dfs

    def set_dict_values(self):
        for key, wgt_dct in self.mb_settings.items():
            widget = wgt_dct["QElem"]
            if isinstance(widget, QComboBox):
                val = widget.currentText()
            else:
                val = widget.text()

            self.mb_settings[key]["value"] = val
        print(self.mb_settings)

    def transform_to_conc(self, df):
        for s, e in zip(self.to_sum, self.result["x"]):
            # print(f"{s=}, {e=}")
            for header in df.columns:
                if s == header:
                    df[header] = df[header] * e
        return df
    
    def display_selected(self):
        if self.results_df is None:
            return
        df = self.results_df # just to type less. it doesnt get modified.

        eps = self.result["x"]   
        for s, e in zip(self.to_sum, eps):
            for header in df.columns:
                if s == header and not s.endswith("_area"):
                    plt.scatter(df["time"], df[header], label=f"{header}")


        plt.scatter(df["time"], df["mass_balance"], label="Mass Balance", color="black")

        total_error = self.mass_balance_error(epsilons=eps)
        error_str = str(float(f"{total_error:.5g}"))
        self.mb_outputs["total_error"]["QElem"].setText(error_str)
        self.mb_outputs["total_error"]["value"] = total_error


        plt.xlabel("time")
        plt.ylabel("concentration")
        plt.legend()
        apply_acs_layout()
        plt.savefig(self.img_path, bbox_inches="tight")
        plt.clf()
        self.img_wgt.set_image_path(self.img_path)

    def save_all(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.logger.debug("Selected folder:", folder_path)
       
            csv_files = self.table.get_df()["CSV file"]

            for path, df in zip(csv_files, self.dfs):
                csv_name = os.path.basename(path)
                conc_df = self.transform_to_conc(df)
                conc_df.to_csv(f"{folder_path}/{csv_name}_conc.csv", index=False)
                
    def create_result_df(self):
        # make all conc
        conc_df = self.transform_to_conc(self.df.copy())
        conc_cols = [col for col in conc_df if not col.startswith("time")]
        conc_df = conc_df[conc_cols]

        area_df = self.df.copy()
        area_cols = {col: col + '_area' for col in area_df.columns if not col.startswith("time")}
        area_df.rename(columns=area_cols, inplace=True)

        self.results_df = pd.DataFrame()
        self.results_df = pd.concat([conc_df, area_df], axis=1)
        self.results_df["mass_balance"] = self.results_df[conc_cols].sum(axis=1)


    def mass_balance_error(self, epsilons):
        total_error = 0

        for i in range(len(self.dfs)):
            df = self.dfs[i].copy(deep=True)
            # true mass balance
            true_mb = self.max_concs[i]

            # multiply all concentrations wtih their respective best guess epsilon
            for j, species in enumerate(self.to_sum):
                # e.g. df["A"] = df["A"] * epsilon_A
                df[species] = df[species]*epsilons[j]

            # everything is now in concentration. Sum all species that should be added 
            sum_col_name = "".join(self.to_sum) # this should get smth like ABP if A, B and P are summed)
            df[sum_col_name] = df[self.to_sum].sum(axis=1)

            # Calculate r2
            error = ((df[sum_col_name] - true_mb) ** 2).sum()
            # print(error)
            total_error += error

            # df.drop(sum_col_name, axis=1, inplace=True)
        self.logger.info(f"{total_error=}, {epsilons=}\n_______________________")
        return total_error
            
    @Slot(list)
    def on_new_selected(self, selected_row):
        self.curr_row = selected_row
        self.logger.debug(f"Received {selected_row = }")
        try:
            df = load_file_to_df(selected_row[0])
        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            df = pd.DataFrame()

        self.df = df
        # self.get_species()

if __name__ == "__main__":

    
    app = QApplication(sys.argv)
    window = MBSolverTab()
    window.setup_ui()
    window.show()

    sys.exit(app.exec())