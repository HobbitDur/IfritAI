from os.path import split
from typing import List

from PyQt6.QtWidgets import QWidget, QTextEdit, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy

from FF8GameData.gamedata import GameData
from IfritAI.codeanalyser import CodeAnalyser
from IfritAI.command import Command
from IfritAI.ennemy import Ennemy


class CodeWidget(QWidget):
    IF_INDENT_SIZE = 3

    def __init__(self, game_data: GameData, ennemy_data: Ennemy, expert_level=2, command_list: List[Command] = (), code_changed_hook=None,
                 hex_chosen: bool = False):
        QWidget.__init__(self)
        self.game_data = game_data
        self.ennemy_data = ennemy_data
        self.code_changed_hook = code_changed_hook
        self._hex_chosen = hex_chosen
        self._expert_level = expert_level
        self.code_area_widget = QTextEdit()
        self.code_area_widget.setFontPointSize(15)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.compute_button = QPushButton()
        self.compute_button.setText("Compute")
        self.change_expert_level(expert_level)

        self.main_layout.addWidget(self.compute_button)
        self.main_layout.addWidget(self.code_area_widget)

        self._command_list = command_list
        self.set_text_from_command(self._command_list)

    def change_expert_level(self, expert_level):
        print("change_expert_level")
        self._expert_level = expert_level
        if expert_level == 2:
            self.compute_button.clicked.connect(self._compute_text_to_command)
        elif expert_level == 3:
            self.compute_button.clicked.connect(self._compute_ifrit_ai_code_to_command)
        else:
            print(f"Unexpected expert level in codewidget: {expert_level}")

    def change_hex(self, hex_chosen):
        self._hex_chosen = hex_chosen
        new_code_text = ""
        for line in self.code_area_widget.toPlainText().splitlines():
            command_id_text, op_code_text = self._get_data_from_line(line)
            op_code_new_text = ""
            if op_code_text:
                op_code_new_text += "("
            for i in range(len(op_code_text)):
                op_code_int = int(op_code_text[i], 0)
                if i > 0:
                    op_code_new_text += ", "
                if self._hex_chosen:
                    op_code_text_unit = "0x{:02X}".format(op_code_int)
                else:
                    op_code_text_unit = str(op_code_int)
                op_code_new_text += op_code_text_unit
            if op_code_text:
                op_code_new_text += ")"
            new_code_text += command_id_text + op_code_new_text + "\n"
        self.code_area_widget.setText(new_code_text)

    def set_ifrit_ai_code_from_command(self, command_list: List[Command]):
        print("set_ifrit_ai_code_from_command")
        self._command_list = command_list
        func_list = []
        if_list_count = []
        else_list_count = []
        for command in self._command_list:
            print(f"if_list_count: {if_list_count}")
            print("Current id func: {command.get_id()}")
            for i in range(len(if_list_count)):
                if_list_count[i] -= command.get_size()
                if if_list_count[i] == 0:
                    func_list.append('}')
            print(f"if_list_count: {if_list_count}")
            while 0 in if_list_count:
                if_list_count.remove(0)
            print(f"if_list_count: {if_list_count}")
            # text = [x[] for x in self.game_data.ai_data_json['op_code_info'] if x['op_code'] == command.get_id()
            op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == command.get_id()][0]
            if command.get_id() == 2:  # IF
                print("ITS AN IF")
                # func_list.append(command.get_text(with_size=False, for_code=True))

                op_list = command.get_op_code()
                jump_value = int.from_bytes(bytearray([op_list[5], op_list[6]]), byteorder='little')
                print(f"jump_value: {jump_value}")
                if_list_count.append(jump_value)
                print(command.get_text(with_size=False, for_code=True))
                command_text = command.get_text(with_size=False, for_code=True, html=True)
                command_text = command_text.split('|')[0]
                #if last_was_else_for_if:
                #    command_text = command_text.replace('IF', "ELIF")

                func_line_text = op_info['func_name'] + ": "
                func_line_text += command_text
                func_list.append(func_line_text)
                func_list.append('{')
            elif command.get_id() == 35:
                op_list = command.get_op_code()
                jump_value = int.from_bytes(bytearray([op_list[0], op_list[1]]), byteorder='little')
                print(f"jump_value for else: {jump_value}")

                print(command.get_text(with_size=False, for_code=True))
                if jump_value == 0:# An if is finishing here so we ignore it
                    continue
                print(f"Adding else with jump value: {jump_value}")
                else_list_count.append(jump_value)
                print(f"new else_list_count: {else_list_count}")
                command_text = "ELSE"
                func_line_text = op_info['func_name'] + ": "
                func_line_text += command_text
                func_list.append(func_line_text)
                func_list.append('{')


            else:
                print(command.get_text(with_size=False, for_code=True))
                op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == command.get_id()][0]
                func_line_text = op_info['func_name'] + ": "
                func_line_text += command.get_text(with_size=False, for_code=True, html=True)
                func_list.append(func_line_text)
            # The else are closing after the function (you don't count the jump contrary to an if
            if command.get_id() !=35:
                for i in range(len(else_list_count)):
                    else_list_count[i] -= command.get_size()
                    if else_list_count[i] == 0:
                        func_list.append('}')
                print(f"else_list_count: {else_list_count}")
                while 0 in else_list_count:
                    else_list_count.remove(0)

        func_list = self.__compute_indent_bracket(func_list)
        code_text = ""
        for func_name in func_list:
            code_text += func_name
            code_text += '<br/>'
        self.code_area_widget.setText(code_text)

    def _compute_ifrit_ai_code_to_command(self):
        print("compute ifrit start")
        self._command_list = []
        command_text_list = self.code_area_widget.toPlainText().splitlines()
        code_analyser = CodeAnalyser(self.game_data, self.ennemy_data, command_text_list)
        self._command_list = code_analyser.get_command()
        print(f"End ai analyse, command list: {self._command_list}")
        for command in self._command_list:
            print(command)
            print(f"Line index of command before hook: {command.line_index}")
        self.code_changed_hook(self._command_list)
        print("compute ifrit end")

    def set_text_from_command(self, command_list: List[Command]):
        self._command_list = command_list
        func_list = []
        for command in self._command_list:
            func_name = \
                [command_data['func_name'] for command_data in self.game_data.ai_data_json['op_code_info'] if command_data['op_code'] == command.get_id()][0]
            if func_name == "":
                func_name = "unknown_func_name"
            op_code_list = command.get_op_code()
            if op_code_list:
                func_name += "("
            for i, op_code in enumerate(op_code_list):
                if i > 0:
                    func_name += ", "
                if self._hex_chosen:
                    func_name += "0x{:02X}".format(op_code)
                else:
                    func_name += str(op_code)
            if op_code_list:
                func_name += ")"
            func_list.append(func_name)
        code_text = ""
        for func_name in func_list:
            code_text += func_name
            code_text += '\n'
        self.code_area_widget.setText(code_text)
        self.__compute_if()

    def _compute_text_to_command(self):
        print("_compute_text_to_command")
        self._command_list = []
        command_text_list = self.code_area_widget.toPlainText().splitlines()
        for index, line in enumerate(command_text_list):
            command_id_text, op_code_text = self._get_data_from_line(line)
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
        self.__compute_if()

    @staticmethod
    def _get_data_from_line(line):
        line = line.replace(" ", "")
        split_data_name = line.split("(")
        command_id_text = split_data_name[0]
        if len(split_data_name) == 2:
            split_data_name[1] = split_data_name[1].replace(")", "")
            op_code_text = split_data_name[1].split(",")
        else:
            op_code_text = []
        return command_id_text, op_code_text

    def __compute_if(self, raw=True):
        command_text_list = self.code_area_widget.toPlainText().splitlines()
        if_index = 0
        new_text = ""
        for line in command_text_list:
            func_name, op_code_text = self._get_data_from_line(line)
            command_id = [x['op_code'] for x in self.game_data.ai_data_json['op_code_info'] if x['func_name'] == func_name]
            if command_id:
                command_id = command_id[0]
            else:
                print(f"Unknown func when computing if: {func_name}")
                command_id = 0
            if command_id == 35:
                if int(op_code_text[0], 0) == 0 or int(op_code_text[0], 0) == 3:
                    if_index -= 1
            for i in range(if_index * self.IF_INDENT_SIZE):
                new_text += " "
            if command_id == 2:
                if_index += 1
            new_text += line + '\n'

        self.code_area_widget.setText(new_text)

    def __compute_indent_bracket(self, func_list:List):
        print("__compute_indent_bracket")
        indent = 0
        new_text = ""
        indent_text = "&nbsp;" * 4
        for i in range(len(func_list)):
            command_without_space = func_list[i].replace(' ', '')
            if command_without_space == '}':
                indent -= 1
            func_list[i] = indent_text * indent + func_list[i]
            if command_without_space == '{':
                indent += 1
            new_text += func_list[i] + "<br/>"
        return func_list
