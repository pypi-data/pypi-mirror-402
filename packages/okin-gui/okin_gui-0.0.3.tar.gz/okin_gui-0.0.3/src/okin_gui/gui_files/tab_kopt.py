import os.path
import sys, os, json

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel,QPushButton, QHBoxLayout,QVBoxLayout, QLineEdit, QSpinBox, QCheckBox, QFrame
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton, QFileDialog
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from okin_gui.gui_files.wgt_reactions import ReactionWidget
from okin_gui.gui_files.wgt_image import ImageWidget
from okin_gui.gui_files.wgt_save import SavingWidget
from okin_gui.gui_files.wgt_conc import ConcentrationWidget
from okin_gui.gui_files.wgt_table import TableWidget
from okin_gui.gui_files.wgt_qtext_window import AdvancedSettingsWidget


from okin_gui.utils.convert_to_df import load_file_to_df
from okin.simulation.simulator import Simulator
from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_logger import chem_logger
from okin.simulation.simulator import Simulator

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob

from okin_gui.utils.storage_paths import temp_file_path
from okin_gui.utils.storage_paths import copasi_file_path

class KOptTab(QMainWindow):
    get_sb = Signal(str)
    set_results = Signal(pd.DataFrame)
    def __init__(self):
        super().__init__()
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.img_path = f"{temp_file_path}/kopt.png"
        self.settings = {"to_plot": {"QElem": "", "value": ""}, "to_match": {"QElem": "", "value": ""}, "nr_gen": {"QElem": "", "value": 50}, "nr_pop": {"QElem": "", "value": 50}}

        self.copasi_data = {} #{"file_path": {"df": pd.DataFrame(), "c_dict": {"A": 0.5, "B": 0.3}, "k_dict": {"k1": "0.5", "kN1": "$0.4"}}} # c/k dict values are strings as needs to be checked for $
        self.COPASI_BASE_PATH = f"{copasi_file_path}/temp/"
        self.COPASI_RUN_PATH = f"{copasi_file_path}/"
        self.COPASI_INPUT_PATH = f"{copasi_file_path}/temp/input/"
        self.COPASI_DEFAULT_PATH = f"{copasi_file_path}/default/"      
        self.COPASI_OUTPUT_PATH = f"{copasi_file_path}/temp/kopt/Fit1/results/curr_run/" # copasi demands this structure

        self.conc_wgt = None
        self.rct_wgt_headers = []
        self.csv_wgt_headers = []

        self.dfs = []
        self.sb_is_valid = False

        self.sim = Simulator() # for creating Sb string
        self.setup_ui()

    
    def dragEnterEvent(self, event: QDragEnterEvent):
        # Check if the dragged item is a file with .mech extension
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith(".mech"):
                    event.accept()  # Accept the drag event if it's a .mech file
                    return
        event.ignore()  # Ignore the event if not a .mech file

    def dropEvent(self, event: QDropEvent):
        # Handle the dropped .mech file
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(".mech"):
                # print(f"File dropped: {file_path}")  # Process the file as needed
                self.load_mechanism(file_path)


    def update_copasi_gen_pop(self):
        # this updates the user_settings.txt file with values from the gui
        settings_dict = self.copasi_settings_wgt.get_settings_dict()

        self.set_dict_values(settings_dict=self.settings) # update all values

        nr_gen = int(self.settings["nr_gen"]["value"])
        nr_pop = int(self.settings["nr_pop"]["value"])
        
        # Update the desired values
        settings_dict['number_of_generations'] = str(nr_gen)
        settings_dict['population_size'] = str(nr_pop)

        self.copasi_settings_wgt.save_text(settings_dict)


    def setup_ui(self):
        sim_tab = QWidget()
        # sim_tab.setStyleSheet("border: 1px solid black;")
        self.setCentralWidget(sim_tab)
        sim_lyt = QVBoxLayout(sim_tab)

        input_lyt = QHBoxLayout()

        table_list = [{"name": "csv_file", "width_%": 0.97, "enable_dragdrop": True}]
        self.csv_wgt = TableWidget(table_list=table_list, num_row=5)
        self.csv_wgt.MAGIC_TABLE_PADDING = 0
        self.csv_wgt.new_selected.connect(self.on_new_selected)
        self.csv_wgt.new_csv_file.connect(self.track_species)

        self.rct_wgt = ReactionWidget()
        self.rct_wgt.RCT_LINE_WIDTH = 5
        self.rct_wgt.K_LINE_WIDTH = 2.5
        # self.rct_wgt.set_reactions(["Os -> OsO3", "OsO3 + NMO -> cat1 + H2O", "cat1 -> OsO4 + NMM" "OsO4 + SM -> cat2", "cat2 + H2O -> P + OsO3"])
        self.rct_wgt.set_reactions(["A + cat -> P + cat"])
        

        self.conc_wgt = ConcentrationWidget()
        self.conc_wgt.setFixedHeight(215)
        self.rct_wgt.used_chem_change.connect(self.track_species)

        input_lyt.addWidget(self.csv_wgt, 4)
        input_lyt.addWidget(self.rct_wgt, 4)
        input_lyt.addWidget(self.conc_wgt, 2)

        sb_b = QPushButton("Generate Sb String")
        sb_b.clicked.connect(self.generate_sb_string)

        opt_wgt = self.get_opt_wgt()

        run_sim_b = QPushButton("Run COPASI")
        run_sim_b.clicked.connect(self.run_kopt)

        self.img_wgt = ImageWidget(initial_width=1200)
        self.save_wgt = SavingWidget(parent=self, button_names=["Save CSV", "Save Image", "Save Mechanism"])

        sim_lyt.addLayout(input_lyt)
        sim_lyt.addWidget(sb_b)
        sim_lyt.addWidget(opt_wgt)
        sim_lyt.addWidget(run_sim_b)
        sim_lyt.addWidget(self.img_wgt)
        sim_lyt.addWidget(self.save_wgt)

        self.save_wgt.custom_save_b.clicked.connect(self.save_mechanism)


    def save_mechanism(self):
        self.set_dict_values(settings_dict=self.settings)
        mechanism = {}
        # get k_dict
        k_dict = self.rct_wgt.get_k_dict(as_float=False)
        mechanism["k_dict"] = k_dict

        c_dict = self.conc_wgt.get_c_dict()
        mechanism["c_dict"] = c_dict

        # get csv paths
        paths = list(self.csv_wgt.df_dict.keys())
        mechanism["csv_paths"] = paths

        # get reactions
        rcts = [str(rct).split(": ")[1] for rct in self.rct_wgt.get_reaction_list()]
        mechanism["rcts"] = rcts

        # get to_plot
        to_plot = self.settings["to_plot"]["value"]
        mechanism["to_plot"] = to_plot

        # get to_match
        to_match = self.settings["to_match"]["value"]
        self.logger.info(f"\n\nThis is in load_mechansm1 : {to_match = }\n")
        self.logger.info(f'\n\nThis is in load_mechansm1 : {self.settings["to_match"]["QElem"].text() = }\n')


        mechanism["to_match"] = to_match

        # get sb_string
        mechanism["sb_string"] = self.sb_string

        # get num_gen and pop_size
        mechanism["nr_gen"] = self.settings["nr_gen"]["value"]
        mechanism["nr_pop"] = self.settings["nr_pop"]["value"]


        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Mechanism File",
            "my_mechanism.mech",
            "Mechanism Files (*.mech)",  # Filter to only show .mech files
            options=options
        )

        with open(file_name, "w") as mech_f:
            json.dump(mechanism, mech_f, indent=4)

    def load_mechanism(self, mechanism_path):
        with open(mechanism_path, 'r') as mechanism_file:
            mechanism = json.load(mechanism_file)
        
        # get csv paths
        self.csv_wgt.set_dfs(mechanism["csv_paths"])
        self.df = load_file_to_df(mechanism["csv_paths"][-1])

        # get reactions
        self.rct_wgt.set_reactions(mechanism["rcts"])

        # get k_dict
        self.rct_wgt.set_k_dict(mechanism["k_dict"])

        # get sb_string
        #! HERE
        self.sb_string = mechanism["sb_string"]

        # set to_plot
        # self.settings["to_plot"]["value"] = to_plot_str # not needed i guess?
        self.settings["to_plot"]["value"] = mechanism['to_plot']

        # set to_match
        self.settings["to_match"]["QElem"].setText(mechanism['to_match'])
        self.settings["to_match"]["value"] = mechanism['to_match']

        # set c_dict (the ones not defined in csv files)
        c_dict = mechanism["c_dict"]
        self.conc_wgt.update_conc(c_dict, overwrite=True)
        print(f"___{self.conc_wgt.get_c_dict() = }")

        # set num_gen and pop_size
        self.settings["nr_gen"]["QElem"].setValue(int(mechanism["nr_gen"]))
        self.settings["nr_pop"]["QElem"].setValue(int(mechanism["nr_pop"]))
        self.settings["nr_gen"]["value"] = int(mechanism["nr_gen"])
        self.settings["nr_pop"]["value"] = int(mechanism["nr_pop"])


        self.create_copasi_inputs()
        self.plot_results()

    def track_species(self):
        # get all species that show up in the reactions but NOT in the df to get concentrations for them
        sender = self.sender()
        if sender == self.rct_wgt:
            #* ALL chemicals in the mechanism
            self.rct_wgt_headers = self.rct_wgt.get_used_chems()

        elif sender == self.csv_wgt:
            #* chemicals WITH concentration
            all_columns = set()
            c_dict = {}
            to_plot = [] # track to plot to update the to_plot and to_match qls.

            df = list(self.csv_wgt.df_dict.values())[0]
                       
           
            for col in df.columns:
                if not np.isnan(df[col].iloc[0]) and not col.startswith("time"):
                    col_str = col.replace("[", "").replace("]", "")
                    c_dict[col_str] = df[col].iloc[0]

                    #! FIX THIS •*!
                    #TODO FIX THIS
                    if col_str in ["L", "cat"]:
                        continue

                    # only use columns for plotting that have more than 2 data points
                    _temp_val = df[col].iloc[3]
                    if _temp_val >= 0:
                        to_plot.append(col_str)
 
            self.settings["to_plot"]["QElem"].setText(",".join(to_plot))
            self.settings["to_match"]["QElem"].setText(",".join(to_plot))

            #  kick out "[]"
            all_columns.update(list(c_dict.keys()))
            self.csv_wgt_headers = all_columns

        #* update conc input

        no_conc_species = set(self.rct_wgt_headers).difference(set(self.csv_wgt_headers))
        # print(f"{self.rct_wgt_headers = }")
        # print(f"{self.csv_wgt_headers = }")
        # print(f"{no_conc_species = }")
        self.conc_wgt.update_species(species=no_conc_species)

        # if sender == self.csv_wgt:
        #     self.conc_wgt.update_conc(c_dict=c_dict)
        
    def get_opt_wgt(self):
        wgt = QWidget()
        lyt = QHBoxLayout(wgt)

        opt_wgt = QWidget()
        opt_lyt = QHBoxLayout(opt_wgt)
        opt_lyt.setAlignment(Qt.AlignCenter)
        # lyt.setAlignment(Qt.)

        pairs = [
            (QLabel("To Plot"), QLineEdit(""), 40, 130, self.settings["to_plot"]),
            (QLabel("To Match"), QLineEdit(""), 50, 130, self.settings["to_match"]),
            (QLabel("Generations"), QSpinBox(), 45, 80, self.settings["nr_gen"]),
            (QLabel("Population"), QSpinBox(), 45, 80, self.settings["nr_pop"]),
        ]

        # Iterate over pairs and pack matching pairs into QHBoxLayouts
        for label, widget, lwidth, qwidth, qdict in pairs:
            pair_lyt = QHBoxLayout()
            if label:
                pair_lyt.addWidget(label)
                label.setFixedWidth(lwidth)
            
            pair_lyt.addWidget(widget)
            widget.setFixedWidth(qwidth)
            qdict["QElem"] = widget
            opt_lyt.addLayout(pair_lyt)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Advanced COPASI settings
        default_settings_file = os.path.join(self.COPASI_DEFAULT_PATH, "settings.txt") # this is only loaded / copied if user_settings_file not exstis
        user_settings_file = os.path.join(self.COPASI_INPUT_PATH, "user_settings.txt")
        self.copasi_settings_wgt = AdvancedSettingsWidget(settings_file=default_settings_file, custom_file=user_settings_file)
        settings = self.copasi_settings_wgt.get_settings_dict()

        self.user_settings_file = user_settings_file


        self.settings["nr_gen"]["QElem"].setValue(int(settings["number_of_generations"]))
        self.settings["nr_pop"]["QElem"].setValue(int(settings["population_size"]))

        self.settings["nr_gen"]["QElem"].setMaximum(50_000)
        self.settings["nr_pop"]["QElem"].setMaximum(50_000)

        self.settings["nr_gen"]["QElem"].valueChanged.connect(self.update_copasi_gen_pop)
        self.settings["nr_pop"]["QElem"].valueChanged.connect(self.update_copasi_gen_pop)


        advanced_copasi_b = QPushButton("!")
        advanced_copasi_b.setFixedSize(lyt.sizeHint().height()*2, lyt.sizeHint().height()*2)
        advanced_copasi_b.clicked.connect(self.copasi_settings_wgt.exec)

        lyt.addWidget(opt_wgt)
        lyt.addWidget(separator)
        lyt.addWidget(advanced_copasi_b)

        return wgt
    
    def update_sb_string(self, sb_string, sb_is_valid):
        # self.logger.info(f"Updated Sb String: \n{sb_string}")
        #! HERE
        self.sb_string = sb_string
        self.sb_is_valid = sb_is_valid            
        # self.sb_is_valid = True

    def generate_sb_string(self):
        """
        - this function generates the Sb string from initial data.
        - the sb string is send to the Sb wgt where it is checkd for validity
        - the Sb string gets updated in self.update_sb_string(), which is triggered by a Signal from the Sb wgt
        """
        self.logger.info("Now creating Sb string from reactions")
       
        rcts = self.rct_wgt.get_reaction_list()
        k_dict = self.rct_wgt.get_k_dict(as_float=False) # in case of $
        c_dict = self.get_full_c_dict()       
        self.used_chems = c_dict.keys()
        sb_string = self.sim._get_antimony_str(reactions=rcts, c_dict=c_dict, k_dict=k_dict)

        self.get_sb.emit(sb_string)

    def get_full_c_dict(self):
        no_conc_c_dict = self.conc_wgt.get_c_dict() # conc for the Sb String

        # concentration without [] = df[h].iloc[0] is the first concentration for the species (s)
        csv_c_dict = {s.replace("[", "").replace("]", ""): round(float(self.df[s].iloc[0]), 4) for s in self.df.columns if not s.startswith("Unnamed") and not s.lower().startswith("time")}

        full_c_dict = no_conc_c_dict
        full_c_dict.update(csv_c_dict)

        self.logger.info(f"new {full_c_dict = }")

        return full_c_dict

    def set_dict_values(self, settings_dict):
        for key, wgt_dct in settings_dict.items():
            widget = wgt_dct["QElem"]

            if isinstance(widget, QLineEdit):
                val = widget.text()
            
            elif isinstance(widget, QSpinBox):
                val = widget.value()

            # elif isinstance(widget, QWidget):
            #     checkboxes = widget.findChildren(QCheckBox)
            #     if checkboxes:
            #         val = {k: ch.isChecked() for k, ch in zip(self.ta_species_list, checkboxes)}
            #     else:
            #         val = widget.isChecked()
            
            # print(key, val)
            settings_dict[key]["value"] = val

    def run_kopt(self):
        if not self.sb_is_valid:
            self.logger.warning("The given Sb String is incorrect.")
            # return

        self.set_dict_values(settings_dict=self.settings)

        self.run_copasi()

        result_df = self.read_results()
        
        # signal resulting k-values to result_wgt
        self.set_results.emit(result_df) 
        
        best_results = result_df.iloc[0].tolist()
        self.update_k(best_results)
        self.plot_results()


    def update_k(self, results_row=None):
        if results_row is not None:
            self.result_row = results_row
        
        results_dict = {k: v for k, v in zip(self.k_to_fit, results_row)}

        self.rct_wgt.set_k_dict(k_dict=results_dict)

    def update_sb_k(self):
        # update only current k_values in self.sb_string 
        k_dict = self.rct_wgt.get_k_dict(as_float=False)
        results_dict = {key: value for key, value in k_dict.items() if key in self.k_to_fit}

        new_sb_string = ""
        for l in self.sb_string.split("\n"):
            # print(l)
            
            for k_name, k_val in results_dict.items():
                if l.strip().startswith(k_name):
                    new_l = f"{k_name} = {k_val}"
                    break
                else:
                    new_l = l
                
            new_sb_string += f"{new_l}\n"
        # print(f"Old Sb = {self.sb_string}\n")
        # print(f"New Sb = {new_sb_string}")
        # self.sb_string = new_sb_string
        self.get_sb.emit(new_sb_string)

    def update_sb_c(self):
        full_c_dict = self.get_full_c_dict()
        self.logger.info(f"New {full_c_dict = }")
        # results_dict = {key: value for key, value in k_dict.items() if key in self.k_to_fit}

        new_sb_string = ""
        for l in self.sb_string.split("\n"):
            # print(f"{l = }")
            
            for c_name, c_val in full_c_dict.items():
                # print(f"{c_name = }, {c_val = }")
                if l.strip().startswith(c_name):
                    new_l = f"{c_name = } = {c_val = }"
                    # print(f"updated {new_l =}")
                    break
                else:
                    new_l = l
                
            new_sb_string += f"{new_l}\n"
        # print(f"Old Sb = {self.sb_string}\n")
        # print(f"New Sb = {new_sb_string}")
        # self.sb_string = new_sb_string
        self.get_sb.emit(new_sb_string)

    def run_copasi(self):
        # delete old csvs

        self.clear_copasi_inputs()
        self.create_copasi_csvs()
        self.create_copasi_inputs() # generate COPASI settings -> full copasi dict in txt file -> include species to match, file paths, nr_gen, nr_pop, algorithm etc

        cwd = os.path.abspath(self.COPASI_RUN_PATH)

        #! version for calling second environment
        python_exe_path = os.path.join(cwd, "copasi_env", "python.exe")
        python_file_path = os.path.join(cwd, "optimize_k.py")
        cmd = f"{python_exe_path} {python_file_path}"
        print(f"\n\n{cmd = }\n")
        os.system(cmd)

        # exe_path = f"{cwd}/optimize_k.exe"
        # os.system(exe_path)
        
    
    def clear_copasi_inputs(self):
        self.logger.info("in clear")

        files = glob.glob(f"{self.COPASI_INPUT_PATH}/*.csv")
        for f in files:
            os.remove(f)

        files = glob.glob(f"{self.COPASI_INPUT_PATH}/*.txt")
        for f in files:
            if not f.endswith("user_settings.txt"):
                os.remove(f)

    def create_copasi_csvs(self):
        to_match = [s.strip() for s in self.settings["to_match"]["value"].split(",")]
        self.logger.info(f"\n\nThis is in create_copasi_csvs : {to_match = }\n")

        # df[c].iloc[0] for all that have different concentrations between experiments -> all other from conc input
        for path, df in self.csv_wgt.df_dict.items():
            name = os.path.basename(path)
            time_col = [c for c in df.columns if c.startswith("time")][0]

            try:
                df = df.rename(columns={time_col: 'time'})
            except:
                pass

            df = df.reset_index(drop=True)
            df = df.set_index("time")
            new_path = os.path.join(self.COPASI_INPUT_PATH, name)

            # create the _indep column to signal COPASI the starting concentration for that species FROM THE CSV FILE
            for species in df.columns:
                # create starting conc for species in CSV
                if species.lower().startswith("unnamed") or species.lower().startswith("time"):
                    continue
    
                starting_conc = df[species].iloc[0]
                col_name = species + "_indep"
                df[col_name] = None  # Initialize the new column with None (or NaN)
                    
                try:
                    self.logger.debug(f"{df[species].iloc[0]=}, {starting_conc=}")
                except KeyError:
                    pass
                # Set the value for the first row in the new column
                df.loc[0, col_name] = starting_conc

            # create the _indep column to signal COPASI the starting concentration for that species FROM THE CONC INPUT WIDGET
            for species, s_dict in self.conc_wgt.c_dict.items():
                starting_conc = round(float(s_dict["value"]), 4)
                col_name = species + "_indep"
                df[col_name] = None  # Initialize the new column with None (or NaN)
                df.loc[0, col_name] = starting_conc

            # delete all time course values that should not be used for to match
            for col in df.columns:
                if col == "time" or col.endswith("_indep"):
                    continue
                if col not in to_match:
                    # Set all values except the first one to ""
                    df.iloc[1:, df.columns.get_loc(col)] = ""


            self.logger.info(f"Created csv at {new_path=}")
        
            # remove [] from headers 
            df.columns = [col.replace('[', '').replace(']', '') for col in df.columns]

            df.to_csv(new_path)

    def create_copasi_inputs(self):
        # settings is in self.copasi_settings_wgt and gets updated automatically

        # fit_items.txt
        k_dict = self.rct_wgt.get_k_dict(as_float=False)
        fit_item_path = os.path.join(self.COPASI_INPUT_PATH, "fit_items.txt")
        print(f"{k_dict = }")
        k_to_fit = [k_name for k_name in k_dict.keys() if not "$" in k_dict[k_name]]
        self.k_to_fit = k_to_fit
        self.logger.info(f"{k_to_fit=}")

        with open(fit_item_path, "w") as fif:
            fif.write(str(k_to_fit))

        # sb_string.txt
        sb_string_path = os.path.join(self.COPASI_INPUT_PATH, "sb_string.txt")
        with open(sb_string_path, "w") as sbf:
            print(f"COPASI from Sb string:\n{self.sb_string}")
            sbf.write(self.sb_string)
 
        with open(sb_string_path, "w") as sbf:
            sbf.write(self.sb_string)

    def read_results(self):
        paths_to_ks = glob.glob(self.COPASI_OUTPUT_PATH + "\*.txt")
        
        dfs = []
        for path_to_ks  in paths_to_ks:
            temp_df = pd.read_csv(path_to_ks, sep="\t")
            dfs.append(temp_df)
        
        df = pd.concat(dfs, ignore_index=True).sort_values(by='RSS', ascending=True)
        return df

    def get_result_ks(self, row=None):
        if isinstance(row, pd.Series):
            selected_row = row
        else:
            selected_row = self.df_widget.get_selected_row() # <class 'pandas.core.series.Series'>
            
        # self.result_dict = dict(selected_row)
        self.results_ks = list(selected_row)
        self.results_rss = self.results_ks.pop(-1) # last value is rss

    def plot_results(self):
        to_plot = ["time"] + [s.strip() for s in self.settings["to_plot"]["value"].split(",")]
        self.update_sb_k()
        # full_k_dict = self.rct_wgt.get_k_dict(as_float=False)
        # full_c_dict = self.get_full_c_dict()
        # rcts = self.rct_wgt.get_reaction_list()
        self.logger.info(f"{to_plot = }")

        time_col = [col for col in self.df.columns if col.startswith("time")][0]
        times = [float(t) for t in self.df[time_col]]

        self.logger.warning(f"This is what I give as selection: {to_plot = }, {type(to_plot) = }")
        self.sim.simulate(sb_string=self.sb_string, times=times, selections=to_plot)

        self.results_df = self.sim.result.copy()
        
        for s in to_plot:
            self.logger.info(f"Now plotting {s = }")
            if s.lower().startswith("time"):
                continue
            # plot simulation first so that it can plot things that are not in df
            plt.plot(self.sim.result["time"], self.sim.result[s], linestyle=":", marker="*", markersize=5, label=f"{s} model")

            plt.scatter(self.df[time_col], self.df[s], label=f"{s} real", s=30, alpha=0.6)
            # plt.plot(self.df[time_col], self.df[s], c="orange", alpha=0.7)

            # plt.scatter(self.sim.result["time"], self.sim.result[s], label=f"{s} simulated", linestyle=":", marker="h", c="k", alpha=0.6)
        
        self.sim.result.to_csv("test.csv", index=False)

        plt.xlabel("time")
        plt.ylabel("concentration")
        plt.legend()
        apply_acs_layout()
        plt.savefig(self.img_path, dpi=500)
        plt.clf()
        
        self.img_wgt.set_image_path(self.img_path)

    # def update_to_plot(self):
    #     self.settings["to_plot"]["value"] = self.settings["to_plot"]["QElem"].text()

    def new_results_selected(self, results_row):
        # self.update_k(results_row=results_row)
        self.update_sb_k()
        self.update_sb_c()
        self.plot_results()


    @Slot(list)
    def on_new_selected(self, selected_row):
        try:
            self.df = load_file_to_df(selected_row[0])
            # self.update_sb_k()
            # self.update_sb_c()
            self.set_dict_values(self.settings)
            self.generate_sb_string() #TODO make this only update concentrations
            self.plot_results()

        except Exception as e:
            self.logger.warning(f"Data could not be read because: {e}")
            # df = pd.DataFrame()


        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KOptTab()
    window.setup_ui()
    window.resize(1000, 850)
    window.show()
    

    sys.exit(app.exec())