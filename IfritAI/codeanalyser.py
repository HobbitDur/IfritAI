from typing import List
import re
from FF8GameData.gamedata import GameData
from IfritAI.command import Command

class CodeAnalyseTool:
    @classmethod
    def searching_if(cls, lines:List[str], if_func_name:str):
        print(f"searching_if")
        print(f"lines: {lines}")
        # Now searching for IF in the section
        index_start_if = -1
        index_end_if = -1
        for i in range(len(lines)):
            print(f"Current line: {lines[i]}")
            if if_func_name+":" in lines[i].replace(' ', ''):  # New if found
                print("New if found !")
                index_start_if = i
                # Now searching the end
                # Searching the closing bracket of this if. If there is other open bracket, it means we need to search one more close bracket for this if.
                number_close_bracket_to_search = 0
                for j in range(i+1,  len(lines)):
                    print(f"j: {j}")
                    print(f"Current line j: {lines[j]}")
                    if lines[j].replace(' ', '') == '{':
                        number_close_bracket_to_search +=1
                    elif lines[j].replace(' ', '') == '}':
                        number_close_bracket_to_search -=1
                    if number_close_bracket_to_search == 0:
                        index_end_if = j
                        break
                break
        return index_start_if, index_end_if

    @classmethod
    def analyse_lines(cls, section_lines, game_data, enemy_data):
        command_list = []
        for i in range(len(section_lines)):
            new_code_line = CodeLine(game_data, enemy_data, section_lines[i], i)
            command_list.append(new_code_line.get_command())
        return command_list

    @classmethod
    def analyse_loop(cls, section_lines, func_name, game_data, enemy_data):
        command_list = []
        print("Starting looping !")
        while True:
            command_list_temp, if_index, last_line = CodeAnalyseTool().analyse_one_round(section_lines,func_name, game_data,enemy_data)
            print(f"One round done: if_index: {if_index}, last_line: {last_line}")
            print(f"command_list_temp: {command_list_temp}, ")
            command_list.extend(command_list_temp)
            if if_index < 0:
                break
        command_list.extend(CodeAnalyseTool.analyse_lines(section_lines[last_line:], game_data,enemy_data))
        return command_list

    @classmethod
    def analyse_one_round(cls, section_lines, func_name, game_data, enemy_data):
        print("analyse_one_round")
        # Searching for IF in the section
        if_start_index, if_end_index = CodeAnalyseTool.searching_if(section_lines, func_name)
        print(f"if_start_index: {if_start_index}, if_end_index:{if_end_index} ")
        if if_start_index == -1:  # Didn't find any if, we analyse till the end:
            print("No if found, finishing analysing")
            end_analyse_line = len(section_lines)
        else:
            print("New if found, analysing only till if")
            end_analyse_line = if_start_index

        # Analysing all normal command before the if (till the end if no one found)
        command_list = CodeAnalyseTool.analyse_lines(section_lines[:end_analyse_line], game_data,enemy_data)

        last_line = end_analyse_line
        # Analysing the if section if found one
        if if_start_index != -1:
            if_section_command_list = CodeIfSection(game_data, enemy_data, section_lines[if_start_index: if_end_index + 1], if_start_index)
            command_list.extend(if_section_command_list.get_command())
            last_line+=if_section_command_list.get_size()
        return command_list, if_start_index, last_line

class CodeLine:
    def __init__(self, game_data:GameData, enemy_data, code_text_line, line_index):
        self._code_text_line = code_text_line
        self._line_index = line_index
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._command = None
        self._analyse_line()

    def _analyse_line(self):
        self._code_text_line.replace(' ', '')
        code_split = self._code_text_line.split(':')
        func_name = code_split[0]
        param_list = re.findall(r"\{(.*?)\}", code_split[1])
        op_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["func_name"] == func_name]
        if op_info:
            op_info = op_info[0]
        else:
            print(f"Didn't find func name: {func_name}, assuming stop")
            op_info = self.game_data.ai_data_json['op_code_info'][0]

        self._command = Command(op_info["op_code"], param_list, self.game_data, info_stat_data=self.enemy_data.info_stat_data,
                                      battle_text=self.enemy_data.battle_script_data['battle_text'], line_index=self._line_index)

    def get_command(self):
        return self._command

class CodeIfSection:
    def __init__(self, game_data:GameData, enemy_data, section_lines, line_index):
        self._section_lines = section_lines
        self._line_index = line_index
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._command_list = []
        self._section_size = 0
        self.analyse_section()

    def analyse_section(self):
        print("Analysing if section")
        print(f"section_line: {self._section_lines}")
        # First remove first bracket and last bracket
        if self._section_lines[1].replace(' ', '')== '{':
            del self._section_lines[1]
        else:
            print(f"Not a bracket following if: {self._section_lines[1]}")
        if self._section_lines[-1].replace(' ', '')== '}':
            del self._section_lines[-1]
        else:
            print(f"Not a bracket ending if: {self._section_lines[-1]}")
        print(f"section_line after bracket removal: {self._section_lines}")
        # Checking the section is correct
        ## Size should be at least 2
        if len(self._section_lines) < 2:
            print(f"Section too short, should be at least 2, but it's {len(self._section_lines)} lines")
        ## IF first line is an IF
        op_if_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 2][0]
        if op_if_info['func_name'] not in self._section_lines[0]:
            print(f"Unexpected first line of if section: {self._section_lines[0]}")


        self._command_list = CodeAnalyseTool.analyse_loop(self._section_lines[1:],op_if_info['func_name'],  self.game_data, self.enemy_data)

        print(f"Code if section list: {self._command_list}")

    def get_command(self):
        return self._command_list

    def get_size(self):
        return len(self._section_lines)




class CodeAnalyser:
    def __init__(self, game_data:GameData, enemy_data, code_text_split):
        self.game_data = game_data
        self.enemy_data = enemy_data
        self._original_code_text = code_text_split
        self._section_lines = code_text_split
        self._command_list = []
        self.analyse_code()


    def analyse_code(self):
        """The idea is to go through each line, analyse it and remove the text line while adding the command in the list
        First, we search for an if. Having the line index of this if, we know each previous lines are normal command"""
        op_if_info = [x for x in self.game_data.ai_data_json['op_code_info'] if x["op_code"] == 2][0]
        print("Starting analysing the code")
        print(f"Split text: {self._section_lines}")
        self._command_list = CodeAnalyseTool.analyse_loop( self._section_lines,op_if_info['func_name'], self.game_data, self.enemy_data)
        print(f"Coode analyser list: { self._command_list}")

    def get_command(self):
        return self._command_list

