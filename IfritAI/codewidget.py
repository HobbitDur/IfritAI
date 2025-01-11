from os.path import split
from typing import List

from PyQt6.QtWidgets import QWidget, QTextEdit, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy

from FF8GameData.gamedata import GameData
from IfritAI.command import Command
from IfritAI.ennemy import Ennemy


class CodeWidget(QWidget):

    def __init__(self, game_data: GameData, ennemy_data: Ennemy, command_list: List[Command] = (), code_changed_hook=None, hex_chosen:bool=False):
        QWidget.__init__(self)
        self.game_data = game_data
        self.ennemy_data = ennemy_data
        self.code_changed_hook = code_changed_hook
        self._hex_chosen = hex_chosen
        self.code_area_widget = QTextEdit()
        self.code_area_widget.setFontPointSize(15)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(self.code_area_widget)
        self._command_list = command_list
        self.set_text_from_command(self._command_list)

        self.compute_button = QPushButton()
        self.compute_button.setText("Compute")
        self.compute_button.clicked.connect(self._compute_text_to_command)

        self.main_layout.addWidget(self.compute_button)

    def change_hex(self, hex_chosen):
        self._hex_chosen = hex_chosen
        new_code_text = ""
        for line in self.code_area_widget.toPlainText().splitlines():
            split_data = line.split(" ")
            command_id_text = split_data[0]
            op_code_text = split_data[1:]
            op_code_new_text = ""
            for i in range(len(op_code_text)):
                op_code_int = int(op_code_text[i], 0)
                if self._hex_chosen:
                    op_code_text_unit = "0x{:02X}".format(op_code_int)
                else:
                    op_code_text_unit = str(op_code_int)
                op_code_new_text+= " " + op_code_text_unit
            new_code_text += command_id_text + op_code_new_text + "\n"
        self.code_area_widget.setText(new_code_text)

    def set_text_from_command(self, command_list: List[Command]):
        self._command_list = command_list
        func_list = []
        for command in self._command_list:
            func_name = [command_data['func_name'] for command_data in self.game_data.ai_data_json['op_code_info'] if command_data['op_code'] == command.get_id()][0]
            if func_name == "":
                func_name="unknown_func_name"
            for op_code in command.get_op_code():
                if self._hex_chosen:
                    func_name += " " + "0x{:02X}".format(op_code)
                else:
                    func_name += " " + str(op_code)
            func_list.append(func_name)
        code_text = ""
        for func_name in func_list:
            code_text += func_name
            code_text+= '\n'
        self.code_area_widget.setText(code_text)

    def _compute_text_to_command(self):
        self._command_list = []
        command_text_list = self.code_area_widget.toPlainText().splitlines()
        for index, command_text in enumerate(command_text_list):
            split_data = command_text.split(" ")
            command_id_text = split_data[0]
            op_code_text = split_data[1:]
            op_code_int = []
            for i in range(len(op_code_text)):
                if self._hex_chosen:
                    op_code_int.append(int(op_code_text[i], 16))
                else:
                    op_code_int.append(int(op_code_text[i]))
            command_id = [x['op_code'] for x in self.game_data.ai_data_json['op_code_info'] if x['func_name'] == command_id_text]
            if command_id:
                command_id = command_id[0]
            else:
                print("Unknown function name, using stop by default")
                command_id = 0
            new_command = Command(command_id, op_code_int, self.game_data, info_stat_data=self.ennemy_data.info_stat_data,
                                  battle_text=self.ennemy_data.battle_script_data['battle_text'], line_index=index)
            self._command_list.append(new_command)
        self.code_changed_hook(self._command_list)



