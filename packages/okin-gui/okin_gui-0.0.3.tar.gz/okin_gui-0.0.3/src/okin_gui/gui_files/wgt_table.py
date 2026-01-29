from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent
import pandas as pd
import os
# from okin_gui_utils.style_utils import get_stylesheet

from okin.base.chem_logger import chem_logger
from okin_gui.utils.convert_to_df import load_file_to_df

class TableWidget(QWidget):
    resized = Signal()
    new_selected = Signal(list)
    new_csv_file = Signal()
    double_click_trigger = Signal()

    VALID_FILE_EXTENSIONS = [".csv", ".txt"] # add  ".xlsx", "xls"
    MAGIC_TABLE_PADDING = 30

    def __init__(self, table_list, fixed_height=215, num_row=1, allow_edit=False, cell_alignment="left"):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        super().__init__() # there was super().__init__(parent) and parent=None in __init__(self, …)
        #! make this usalble self.cell_alignment = cell_alignment
        self.fixed_height = fixed_height
        self.table_list = table_list
        self.num_row = num_row
        self.selected_row = None
        self.allow_edit = allow_edit
        self.df_dict = {} # "{path: df}"
        
        self.setup_ui()

    def setup_ui(self):
        # self.resize(600, 800)
        self.content_wgt = QWidget()
        self.content_wgt.setMinimumWidth(300)
        content_layout = QVBoxLayout(self.content_wgt)

        # Create the table
        self.table = QTableWidget(0, len(self.table_list))
        self.table.setHorizontalHeaderLabels([item["name"] for item in self.table_list])
        self.table.setRowCount(self.num_row)
        self.table.setFixedHeight(215)

        # Enable drag and drop
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QAbstractItemView.DragDrop)
        self.table.dragEnterEvent = self.dragEnterEvent
        self.table.dragMoveEvent = self.dragMoveEvent
        self.table.dropEvent = self.dropEvent

        # self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.handle_item_selection)
        self.table.cellClicked.connect(self.get_clicked_row_content)
        self.table.cellDoubleClicked.connect(self.double_click)
        self.table.setSelectionMode(QTableWidget.SingleSelection)  # Set single selection mode
        
        if not self.allow_edit:
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        
        content_layout.addWidget(self.table)
        layout = QVBoxLayout(self)
        layout.addWidget(self.content_wgt)

        header_style = (
            "QHeaderView::section {"
            "    background-color: #333333;"  # Dark grey background color
            "    color: white;"               # White text color
            "}"
        )
        self.table.horizontalHeader().setStyleSheet(header_style)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addStretch(1)
        self.logger.debug("setup done")
        self.table.cellChanged.connect(self.check_last_row_empty)

    def double_click(self):
        self.logger.info(f"triggering double click in {self.__class__.__name__}")
        self.double_click_trigger.emit()

    def check_last_row_empty(self):
        if not self.is_last_row_empty():
            self.table.setRowCount(self.table.rowCount() + 1)
        self.num_row = self.table.rowCount()

    def handle_item_selection(self):
        selected_items = self.table.selectedItems()
        if len(selected_items) == 0:
            return

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            self.delete_selected_cell()
        else:
            super().keyPressEvent(event)

    def delete_selected_cell(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        rows_to_remove = set()
        for item in selected_items:
            row = item.row()
            col = item.column()

            if self.is_row_empty(row):
                rows_to_remove.add(row)
            else:
                item.setText("")  # Clear the content of the selected cell

        # Remove entire rows that are empty after deleting cells
        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)
            # remove the csv from the dfs
            csv_path_to_remove = self.table.item(row, 0).text() if self.table.item(row, 0) else None
            del self.df_dict[csv_path_to_remove]

    def is_row_empty(self, row):
        num_columns = self.table.columnCount()
        for col in range(num_columns):
            item = self.table.item(row, col)
            if item is not None and item.text():
                return False
        return True

    def is_last_row_empty(self):
        last_row = self.table.rowCount() - 1
        for col in range(self.table.columnCount()):
            item = self.table.item(last_row, col)
            if item and item.text():
                return False
        return True

    def get_clicked_row_content(self, row, column) -> list:
        # Retrieve the content of the clicked row
        row_content = []
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item is not None:
                row_content.append(item.text())
            else:
                row_content.append(None)
        self.selected_row = row_content
        self.new_selected.emit(self.selected_row)
        self.logger.debug(f"selected_row = {self.selected_row}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # self.resize(self.size().width()*self.rel_width_pct)
        self.resized.emit()

        total_width = self.content_wgt.size().width() - self.MAGIC_TABLE_PADDING
        for i, col in enumerate(self.table_list):
            col_width = col["width_%"] * total_width
            self.table.setColumnWidth(i, col_width)
            
    def dragMoveEvent(self, event: QDragMoveEvent):
        return

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            file_extension = os.path.splitext(file_path)[1]
            if file_extension not in self.VALID_FILE_EXTENSIONS:
                continue
                       
            
            column = self.table.columnAt(event.position().toPoint().x())

            # check if column should accept
            if not self.table_list[column]['enable_dragdrop']:
                continue

            # Check if the file path is already present in the column
            already_present = any(
                self.table.item(row, column).text() == file_path
                for row in range(self.table.rowCount())
                if self.table.item(row, column) is not None
            )
            if not already_present:
                try:
                    df = load_file_to_df(file_path=file_path)
                    self.df_dict[file_path] = df
                    self.new_csv_file.emit()

                except Exception as e:
                    self.logger.warning(f"Data could not be read because: {e}")
                
                # Find the first empty cell in the column
                for row in range(self.table.rowCount()):
                    if self.table.item(row, column) is None:
                        # file_base_path = os.path.basename(file_path)
                        self.table.setItem(row, column, QTableWidgetItem(file_path))
                        break

        if not self.selected_row:
            last_added_item = self.table.item(row, column)
            self.get_clicked_row_content(row=row, column=column)
            self.table.setCurrentItem(last_added_item)

    def get_df(self):
        # thank you chatGPT
        headers = [self.table.horizontalHeaderItem(col).text() for col in range(self.table.columnCount())]
        df = pd.DataFrame(columns=headers)
        self.logger.debug(f"created df with headers: {headers}")

        for row in range(self.table.rowCount()):
            row_data = []

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append(None)
            if not any(row_data):
                continue
            df.loc[len(df)] = row_data
        self.logger.debug(f"df has {len(df)} rows of valid data")
        return df  

    def set_dfs(self, csv_list):
        # clear layout
        self.table.clearContents()               # Clear all existing content in the table
        self.table.setRowCount(len(csv_list))         # Set the number of rows based on the length of dfs

        # populate layout
        for row_idx, csv_path in enumerate(csv_list):
            # for col_idx, value in enumerate(csv_path):
            self.table.setItem(row_idx, 0, QTableWidgetItem(csv_path))

            try:
                df = load_file_to_df(file_path=csv_path)
                self.df_dict[csv_path] = df
                self.new_csv_file.emit()

            except Exception as e:
                self.logger.warning(f"Data could not be read because: {e}")
            

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    table_list = [{"name": "csv_file", "width_%": 0.7, "enable_dragdrop": True}, {"name": "csv2", "width_%": 0.3, "enable_dragdrop": False}]
    widget = TableWidget(table_list)
    widget.show()
    sys.exit(app.exec())
