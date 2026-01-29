import os

okin_gui_path = __file__[:-23]
temp_file_path = os.path.join(okin_gui_path, "temp")
# copasi_file_path = os.path.join(okin_gui_path, "copasi")
copasi_path = "copasi_path.txt"
# print(copasi_path)
with open(copasi_path, "r") as f:
    copasi_file_path = f.read()


print(f"{okin_gui_path = }\n{temp_file_path = }\n{copasi_file_path = }")


# D:\code\modules\hein_modules\okin_gui\src\okin_gui\copasi