from FF8GameData.gamedata import GameData
import re


class Command:

    def __init__(self, op_id: int, op_code: list, game_data: GameData, battle_text=(), info_stat_data={},
                 line_index=0, color="#0055ff", code_text=None):
        self.__op_id = op_id
        self.__op_code = op_code
        self.__battle_text = battle_text
        self.__text_colored = ""
        self.game_data = game_data
        self.info_stat_data = info_stat_data
        self.__color_param = color
        self.line_index = line_index
        self.__if_index = 0
        self.was_physical = False
        self.was_magic = False
        self.was_item = False
        self.was_gforce = False
        self.type_data = []
        self.id_possible_list = [{'id': x['op_code'], 'data': x['short_text']} for x in self.game_data.ai_data_json['op_code_info']]
        self.param_possible_list = []
        self.__size = 0
        self.__raw_text = ""
        self.__raw_parameters = []
        if not code_text:
            self.__analyse_op_data()
        else:
            self.__analyse_text_data(code_text)

    def __str__(self):
        return f"ID: {self.__op_id}, op_code: {self.__op_code}, text: {self.get_text()}"

    def __repr__(self):
        return self.__str__()

    def reset_data(self):
        self.was_physical = False
        self.was_magic = False
        self.was_item = False
        self.was_gforce = False
        self.param_possible_list = []
        self.__if_index = 0
        self.type_data = []
        self.__size = 0
        self.__raw_text = ""
        self.__raw_parameters = []

    def set_color(self, color):
        self.__color_param = color
        self.__analyse_op_data()

    def set_op_id(self, op_id):
        self.reset_data()
        self.__op_id = op_id
        op_info = self.__get_op_code_line_info()
        self.__op_code = [0] * op_info["size"]

        self.id_possible_list = [{'id': x['op_code'], 'data': x['short_text']} for x in self.game_data.ai_data_json['op_code_info']]
        self.__analyse_op_data()

    def set_op_code(self, op_code):
        self.reset_data()
        self.__op_code = op_code
        self.__analyse_op_data()

    def get_id(self):
        return self.__op_id

    def get_op_code(self):
        return self.__op_code

    def get_text(self, with_size=True, raw=False, for_code=False):
        if for_code:
            print("get_text for code")
            print(self.__raw_text)
            print(self.__raw_parameters)
        text = self.__raw_text
        parameters = self.__raw_parameters
        if for_code:
            parameters = []
            for parameter in self.__raw_parameters:
                parameters.append('{' + str(parameter) + '}')
        if not raw:
            text = text.format(*parameters)
        if with_size:
            text += " (size:{}bytes)".format(self.__size)
        return text

    def set_if_index(self, if_index):
        self.__if_index = if_index

    def __get_op_code_line_info(self):
        all_op_code_info = self.game_data.ai_data_json["op_code_info"]
        op_research = [x for x in all_op_code_info if x["op_code"] == self.__op_id]
        if op_research:
            op_research = op_research[0]
        else:
            print("No op_code defined for op_id: {}".format(self.__op_id))
            op_research = [x for x in all_op_code_info if x["op_code"] == 255][0]
        return op_research

    def __analyse_text_data(self, code_text):
        print("__analyse_text_data")
        op_code_list = re.findall(r"\{(.*?)\}", code_text)
        text_without_op_code = code_text
        for match in op_code_list:
            text_without_op_code = text_without_op_code.replace('{' + match + '}', '{}')

        print(f"Code text: {code_text}")
        print(f"op_code_list: {op_code_list}")

        # Matching for simple one
        op_code_dict_current = None
        for op_code_dict in self.game_data.ai_data_json['op_code_info']:
            if op_code_dict['text'] == text_without_op_code:
                op_code_dict_current = op_code_dict
                break
        print(f"Simple op dict: {op_code_dict_current}")
        if op_code_dict_current:
            for i, param_type in enumerate(op_code_dict_current['param_type']):
                if param_type == "int":
                    op_code_list[i] = int(op_code_list[i])
                if param_type == "percent":
                    op_code_list[i] = int(int(op_code_list[i]) / 10)
                elif param_type == "var":
                    op_code_list[i] = [x['op_code'] for x in self.game_data.ai_data_json['list_var'] if x['var_name'] == op_code_list[i]][0]
                elif param_type == "special_action":
                    op_code_list[i] = [x['id'] for x in self.game_data.special_action_data_json['special_action'] if x['name'] == op_code_list[i]][0]
                elif param_type == "monster_line_ability":
                    if op_code_list[i] == "None":
                        op_code_list[i] = 253  # None means a not existent line, so 253 is the default "garbage" one
                        continue
                    print("monster_line_ability")
                    print(f"op_code_list[i]: {op_code_list[i]}")
                    split_result = op_code_list[i].split(' | ')
                    print(f"split_result | : {split_result}")
                    split_result[0] = split_result[0].replace('Low: ', '')
                    split_result[1] = split_result[1].replace('Med: ', '')
                    split_result[2] = split_result[2].replace('High: ', '')

                    nb_ability_high = len([x for x in self.info_stat_data['abilities_high'] if x['id'] != 0])
                    nb_ability_med = len([x for x in self.info_stat_data['abilities_med'] if x['id'] != 0])
                    nb_ability_low = len([x for x in self.info_stat_data['abilities_low'] if x['id'] != 0])
                    nb_abilities = max(nb_ability_high, nb_ability_med, nb_ability_low)

                    print("Computing abilities")
                    print(f"Abilities high:{self.info_stat_data['abilities_high']}")
                    print(f"Abilities med:{self.info_stat_data['abilities_med']}")
                    print(f"Abilities low:{self.info_stat_data['abilities_low']}")
                    print(f"Split result:{split_result}")

                    for j in range(nb_abilities):
                        print(f"j: {j}")
                        high_text = ""
                        med_text = ""
                        low_text = ""

                        if self.info_stat_data['abilities_high'][j]['type'] == 2:  # Magic
                            high_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_high'][j]['id']]['name']
                        elif self.info_stat_data['abilities_high'][j]['type'] == 4:  # Item
                            high_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_high'][j]['id']]['name']
                        elif self.info_stat_data['abilities_high'][j]['type'] == 8:  # Ability
                            high_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_high'][j]['id']]['name']
                        elif self.info_stat_data['abilities_high'][j]['type'] == 0:  # Emptyness
                            high_text = "None"
                        else:
                            print(f"Unexpected high type ability: {self.info_stat_data['abilities_high'][j]['type']}")
                        print(high_text)
                        if high_text == split_result[2]:
                            if self.info_stat_data['abilities_med'][j]['type'] == 2:  # Magic
                                med_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_med'][j]['id']]['name']
                            elif self.info_stat_data['abilities_med'][j]['type'] == 4:  # Item
                                med_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_med'][j]['id']]['name']
                            elif self.info_stat_data['abilities_med'][j]['type'] == 8:  # Ability
                                med_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_med'][j]['id']]['name']
                            elif self.info_stat_data['abilities_med'][j]['type'] == 0:  # Emptyness
                                med_text = "None"
                            else:
                                print(f"Unexpected med type ability: {self.info_stat_data['abilities_high'][j]['type']}")
                            print(med_text)
                            if med_text == split_result[1]:
                                if self.info_stat_data['abilities_low'][j]['type'] == 2:  # Magic
                                    low_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_low'][j]['id']]['name']
                                elif self.info_stat_data['abilities_low'][j]['type'] == 4:  # Item
                                    low_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_low'][j]['id']]['name']
                                elif self.info_stat_data['abilities_low'][j]['type'] == 8:  # Ability
                                    low_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_low'][j]['id']]['name']
                                elif self.info_stat_data['abilities_low'][j]['type'] == 0:  # Emptyness
                                    low_text = "None"
                                else:
                                    print(f"Unexpected low type ability: {self.info_stat_data['abilities_high'][j]['type']}")
                                print(low_text)
                                if low_text == split_result[0]:
                                    print(f"tutu ! {j}")
                                    op_code_list[i] = j
                                    break
                elif param_type == "ability":
                    op_code_list[i] = [x['id'] for x in self.game_data.enemy_abilities_data_json['abilities'] if x['name'] == op_code_list[i]][0]
                elif param_type == "card":
                    op_code_list[i] = [x['id'] for x in self.game_data.card_data_json['card_info'] if x['name'] == op_code_list[i]][0]
                elif param_type == "monster":
                    op_code_list[i] = [x['id'] for x in self.game_data.monster_data_json['monster'] if x['name'] == op_code_list[i]][0]
                elif param_type == "item":
                    op_code_list[i] = [x['id'] for x in self.game_data.item_data_json['items'] if x['name'] == op_code_list[i]][0]
                elif param_type == "gforce":
                    op_code_list[i] = [x['id'] for x in self.game_data.gforce_data_json['gforce'] if x['name'] == op_code_list[i]][0]
                elif param_type == "target_advanced_specific":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=True, specific=True) if x['data'] == op_code_list[i]][0]
                elif param_type == "target_advanced_generic":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=True, specific=False) if x['data'] == op_code_list[i]][0]
                elif param_type == "target_basic":
                    op_code_list[i] = [x['id'] for x in self.__get_target_list(advanced=False, specific=False) if x['data'] == op_code_list[i]][0]
                elif param_type == "comparator":
                    op_code_list[i] = self.game_data.ai_data_json['list_comparator'].index(op_code_list[i])
                elif param_type == "status_ai":
                    op_code_list[i] = [x['id'] for x in self.game_data.status_data_json['status_ai'] if x['name'] == op_code_list[i]][0]
                elif param_type == "aptitude":
                    op_code_list[i] = [x['aptitude_id'] for x in self.game_data.ai_data_json['aptitude_list'] if x['text'] == op_code_list[i]][0]
                else:
                    print(f"Text data analysis - Unknown type {param_type}, considering a int")
                    op_code_list[i] = int(op_code_list[i])
            # Putting the parameters in the correct order
            print(f"Original op_list: {op_code_list}")
            original_op_list = op_code_list.copy()
            for i, param_index in enumerate(op_code_dict_current['param_index']):
                op_code_list[param_index] = original_op_list[i]
            print(f"after reorder op_list: {op_code_list}")
        # Matching for complex one
        ## Searching which op code correspond
        elif not op_code_dict_current:
            print("Searching complex")
            for op_code_dict in self.game_data.ai_data_json['op_code_info']:
                op_code_list_temp = op_code_list.copy()
                if op_code_dict['complexity'] == 'complex':
                    try:
                        print(f"Working on : {op_code_dict}")
                        print(f"len(op_code_list) : {len(op_code_list)}")
                        print(f"op_code_dict[size] : {op_code_dict["size"]}")

                        # Some op_code have concatenated param
                        print(f"op_code_list: {op_code_list}")

                        # Preparing complex data before analysing (the one that are smaller than expected due to concatenation)
                        if op_code_dict['op_code'] == 35 and len(op_code_list) in (0, 1):
                            if len(op_code_list) == 0:  # ENDIF
                                op_code_list = [0, 0]  # Endif is a jump to 0
                            else:  # Expanding jump
                                jump_2_byte = int(op_code_list[0]).to_bytes(byteorder="little", length=2)
                                print(f"jump_2_byte: {jump_2_byte}")
                                byte1 = int.from_bytes([jump_2_byte[0]])
                                byte2 = int.from_bytes([jump_2_byte[1]])
                                op_code_list = [byte1, byte2]

                        elif op_code_dict['op_code'] == 2 and len(op_code_list) in (5, 6):  # IF
                            op_code_original_str_list = op_code_list.copy()
                            print(f"op_code_original_str_list after copy:  {op_code_original_str_list}")
                            op_code_list = []

                            # Subject ID (0)
                            subject_id = int(op_code_original_str_list[3])
                            op_code_list.append(subject_id)
                            # Left condition (1)
                            if_subject_dict = [x for x in self.game_data.ai_data_json['if_subject'] if x['subject_id'] == subject_id]
                            if if_subject_dict:
                                if_subject_dict = if_subject_dict[0]
                            elif subject_id > 19:  # It's a var
                                if_subject_dict = {"subject_id": op_code_original_str_list[3], "short_text": self.__get_var_name(subject_id),
                                                   "left_text": self.__get_var_name(subject_id), "complexity": "simple", "param_left_type": "var",
                                                   "param_right_type": "int"}
                            print(f"if_subject_dict: {if_subject_dict}")
                            # Now we want to have only the parameter of the subject, for this we remove data around
                            split_text = if_subject_dict['left_text'].split('{}')
                            print(f"split_text: {split_text}")
                            if_subject_left_parameter_text = op_code_original_str_list[0].replace(split_text[0], '')
                            if len(split_text) > 1:
                                if_subject_left_parameter_text = if_subject_left_parameter_text.replace(split_text[1], '')

                            print(f"if_subject_left_parameter_text: {if_subject_left_parameter_text}")
                            if if_subject_dict['param_left_type'] == "int":
                                op_code_list.append(int(if_subject_left_parameter_text))
                            elif if_subject_dict['param_left_type'] == "var":
                                print("VAR AJJAJ")
                                print(if_subject_dict)
                                print(if_subject_dict['left_text'])
                                op_code_list.append(if_subject_dict['left_text'])
                            elif if_subject_dict['param_left_type'] == "int_shift":
                                if if_subject_dict['subject_id'] == 2:
                                    shift = 1
                                else:
                                    print("unexpected int_shift for subject id: {}")
                                op_code_list.append(int(if_subject_left_parameter_text) + shift)
                            elif if_subject_dict['param_left_type'] in ("target_advanced_specific", "target_advanced_generic"):
                                if if_subject_dict['param_left_type'] == "target_advanced_specific":
                                    target_list = self.__get_target_list(advanced=True, specific=True)
                                if if_subject_dict['param_left_type'] == "target_advanced_generic":
                                    target_list = self.__get_target_list(advanced=True, specific=False)
                                print(f"target_list: {target_list}")
                                target_id = [x['id'] for x in target_list if x['data'] == if_subject_left_parameter_text][0]
                                print(f"target_id: {target_id}")
                                op_code_list.append(int(target_id))
                            elif  if_subject_dict['param_left_type'] == "":
                                op_code_list.append(0)#Unused
                            else:
                                print(f"Unexpected if_subject_dict['param_left_type']: {if_subject_dict['param_left_type']}")
                                op_code_list.append(0)
                            print(f"Before compare: {op_code_list}")
                            # Comparison (2)
                            op_code_list.append(self.game_data.ai_data_json['list_comparator'].index(op_code_original_str_list[1]))
                            print(f"Before right condition: {op_code_list}")
                            # Right condition (3)
                            r_cond = op_code_original_str_list[2]
                            if if_subject_dict['param_right_type'] == "int":
                                op_code_list.append(int(r_cond))
                            elif if_subject_dict['param_right_type'] == "percent":
                                op_code_list.append(int(int(r_cond.replace(' %', '')) / 10))
                            elif if_subject_dict['param_right_type'] == "status_ai":
                                op_code_list.append([x['id'] for x in self.game_data.status_data_json['status_ai'] if x['name'] == r_cond][0])
                            elif if_subject_dict['param_right_type'] == "target_advanced_specific":
                                target_list = self.__get_target_list(advanced=True, specific=True)
                                op_code_list.append([x['id'] for x in target_list if x['data'] == r_cond][0])
                            elif if_subject_dict['param_right_type'] == "target_advanced_generic":
                                target_list = self.__get_target_list(advanced=True, specific=False)
                                op_code_list.append([x['id'] for x in target_list if x['data'] == r_cond][0])
                            elif if_subject_dict['param_right_type'] == "complex":
                                print("TODO")
                                op_code_list.append(0)
                            else:
                                print(f"Unexpected if subject param right type: {if_subject_dict['param_right_type']}")

                            # Unused value (called debug)
                            if len(op_code_original_str_list) == 5:
                                op_code_list.append(0)
                            elif len(op_code_original_str_list) == 6:
                                op_code_list.append(int(op_code_original_str_list[5]))
                            # Expanding jump
                            jump_2_byte = int(op_code_original_str_list[4]).to_bytes(byteorder="little", length=2)
                            print(f"jump_2_byte: {jump_2_byte}")
                            op_code_list.append(int.from_bytes([jump_2_byte[0]]))
                            print(f"op_code_list[5]: {op_code_list[5]}")
                            op_code_list.append(int.from_bytes([jump_2_byte[1]]))
                            print(f"op_code_list[6]: {op_code_list[6]}")

                            print(f"reformatted op_code_list: {op_code_list}")

                        # Now if same size, we can analyse
                        if len(op_code_list) == op_code_dict["size"]:
                            print("Size matter !")

                            if op_code_dict['op_code'] not in (2, 35):  # If not previously analyzed
                                print("Analysing param type")
                                print(f"op_code_dict['param_type']: {op_code_dict['param_type']}")
                                for i in range(len(op_code_list)):
                                    print(f"i: {i}")
                                    print(f"op_code_dict['param_type'][i]: {op_code_dict['param_type'][i]}")
                                    if op_code_dict['param_type'][i] == "int":
                                        op_code_list[i] = int(op_code_list[i])
                                    elif op_code_dict['param_type'][i] == "comparator":
                                        op_code_list[i] = self.game_data.ai_data_json["list_comparator"].index(op_code_list[i])
                                    elif op_code_dict['param_type'][i] == "target_advanced_generic":
                                        op_code_list[i] = \
                                            [x['param_id'] for x in self.game_data.ai_data_json["target_advanced_generic"] if x['text'] == op_code_list[i]][0]
                                    elif op_code_dict['param_type'][i] == "target_advanced_specific":
                                        op_code_list[i] = \
                                            [x['param_id'] for x in self.game_data.ai_data_json["target_advanced_specific"] if x['text'] == op_code_list[i]][0]
                                    elif op_code_dict['param_type'][i] == "target_basic":
                                        op_code_list[i] = [x['param_id'] for x in self.game_data.ai_data_json["target_basic"] if x['text'] == op_code_list[i]][
                                            0]
                                    elif op_code_dict['param_type'][i] == "status_ai":
                                        op_code_list[i] = [x['id'] for x in self.game_data.status_data_json['status_ai'] if x['name'] == op_code_list[i]][0]
                                    elif op_code_dict['param_type'][i] == "battle_text":
                                        op_code_list[i] = self.__battle_text.index(op_code_list[i])
                                    else:
                                        print(f"Unexpected param type: {op_code_dict['param_type'][i]}")
                                original_op_list = op_code_list.copy()
                                op_code_list = []
                                for i, param_index in enumerate(op_code_dict['param_index']):
                                    op_code_list[i] = original_op_list[param_index]

                            call_function = getattr(self, "_Command__op_" + "{:02}".format(op_code_dict["op_code"]) + "_analysis")
                            call_result = call_function(op_code_list)
                            self.__raw_text = call_result[0]
                            self.__raw_parameters = call_result[1]
                            print(f"Raw text: {self.__raw_text}")
                            print(f"text_without_op_code: {text_without_op_code}")
                    except (TypeError, ValueError, IndexError) as e:
                        print("Problem searching for complex")
                        print(repr(e))
                        op_code_list = op_code_list_temp.copy()
                        continue

                    print(f"code_text: {code_text}")
                    print(f"get_text: {self.get_text(with_size=False, raw=False, for_code=True)}")
                    if code_text == self.get_text(with_size=False, raw=False, for_code=True):
                        print("Found it !")
                        op_code_dict_current = op_code_dict
                        break
                        current_raw_parameters = ['<span style="color:' + self.__color_param + ';">' + str(x) + '</span>' for x in call_result[1]]
                op_code_list = op_code_list_temp.copy()

        if not op_code_dict_current:
            print("Didn't find any op_code for this function")
            return "", ""

        print(op_code_dict_current['op_code'])
        print(op_code_list)

        self.set_op_id(op_code_dict_current['op_code'])
        self.set_op_code(op_code_list)

    def __analyse_op_data(self):
        self.reset_data()
        op_info = self.__get_op_code_line_info()
        # Searching for errors in json file
        if len(op_info["param_type"]) != op_info["size"] and op_info['complexity'] == 'simple':
            print(f"Error on JSON for op_code_id: {self.__op_id}")
        if op_info["complexity"] == "simple":
            param_value = []
            for index, type in enumerate(op_info["param_type"]):
                print(f"op_info: {op_info}")
                print(f"index: {index}")
                print(f"type: {type}")
                print(f"self.__op_code: {self.__op_code}")
                op_index = op_info["param_index"][index]
                self.type_data.append(type)
                if type == "int":
                    param_value.append(str(self.__op_code[op_index]))
                    self.param_possible_list.append([])
                elif type == "percent":
                    param_value.append(str(self.__op_code[op_index] * 10))
                    self.param_possible_list.append([])
                elif type == "bool":
                    param_value.append(str(bool(self.__op_code[op_index])))
                    self.param_possible_list.append([{"id": 0, "data": "True"}, {"id": 1, "data": "False"}])
                elif type == "var":
                    # There is specific var known, if not in the list it means it's a generic one
                    param_value.append(self.__get_var_name(self.__op_code[op_index]))
                    self.param_possible_list.append(self.__get_possible_var())
                elif type == "special_action":
                    if self.__op_code[op_index] < len(self.game_data.special_action_data_json["special_action"]):
                        param_value.append(self.game_data.special_action_data_json["special_action"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_special_action())
                    else:
                        param_value.append("UNKNOWN SPECIAL_ACTION")
                elif type == "monster_line_ability":
                    possible_ability_values = []
                    nb_ability_high = len([x for x in self.info_stat_data['abilities_high'] if x['id'] != 0])
                    nb_ability_med = len([x for x in self.info_stat_data['abilities_med'] if x['id'] != 0])
                    nb_ability_low = len([x for x in self.info_stat_data['abilities_low'] if x['id'] != 0])
                    nb_abilities = max(nb_ability_high, nb_ability_med, nb_ability_low)
                    for i in range(nb_abilities):
                        if self.info_stat_data['abilities_high'][i] != 0:
                            if self.info_stat_data['abilities_high'][i]['type'] == 2:  # Magic
                                high_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 4:  # Item
                                high_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 8:  # Ability
                                high_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_high'][i]['id']]['name']
                            elif self.info_stat_data['abilities_high'][i]['type'] == 0:  # Emptyness
                                high_text = "None"
                            else:
                                high_text = "Unexpected type ability"
                        else:
                            high_text = "None"
                        if self.info_stat_data['abilities_med'][i] != 0:
                            if self.info_stat_data['abilities_med'][i]['type'] == 2:  # Magic
                                med_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 4:  # Item
                                med_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 8:  # Ability
                                med_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_med'][i]['id']]['name']
                            elif self.info_stat_data['abilities_med'][i]['type'] == 0:  # Emptyness
                                med_text = "None"
                            else:
                                med_text = "Unexpected type ability"
                        else:
                            med_text = "None"
                        if self.info_stat_data['abilities_low'][i] != 0:
                            if self.info_stat_data['abilities_low'][i]['type'] == 2:  # Magic
                                low_text = self.game_data.magic_data_json["magic"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 4:  # Item
                                low_text = self.game_data.item_data_json["items"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 8:  # Ability
                                low_text = self.game_data.enemy_abilities_data_json["abilities"][self.info_stat_data['abilities_low'][i]['id']]['name']
                            elif self.info_stat_data['abilities_low'][i]['type'] == 0:  # Emptyness
                                low_text = "None"
                            else:
                                low_text = "Unexpected type ability"
                        else:
                            low_text = "None"
                        text = f"Low: {low_text} | Med: {med_text} | High: {high_text}"
                        possible_ability_values.append({'id': i, 'data': text})
                        if self.__op_code[op_index] == i:
                            param_value.append(text)
                    if self.__op_code[op_index] >= nb_abilities:
                        param_value.append("None")
                    possible_ability_values.append({'id': 0, 'data': "None"})  # 253 for None value is often used by monsters.
                    self.param_possible_list.append(possible_ability_values)
                elif type == "ability":
                    if self.__op_code[op_index] < len(self.game_data.enemy_abilities_data_json["abilities"]):
                        param_value.append(self.game_data.enemy_abilities_data_json["abilities"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_ability())
                    else:
                        param_value.append("UNKNOWN CARD")
                elif type == "card":
                    if self.__op_code[op_index] < len(self.game_data.card_data_json["card_info"]):
                        param_value.append(self.game_data.card_data_json["card_info"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_card())
                    else:
                        param_value.append("UNKNOWN CARD")
                elif type == "monster":
                    if self.__op_code[op_index] < len(self.game_data.monster_data_json["monster"]):
                        param_value.append(self.game_data.monster_data_json["monster"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_monster())
                    else:
                        param_value.append("UNKNOWN MONSTER")
                elif type == "item":
                    if self.__op_code[op_index] < len(self.game_data.item_data_json["items"]):
                        param_value.append(self.game_data.item_data_json["items"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_item())
                    else:
                        param_value.append("UNKNOWN ITEM")
                elif type == "status_ai":
                    if self.__op_code[op_index] <= self.game_data.status_data_json["status_ai"][-1]['id']:
                        param_value_temp = [x['name'] for x in self.game_data.status_data_json["status_ai"] if x['id'] == self.__op_code[op_index]]
                        if param_value_temp:
                            param_value.append(param_value_temp[0])
                        else:
                            print(f"Unknown status for id: {self.__op_code[op_index]}")
                            param_value.append(self.__op_code[op_index])
                        self.param_possible_list.append(self.__get_possible_status_ai())
                    else:
                        param_value.append("UNKNOWN STATUS AI")
                elif type == "gforce":
                    if self.__op_code[op_index] < len(self.game_data.gforce_data_json["gforce"]):
                        param_value.append(self.game_data.gforce_data_json["gforce"][self.__op_code[op_index]]['name'])
                        self.param_possible_list.append(self.__get_possible_gforce())
                    else:
                        param_value.append("UNKNOWN GFORCE")
                elif type == "target_advanced_specific":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=True, specific=True))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=True, specific=True)])
                elif type == "target_advanced_generic":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=True, specific=False))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=True, specific=False)])
                elif type == "target_basic":
                    param_value.append(self.__get_target(self.__op_code[op_index], advanced=False))
                    self.param_possible_list.append([x for x in self.__get_target_list(advanced=False)])
                elif type == "comparator":
                    param_value.append(self.game_data.ai_data_json['list_comparator'][self.__op_code[op_index]])
                    self.param_possible_list.append([{"id": i, "data": x} for i, x in enumerate(self.game_data.ai_data_json['list_comparator_html'])])
                elif type == "aptitude":
                    print("APTITUDE")
                    param_value.append([x['text'] for x in self.game_data.ai_data_json['aptitude_list'] if x['aptitude_id'] == self.__op_code[op_index]][0])
                    self.param_possible_list.append([{"id": x["aptitude_id"], "data": x['text']} for x in self.game_data.ai_data_json['aptitude_list']])
                    print(self.param_possible_list)
                else:
                    print(f"Unknown type {type}, considering a int")
                    param_value.append(self.__op_code[op_index])
                print(f"param_value: {param_value}")
            # Now putting the op_list in the correct order for param value (data analysis already in correct order):
            original_param_possible = self.param_possible_list.copy()
            for i, param_index in enumerate(op_info['param_index']):
                self.param_possible_list[param_index] = original_param_possible[i]

            for i in range(len(param_value)):
                param_value[i] = '<span style="color:' + self.__color_param + ';">' + param_value[i] + '</span>'

            self.__raw_text = op_info['text']
            self.__raw_parameters = param_value

        elif op_info["complexity"] == "complex":
            call_function = getattr(self, "_Command__op_" + "{:02}".format(op_info["op_code"]) + "_analysis")
            call_result = call_function(self.__op_code)
            self.__raw_text = call_result[0]
            self.__raw_parameters = ['<span style="color:' + self.__color_param + ';">' + str(x) + '</span>' for x in call_result[1]]
        self.__size = op_info['size'] + 1

    def __get_possible_target_advanced_specific(self):
        return [x for x in self.__get_target_list(advanced=True, specific=True)]

    def __get_possible_target_advanced_generic(self):
        return [x for x in self.__get_target_list(advanced=True, specific=False)]

    def __get_possible_var(self):
        return [{"id": x['op_code'], "data": x['var_name']} for x in self.game_data.ai_data_json["list_var"]]

    def __get_possible_magic(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.magic_data_json["magic"])]

    def __get_possible_magic_type(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.magic_data_json["magic_type"])]

    def __get_possible_item(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.item_data_json["items"])]

    def __get_possible_status_ai(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.status_data_json["status_ai"])]

    def __get_possible_gforce(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.gforce_data_json["gforce"])]

    def __get_possible_monster(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.monster_data_json["monster"])]

    def __get_possible_card(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.card_data_json["card_info"])]

    def __get_possible_status_ai(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.status_data_json["status_ai"])]

    def __get_possible_special_action(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.special_action_data_json["special_action"])]

    def __get_possible_ability(self):
        return [{'id': val_dict['id'], 'data': val_dict['name']} for id, val_dict in enumerate(self.game_data.enemy_abilities_data_json["abilities"])]

    def __op_24_analysis(self, op_code):
        ret = self.__op_01_analysis(op_code)
        ret[0] += ' + unknown action'
        return [ret[0], ret[1]]

    def __op_35_analysis(self, op_code):
        jump = int.from_bytes(bytearray([op_code[0], op_code[1]]), byteorder='little')
        self.param_possible_list.append([])
        self.param_possible_list.append([])
        if jump == 0:
            return ['ENDIF', []]
        else:
            return ['JUMP {} bytes forward', [jump]]

    def __op_45_analysis(self, op_code):
        # op_2D = ['element', 'elementval', '?']
        if op_code[0] < len(self.game_data.magic_data_json['magic']):
            element = self.game_data.magic_data_json['magic'][op_code[0]]
        else:
            element = "UNKNOWN ELEMENT TYPE"
        element_val = op_code[1]
        op_code_unknown = op_code[2]
        param_possible = []
        for i in range(len(self.game_data.magic_data_json['magic'])):
            param_possible.append({'id': i, 'data': self.game_data.magic_data_json['magic'][i]['name']})
        self.param_possible_list.append(param_possible)
        self.param_possible_list.append([])
        self.param_possible_list.append([])
        return ['Resist element {} at {}, unknown value (impact on resist element): {}', [element, element_val, op_code_unknown]]

    def __op_26_analysis(self, op_code):
        analysis = self.__op_01_analysis(op_code)
        analysis[0] += ' AND LOCK BATTLE'
        return analysis

    def __op_01_analysis(self, op_code):
        if op_code[0] < len(self.__battle_text):
            ret = 'SHOW BATTLE TEXT: {}'
            param_return = [self.__battle_text[op_code[0]].get_str()]
        else:
            ret = "/!\\SHOW BATTLE BUT NO BATTLE TO SHOW"
            param_return = []
        possible_param = []
        for i in range(len(self.__battle_text)):
            possible_param.append({'id': i, 'data': self.__battle_text[i].get_str()})
        self.param_possible_list.append(possible_param)
        return [ret, param_return]

    def __op_02_analysis(self, op_code):
        # op_02 = ['subject_id', 'left condition (target)', 'comparator', 'right condition (value)', 'jump1', 'jump2', 'debug']
        subject_id = op_code[0]
        op_code_left_condition_param = op_code[1]
        op_code_comparator = op_code[2]
        op_code_right_condition_param = op_code[3]
        debug_unknown = op_code[4]
        jump_value_op_1 = op_code[5]
        jump_value_op_2 = op_code[6]
        jump_value = int.from_bytes(bytearray([op_code[5], op_code[6]]), byteorder='little')
        target = self.__get_target(op_code_left_condition_param, advanced=True)
        target_advanced_generic = self.__get_target(op_code_left_condition_param, advanced=True, specific=False)
        target_advanced_specific = self.__get_target(op_code_left_condition_param, advanced=True, specific=True)
        if op_code_comparator < len(self.game_data.ai_data_json['list_comparator_html']):
            comparator = self.game_data.ai_data_json['list_comparator_html'][op_code_comparator]
        else:
            comparator = 'UNKNOWN OPERATOR'

        if_subject_left_data = [x for x in self.game_data.ai_data_json["if_subject"] if x["subject_id"] == subject_id]
        list_param_possible_left = []
        list_param_possible_right = []

        # Analysing left subject
        if if_subject_left_data:
            if_subject_left_data = if_subject_left_data[0]
            if if_subject_left_data["complexity"] == "simple":
                if if_subject_left_data['param_left_type'] == "target_basic":
                    param_left = target
                    list_param_possible_left.extend(self.__get_target_list(advanced=False))
                elif if_subject_left_data['param_left_type'] == "target_advanced_generic":
                    param_left = target_advanced_generic
                    list_param_possible_left.extend(self.__get_target_list(advanced=True))
                elif if_subject_left_data['param_left_type'] == "target_advanced_specific":
                    param_left = target_advanced_specific
                    list_param_possible_left.extend(self.__get_target_list(advanced=True))
                elif if_subject_left_data['param_left_type'] == "int":
                    param_left = op_code_left_condition_param
                elif if_subject_left_data['param_left_type'] == "":
                    param_left = "UNKNOWN {}".format(op_code_left_condition_param)
                else:
                    print("Unexpected param_left_type: {}".format(if_subject_left_data['param_left_type']))
                    param_left = op_code_left_condition_param
                    list_param_possible_left.append({"id:": op_code_left_condition_param, "data": "Unused"})
            elif if_subject_left_data["complexity"] == "complex":
                if if_subject_left_data["subject_id"] == 2:  # RANDOM VALUE
                    param_left = op_code_left_condition_param - 1  # The random value is between 0 and the param - 1
                elif if_subject_left_data["subject_id"] == 15:  # ALLY SLOT X IS ALIVE
                    param_left = op_code_right_condition_param - 3 # Special case where we take the right condition
                else:
                    print(f"Unexpected subject_id: {if_subject_left_data["subject_id"]}")
                    param_left = op_code_left_condition_param
            else:
                print(f"Unexpected complexity: {if_subject_left_data["complexity"]}")
                param_left = op_code_left_condition_param
            left_subject = {'text': if_subject_left_data["left_text"], 'param': param_left}
        elif subject_id > 19:
            left_subject = {'text': '{}', 'param': self.__get_var_name(subject_id)}
        else:
            left_subject = {'text': 'UNKNOWN SUBJECT', 'param': None}

        # Analysing right subject
        right_param_type = [x['param_right_type'] for x in self.game_data.ai_data_json['if_subject'] if x['subject_id'] == subject_id]
        if right_param_type:
            right_param_type = right_param_type[0]

            if right_param_type == 'percent':
                right_subject = {'text': '{} %', 'param': [op_code_right_condition_param * 10]}
            elif right_param_type == 'int':
                right_subject = {'text': '{}', 'param': [op_code_right_condition_param]}
            elif right_param_type == 'status_ai':
                param = [x['name'] for x in self.game_data.status_data_json["status_ai"] if x['id'] == op_code_right_condition_param]
                right_subject = {'text': '{}', 'param': [param[0]]}
                list_param_possible_right = self.__get_possible_status_ai()
            elif right_param_type == 'target_advanced_specific':
                right_subject = {'text': '{}', 'param': [self.__get_target(op_code[3], advanced=True, specific=True)]}
            elif right_param_type == 'text':
                right_subject = {'text': '{}', 'param': [self.game_data.ai_data_json['if_subject']['right_text']]}
            elif right_param_type == 'target_advanced_generic':
                right_subject = {'text': '{}', 'param': [self.__get_target(op_code[3], advanced=True, specific=False)]}
            elif right_param_type == 'complex' and subject_id == 10:
                attack_left_text = "{}"
                attack_left_condition_param = str(op_code[1])
                sum_text = ""
                list_param_possible_left.extend(
                    [{'id': x['param_id'], 'data': [sum_text + y for y in x['text']][-1]} for x in self.game_data.ai_data_json['subject_left_10']])
                attack_right_text = "{}"
                attack_right_condition_param = [str(op_code[3])]
                subject_left_data = [x['text'] for x in self.game_data.ai_data_json['subject_left_10'] if x['param_id'] == op_code[1]]
                if not subject_left_data:
                    attack_left_text = "Unknown last attack {}"
                else:
                    attack_left_condition_param = subject_left_data[0][0]
                if op_code[1] == 0:
                    list_param_possible_right.extend(self.game_data.ai_data_json['attack_type'])
                    attack_right_condition_param = [self.game_data.ai_data_json['attack_type'][op_code[3]]['type']]
                elif op_code[1] == 1:
                    attack_right_condition_param = [self.__get_target(op_code_right_condition_param, advanced=True)]
                    list_param_possible_right.extend(self.__get_possible_target_advanced())
                elif op_code[1] == 2:
                    attack_left_condition_param = attack_left_condition_param.format("self")
                elif op_code[1] == 3:  # Need to handle better the was_magic
                    list_param_possible_right.extend(
                        [{"id": 1, "data": "Physical damage"}, {"id": 2, "data": "Magical damage"}, {"id": 4, "data": "Item"}, {"id": 254, "data": "G-Force"}])
                    if op_code_right_condition_param == 1:
                        attack_right_condition_param = ["Physical damage"]
                        self.was_physical = True
                    elif op_code_right_condition_param == 2:
                        attack_right_condition_param = ["Magical damage"]
                        self.was_magic = True
                    elif op_code_right_condition_param == 4:
                        attack_right_condition_param = ["Item"]
                        self.was_item = True
                    elif op_code_right_condition_param == 254:
                        attack_right_condition_param = ["G-Force"]
                        self.was_force = True
                    else:
                        attack_right_condition_param = ["Unknown {}".format(op_code_right_condition_param)]
                elif op_code[1] == 4:
                    if op_code_right_condition_param >= 64:
                        attack_left_condition_param = subject_left_data[0][0]
                        attack_right_condition_param = [self.game_data.gforce_data_json["gforce"][op_code_right_condition_param - 64]['name']]
                        list_param_possible_right.extend(self.__get_possible_gforce())
                    else:
                        if self.was_magic:
                            ret = self.game_data.magic_data_json["magic"][op_code_right_condition_param]['name']
                            list_param_possible_right.extend(self.__get_possible_magic())
                        elif self.was_item:
                            ret = self.game_data.item_data_json["items"][op_code_right_condition_param]['name']
                            list_param_possible_right.extend(self.__get_possible_item())
                        elif self.was_physical:
                            ret = self.game_data.special_action_data_json["special_action"][op_code_right_condition_param]['name']
                            list_param_possible_right.extend(self.__get_possible_special_action())
                        else:
                            ret = str(op_code_right_condition_param)
                        attack_left_condition_param = subject_left_data[0][1]
                        attack_right_condition_param = [ret]
                        self.was_magic = False
                        self.was_item = False
                        self.was_physical = False
                elif op_code[1] == 5:
                    attack_right_condition_param = [str(self.game_data.magic_data_json['magic_type'][op_code_right_condition_param]['name'])]
                    list_param_possible_right.extend(self.__get_possible_magic_type())
                else:
                    attack_left_text = "Unknown attack type {}"
                    attack_left_condition_param = str(op_code[1])
                    attack_right_condition_param = [op_code_right_condition_param]

                left_subject = {'text': attack_left_text, 'param': attack_left_condition_param}
                right_subject = {'text': attack_right_text, 'param': attack_right_condition_param}
        else:
            print(f"Unexpected subject id: {subject_id}")
            right_subject = {'text': '{}', 'param': [op_code_right_condition_param]}

        left_subject_text = left_subject['text'].format(left_subject['param'])
        right_subject_text = right_subject['text'].format(*right_subject['param'])

        param_possible_sub_id = []
        param_possible_sub_id.extend(
            [{"id": x['subject_id'], "data": x['short_text']} for x in self.game_data.ai_data_json["if_subject"]])
        param_possible_sub_id.extend(
            [{"id": x['op_code'], "data": x['var_name']} for x in self.game_data.ai_data_json["list_var"]])
        # op_02 = ['subject_id', 'left condition (target)', 'comparator', 'right condition (value)', 'jump1', 'jump2', 'debug']
        # List of "Subject id" possible list
        self.param_possible_list.append(param_possible_sub_id)
        # List of "Left subject" possible list
        if if_subject_left_data:
            self.param_possible_list.append(list_param_possible_left)
        else:
            self.param_possible_list.append([{"id": op_code_left_condition_param, "data": "UNUSED"}])
        # List of "Comparator" possible list
        self.param_possible_list.append([{"id": i, "data": self.game_data.ai_data_json["list_comparator"][i]} for i in
                                         range(len(self.game_data.ai_data_json["list_comparator"]))])
        # List of "Right subject" possible list
        self.param_possible_list.append(list_param_possible_right)
        # List of "Jump1" possible list
        self.param_possible_list.append([])
        # List of "Jump2" possible list
        self.param_possible_list.append([])
        # List of "Debug" possible list
        self.param_possible_list.append([])

        if op_code[4] != 0:
            return ["IF {} {} {} (Subject ID:{}) | ELSE jump {} bytes forward | Debug: {}",
                    [left_subject_text, comparator, right_subject_text, subject_id, jump_value, op_code[4]]]
        else:
            return ["IF {} {} {} (Subject ID:{}) | ELSE jump {} bytes forward",
                    [left_subject_text, comparator, right_subject_text, subject_id, jump_value]]

    def __op_39_analysis(self, op_code):
        # Apply status

        if op_code[0] < len(self.game_data.status_data_json['status_ai']):
            status = self.game_data.status_data_json['status_ai'][op_code[0]]['name']
        else:
            status = "UNKNOWN STATUS"
        if op_code[1] == 1:
            activation_text = "ACTIVATE"
        elif op_code[1] == 0:
            activation_text = "DEACTIVATE"
        else:
            activation_text = "UNKNOWN ACTIVATION BYTE"
        self.param_possible_list.append([])
        return ['{} STATUS {} to {}', [activation_text, status, self.info_stat_data['monster_name']]]

    def __get_var_name(self, id):
        # There is specific var known, if not in the list it means it's a generic one
        all_var_info = self.game_data.ai_data_json["list_var"]
        var_info_specific = [x for x in all_var_info if x["op_code"] == id]
        if var_info_specific:
            var_info_specific = var_info_specific[0]['var_name']
        else:
            var_info_specific = "var" + str(id)
        return var_info_specific

    def __get_target_list(self, advanced=False, specific=False):
        list_target = []
        # The target list has 4 different type of target:
        # 1. The characters
        # 2. All monsters of the game
        # 3. Special target
        # 4. Target stored in variable

        if advanced:
            for i in range(len(self.game_data.ai_data_json['list_target_char'])):
                list_target.append({"id": i, "data": self.game_data.ai_data_json['list_target_char'][i]})
        for i in range(0, len(self.game_data.monster_data_json["monster"])):
            list_target.append({"id": i + 16, "data": self.game_data.monster_data_json["monster"][i]["name"]})
        number_of_generic_var_read = 0
        for var_data in self.game_data.ai_data_json['list_var']:
            if var_data['op_code'] == 220 + number_of_generic_var_read:
                list_target.append({"id": number_of_generic_var_read + 220, "data": "TARGET TYPE IN: " + var_data['var_name']})
                number_of_generic_var_read += 1

        if advanced:
            if specific:
                list_target_data = self.game_data.ai_data_json['target_advanced_specific']
            else:
                list_target_data = self.game_data.ai_data_json['target_advanced_generic']
        else:
            list_target_data = self.game_data.ai_data_json['target_basic']

        for el in list_target_data:
            if el['param_type'] == "monster_name":
                data = "self"
            elif el['param_type'] == "":
                data = None
            else:
                print("Unexpected param type for target: {}".format(el['param_type']))
                data = None
            if data:
                text = el['text'].format(data)
            else:
                text = el['text']
            list_target.append({"id": el['param_id'], "data": text})
        return list_target

    def __get_target(self, id, advanced=False, specific=False):
        target = [x['data'] for x in self.__get_target_list(advanced, specific) if x['id'] == id]
        if target:
            return target[0]
        else:
            print("Unexpected target with id: {}".format(id))
            return "UNKNOWN TARGET"
