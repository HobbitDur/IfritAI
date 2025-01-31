from typing import List
import re

from FF8GameData.dat.commandanalyser import CommandAnalyser
from FF8GameData.dat.monsteranalyser import MonsterAnalyser
from FF8GameData.gamedata import GameData


class CodeAnalyseTool:
    def __init__(self):
        self.counter = 0

    @classmethod
    def searching_if(cls, lines: List[str], if_func_name: str, else_func_name: str):
        # Now searching for IF in the section
        index_start_if = -1
        index_end_if = -1
        func_found = None
        for i in range(len(lines)):
            if if_func_name + ":" in lines[i].replace(' ', '') or else_func_name + ":" in lines[i].replace(' ', ''):  # New if found
                if if_func_name + ":" in lines[i].replace(' ', ''):
                    func_found = if_func_name
                else:
                    func_found = else_func_name
                index_start_if = i
                # Now searching the end
                # Searching the closing bracket of this if. If there is other open bracket, it means we need to search one more close bracket for this if.
                number_close_bracket_to_search = 0
                for j in range(i + 1, len(lines)):
                    if lines[j].replace(' ', '') == '{':
                        number_close_bracket_to_search += 1
                    elif lines[j].replace(' ', '') == '}':
                        number_close_bracket_to_search -= 1
                    if number_close_bracket_to_search == 0:
                        index_end_if = j
                        break
                break

        return index_start_if, index_end_if, func_found

    @classmethod
    def analyse_lines(cls, section_lines: List[str], game_data: GameData, enemy_data: MonsterAnalyser, section_previous_command:CommandAnalyser=None):
        command_list = []
        for i in range(len(section_lines)):
            if not command_list:
                previous_command = section_previous_command
            else:
                previous_command = command_list[-1]
            new_code_line = CodeLine(game_data, enemy_data, section_lines[i], i, previous_command=previous_command)
            if new_code_line:
                command_list.append(new_code_line.get_command())
        return command_list

    @classmethod
    def analyse_loop(cls, section_lines: List[str], if_func_name: str, else_func_name: str, game_data: GameData, enemy_data: MonsterAnalyser, section_previous_command:CommandAnalyser=None):
        command_list = []
        last_line = 0
        while True:
            if not command_list:
                previous_command = section_previous_command
            else:
                previous_command = command_list[-1]
            command_list_temp, if_index, round_last_line = CodeAnalyseTool().analyse_one_round(section_lines[last_line:], if_func_name, else_func_name,
                                                                                               game_data, enemy_data, section_previous_command=previous_command)
            last_line += round_last_line
            command_list.extend(command_list_temp)
            last_line += 1  # We analyze the line after the last one analysed, logic no ?
            if if_index < 0 or last_line == len(section_lines):
                break
        return command_list

    @classmethod
    def analyse_one_round(cls, section_lines: List[str], if_func_name: str, else_func_name: str, game_data: GameData, enemy_data: MonsterAnalyser, section_previous_command:CommandAnalyser=None):
        # Searching for IF in the section
        if_start_index, if_end_index, func_found = CodeAnalyseTool.searching_if(section_lines, if_func_name, else_func_name)
        if if_start_index == -1:  # Didn't find any if, we analyse till the end:
            end_analyse_line = len(section_lines) - 1
            last_line = end_analyse_line
        else:
            end_analyse_line = if_start_index - 1
            last_line = end_analyse_line
        # Analysing all normal command before the if (till the end if no one found)
        command_list = []
        if if_start_index != 0:  # If the if is the first of the section, then we don't have to analyse anything
            command_list = CodeAnalyseTool.analyse_lines(section_lines[:end_analyse_line + 1], game_data, enemy_data,section_previous_command=section_previous_command )
        # Analysing the if section if found one
        if if_start_index != -1:
            if not command_list:
                previous_command = section_previous_command
            else:
                previous_command = command_list[-1]
            if func_found == if_func_name:
                if len(section_lines) > if_end_index + 1:
                    next_line  = section_lines[if_end_index + 1]
                else:
                    next_line = ""
                section_command_list = CodeIfSection(game_data, enemy_data, section_lines[if_start_index: if_end_index + 1], if_start_index, next_line, section_previous_command=previous_command)
            elif func_found == else_func_name:
                section_command_list = CodeElseSection(game_data, enemy_data, section_lines[if_start_index: if_end_index + 1], if_start_index, section_previous_command=previous_command)
            else:
                print(f"Unexpected func found: {func_found}")
                section_command_list = None
            command_list.extend(section_command_list.get_command())
            last_line += section_command_list.get_nb_line()
        return command_list, if_start_index, last_line


class CodeLine:
    def __init__(self, game_data: GameData, enemy_data: MonsterAnalyser, code_text_line: str, line_index: int, previous_command:CommandAnalyser=None):
        self._code_text_line = code_text_line
        self._line_index = line_index
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._command = None
        self._analyse_line(previous_command)

    def _analyse_line(self, previous_command:CommandAnalyser):
        if self._code_text_line.replace(' ', '') in ('{', '}'):
            print(f"Unexpected {{ or }}: {self._code_text_line.replace(' ', '')}")
            return
        elif self._code_text_line.replace(' ', '') == "":
            print(f"Unexpected empty line")
            return
        code_split = self._code_text_line.split(':')
        func_name = code_split[0].replace(' ', '')
        op_code_list = re.findall(r"\{(.*?)\}", code_split[1])
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["func_name"] == func_name]
        if op_info:
            op_info = op_info[0]
        else:
            print(f"Didn't find func name: {func_name}, assuming stop")
            op_info = self.game_data.ai_data_json['op_code_info'][0]

        # Adding missing param when needed
        if op_info['size'] != len(op_code_list):
            if op_info['op_code'] == 2 and len(op_code_list) in (4, 5):  # IF
                op_code_original_str_list = op_code_list.copy()
                op_code_list = []

                # Subject ID (0)
                subject_id = op_code_original_str_list[3]
                op_code_list.append(subject_id)
                # Left condition (1)
                op_code_list.append(op_code_original_str_list[0])
                # Comparison (2)
                op_code_list.append(op_code_original_str_list[1])
                # Right condition (3)
                op_code_list.append(op_code_original_str_list[2])
                # Unused value (called debug) (4)
                if len(op_code_list) == 5:
                    op_code_list.append(op_code_original_str_list[5])
                elif len(op_code_list) == 4:
                    op_code_list.append(0)
                # Expanding jump (5 and 6)
                jump_2_byte = int(op_code_original_str_list[4]).to_bytes(byteorder="little", length=2)
                op_code_list.append(int.from_bytes([jump_2_byte[0]]))
                op_code_list.append(int.from_bytes([jump_2_byte[1]]))


            elif op_info['op_code'] == 35 and len(op_code_list) in (0, 1):
                if len(op_code_list) == 0:  # ENDIF
                    op_code_list = [0, 0]  # Endif is a jump to 0
                else:  # Expanding jump
                    jump_2_byte = int(op_code_list[0]).to_bytes(byteorder="little", length=2)
                    byte1 = int.from_bytes([jump_2_byte[0]])
                    byte2 = int.from_bytes([jump_2_byte[1]])
                    op_code_list = [byte1, byte2]
            elif op_info['op_code'] == 45 and len(op_code_list) == 2:
                target = 900 - int(op_code_list[1])
                low_byte = target // 256
                high_byte = target - (low_byte*256)
                op_code_list[1] = high_byte
                op_code_list.append(low_byte)
            else:
                print(
                    f"When analysing command, wrong size of parameter ({len(op_code_list)} instead of {op_info['size']}) with op id unexpected {op_info['op_code']}")
        # Putting the parameters in the correct order (if not done previously)
        else:
            original_op_list = op_code_list.copy()
            for i, param_index in enumerate(op_info['param_index']):
                op_code_list[param_index] = original_op_list[i]

        self._command = CommandAnalyser(op_id=op_info['op_code'], op_code=op_code_list, game_data=self.game_data, info_stat_data=self.enemy_data.info_stat_data,
                                line_index=self._line_index, text_param=True, previous_command=previous_command)

    def get_command(self):
        return self._command


class CodeIfSection:
    def __init__(self, game_data: GameData, enemy_data, section_lines, line_index, next_line:str, section_previous_command:CommandAnalyser=None):
        self._section_lines = section_lines
        self._line_index = line_index
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._command_list = []
        self._section_size = 0
        self._next_line = next_line
        self._connected_else = False
        self.analyse_section(section_previous_command)

    def analyse_section(self, section_previous_command:CommandAnalyser):
        # First remove first bracket and last bracket
        next_line_to_start = 1  # Starting after the IF
        end_line = len(self._section_lines)
        if self._section_lines[1].replace(' ', '') == '{':
            next_line_to_start += 1
        else:
            print(f"Not a bracket following if: {self._section_lines[1]}")
        if self._section_lines[-1].replace(' ', '') == '}':
            end_line -= 1
        else:
            print(f"Not a bracket ending if: {self._section_lines[-1]}")
        # Checking the section is correct
        ## Size should be at least 2
        if len(self._section_lines) < 2:
            print(f"Section too short, should be at least 2, but it's {len(self._section_lines)} lines")
        ## IF first line is an IF
        op_if_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 2][0]
        op_else_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 35][0]
        if op_if_info['func_name'] not in self._section_lines[0]:
            print(f"Unexpected first line of if section: {self._section_lines[0]}")

        # Analysing the content of the IF
        self._command_list = CodeAnalyseTool.analyse_loop(self._section_lines[next_line_to_start:end_line], op_if_info['func_name'], op_else_info['func_name'],
                                                          self.game_data, self.enemy_data)
        # Adding an endif to the if only if next is not an else
        else_name = op_else_info['func_name'] + ":"
        if not else_name in self._next_line:
            if self._command_list:
                previous_command = self._command_list[-1]
            else:
                previous_command = None
            end_command = CommandAnalyser(op_id=35, op_code=[0, 0], game_data=self.game_data, info_stat_data=self.enemy_data.info_stat_data,
                                  line_index=self._line_index + len(self._section_lines) - 1, previous_command=previous_command)
            self._command_list.append(end_command)
        else:
            # As we don't add the ENDIF here, but still need to jump over the jump func, we had the 3 size
            self._connected_else = True
        # Now we can insert on first line the complete if
        if_command = CodeLine(game_data=self.game_data, enemy_data=self.enemy_data, code_text_line=self._section_lines[0] + f"{{{self.get_size()}}}",
                              line_index=self._line_index, previous_command=section_previous_command)
        self._command_list.insert(0, if_command.get_command())

    def get_command(self):
        return self._command_list

    def get_nb_line(self):
        return len(self._section_lines)

    def get_size(self):
        size = 0
        for command in self._command_list:
            if command:
                size += command.get_size()
        if  self._connected_else:
            size+= 3
        return size


class CodeElseSection:
    def __init__(self, game_data: GameData, enemy_data, section_lines, line_index, section_previous_command:CommandAnalyser=None):
        self._section_lines = section_lines
        self._line_index = line_index
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._command_list = []
        self._section_size = 0
        self.analyse_section(section_previous_command)

    def analyse_section(self, previous_section_command:CommandAnalyser):
        if len(self._section_lines) <= 1:
            return
        # First remove first bracket and last bracket
        next_line_to_start = 1  # Starting after the IF
        end_line = len(self._section_lines)
        if self._section_lines[1].replace(' ', '') == '{':
            next_line_to_start += 1
        else:
            print(f"Not a bracket following if: {self._section_lines[1]}")
        if self._section_lines[-1].replace(' ', '') == '}':
            end_line -= 1
        else:
            print(f"Not a bracket ending if: {self._section_lines[-1]}")
        # Checking the section is correct
        ## If first line is an else
        op_if_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 2][0]
        op_else_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 35][0]
        if op_else_info['func_name'] not in self._section_lines[0]:
            print(f"Unexpected first line of else section: {self._section_lines[0]}")

        # Analysing the content of the IF
        if self._command_list:
            previous_command = self._command_list[-1]
        else:
            previous_command = None
        self._command_list = CodeAnalyseTool.analyse_loop(self._section_lines[next_line_to_start:end_line], op_if_info['func_name'], op_else_info['func_name'],
                                                          self.game_data, self.enemy_data, section_previous_command=previous_command)
        # Compute size of else
        else_command = CodeLine(game_data=self.game_data, enemy_data=self.enemy_data, code_text_line=self._section_lines[0] + f"{{{self.get_size()}}}",
                                line_index=self._line_index, previous_command=previous_section_command)
        self._command_list.insert(0, else_command.get_command())

    def get_command(self):
        return self._command_list

    def get_nb_line(self):
        return len(self._section_lines)

    def get_size(self):
        size = 0
        for command in self._command_list:
            size += command.get_size()
        return size


class CodeAnalyser:
    def __init__(self, game_data: GameData, enemy_data: MonsterAnalyser, code_text_split):
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._original_code_text = code_text_split
        self._section_lines = code_text_split
        self._command_list = []
        self.analyse_code()

    def analyse_code(self):
        print("analyse code")
        """The idea is to go through each line, analyse it and remove the text line while adding the command in the list
        First, we search for an if. Having the line index of this if, we know each previous lines are normal command"""
        op_if_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 2][0]
        op_else_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 35][0]
        temp_command_list = CodeAnalyseTool.analyse_loop(self._section_lines, op_if_info['func_name'], op_else_info['func_name'], self.game_data,
                                                          self.enemy_data)

        print(temp_command_list)

        # Changing line index of each command as they should be in the correct order
        # Also remove empty lines
        index = 0
        for i in range(len(temp_command_list)):
            if temp_command_list[i]:
                self._command_list.append(temp_command_list[i])
                self._command_list[-1].line_index =index
                index +=1
            else:
                continue
        print(temp_command_list)


    def get_command(self):
        return self._command_list
