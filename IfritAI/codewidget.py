from os.path import split
from typing import List

from PyQt6.QtWidgets import QWidget, QTextEdit, QHBoxLayout, QPushButton, QVBoxLayout, QSizePolicy

from FF8GameData.gamedata import GameData
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
        last_was_else_for_if = False
        for command in self._command_list:
            print(f"if_list_count: {if_list_count}")
            print("Current id func: {command.get_id()}")
            for i in range(len(if_list_count)):
                if_list_count[i] -= command.get_size()
                if if_list_count[i] == 0:
                    func_list.append('}')
            print(f"if_list_count: {if_list_count}")
            nb_remove = 0
            while 0 in if_list_count:
                if_list_count.remove(0)
                nb_remove += 1
            print(f"if_list_count: {if_list_count}")
            # text = [x[] for x in self.game_data.ai_data_json['op_code_info'] if x['op_code'] == command.get_id()
            if command.get_id() != 2 and last_was_else_for_if:
                last_was_else_for_if = False
            elif command.get_id() == 2:  # IF
                print("ITS AN IF")
                # func_list.append(command.get_text(with_size=False, for_code=True))

                op_list = command.get_op_code()
                jump_value = int.from_bytes(bytearray([op_list[5], op_list[6]]), byteorder='little')
                print(f"jump_value: {jump_value}")
                if_list_count.append(jump_value)
                print(command.get_text(with_size=False, for_code=True))
                command_text = command.get_text(with_size=False, for_code=True)
                command_text = command_text.split('|')[0]
                if last_was_else_for_if:
                    command_text = command_text.replace('IF', "ELIF")
                func_list.append(command_text)
                func_list.append('{')

            else:
                if nb_remove > 0 and command.get_id() == 35:  # We have an else that finish there
                    op_list = command.get_op_code()
                    jump_value = int.from_bytes(bytearray([op_list[0], op_list[1]]), byteorder='little')
                    if jump_value > 0:
                        last_was_else_for_if = True
                    continue

                print(command.get_text(with_size=False, for_code=True))
                func_list.append(command.get_text(with_size=False, for_code=True))
        code_text = ""
        for func_name in func_list:
            code_text += func_name
            code_text += '<br/>'
        self.code_area_widget.setText(code_text)
        self.__compute_indent_bracket()

    def _compute_ifrit_ai_code_to_command(self):
        print("compute ifrit start")
        self._command_list = []
        command_text_list = self.code_area_widget.toPlainText().splitlines()

        # First analyse everything between { }
        print("First analyse")
        between_bracket = False
        useful_line_index = 0
        for index, line in enumerate(command_text_list):
            print(f"index: {index}, line: {line}")
            if line == "":
                continue
            elif line.replace(' ', '') == "{":
                between_bracket = True
                continue
            elif line.replace(' ', '') == "}":
                between_bracket = False
                continue
            elif "IF" in line:
                useful_line_index+=1
                continue
            elif "ELIF" in line:
                useful_line_index+=1
                continue
            if between_bracket:
                print("between_bracket")
                new_command = Command(0, [], self.game_data, info_stat_data=self.ennemy_data.info_stat_data,
                                      battle_text=self.ennemy_data.battle_script_data['battle_text'], line_index=useful_line_index, code_text=line)
                self._command_list.append(new_command)
                useful_line_index += 1
                print(self._command_list)


        # Then analysing IF
        print("Second analyse")
        print(self._command_list)
        if_found = True
        count_while = 0
        while if_found:
            print("Looping while")
            useful_line_index = 0
            real_if_line_index = 0
            count_while +=1
            if_found = False
            in_if_counting = False
            if_line_index = 0
            counting_if = 0
            for index, line in enumerate(command_text_list):
                print(f"index: {index}, line: {line}")
                print(f" counting_if:{counting_if}")
                print(f" if_line_index:{if_line_index}")
                print(f"if_found:{if_found}")
                if 'IF' in line and 'ELSE' not in line:
                    print("IF WITHOUT ELSE FOUND")
                    counting_if = 0
                    useful_if_line_index = useful_line_index
                    real_if_line_index = index
                    if_found = True
                    in_if_counting = True
                    useful_line_index+=1
                    continue
                elif 'IF' in line:
                    useful_line_index += 1
                    continue
                elif line.replace(' ', '') == "{":
                    print("{ found")
                    continue
                elif line.replace(' ', '') == "}": # End of counting
                    print("} found")
                    if counting_if == 0: # Already managed if
                        continue
                    command_text_list[real_if_line_index] += f"| ELSE jump {{{counting_if+3}}} bytes forward"
                    print(f"Command: {command_text_list[real_if_line_index]}")
                    print(f"useful_if_line_index: {useful_if_line_index}")
                    new_command = Command(0, [], self.game_data, info_stat_data=self.ennemy_data.info_stat_data,
                                          battle_text=self.ennemy_data.battle_script_data['battle_text'], line_index=useful_if_line_index, code_text=command_text_list[real_if_line_index])
                    self._command_list.insert(useful_if_line_index, new_command)
                    new_command = Command(35, [0,0], self.game_data, info_stat_data=self.ennemy_data.info_stat_data,
                                          battle_text=self.ennemy_data.battle_script_data['battle_text'], line_index=useful_line_index)

                    self._command_list.insert(useful_line_index, new_command)
                    counting_if = 0
                    in_if_counting = False
                    continue

                elif "ELIF" in line:#TODO
                    print("ELIF")
                    line = line.replace('ELIF', 'IF')
                    new_command = Command(0, [], self.game_data, info_stat_data=self.ennemy_data.info_stat_data,
                                          battle_text=self.ennemy_data.battle_script_data['battle_text'], line_index=index, code_text=line)
                    self._command_list.append(new_command)
                else:
                    current_command = [x.get_size() for x in self._command_list if x.line_index == useful_line_index]
                    if current_command and in_if_counting:
                        counting_if += current_command[0]
                    else:
                        print(f"No current command found on index: {index} for command list: {self._command_list}")
                    useful_line_index += 1
            if not if_found:
                break
            if count_while > 3:
                exit(-1)
        self.code_changed_hook(self._command_list)
        # self.__compute_indent_bracket()
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

    def __compute_indent_bracket(self):
        print("__compute_indent_bracket")
        command_text_list = self.code_area_widget.toPlainText().splitlines()
        indent = 0
        new_text = ""
        indent_text = "&nbsp;" * 4
        for i in range(len(command_text_list)):
            command_without_space = command_text_list[i].replace(' ', '')
            if command_without_space == '}':
                indent -= 1
            command_text_list[i] = indent_text * indent + command_text_list[i]
            if command_without_space == '{':
                indent += 1
            new_text += command_text_list[i] + "<br/>"
        self.code_area_widget.setText(new_text)
