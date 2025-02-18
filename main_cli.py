import argparse
import pathlib
import shutil
import re

from FF8GameData.gamedata import GameData
from FF8GameData.dat.monsteranalyser import MonsterAnalyser
from IfritAI.codeanalyser import CodeAnalyser
from IfritAI.codewidget import CodeWidget

if __name__ == '__main__':

    parser = argparse.ArgumentParser("Ifritai_cli")
    parser.add_argument("export_import", help="If you want to export (create .md) or import (read .md)", type=str, choices=["export", "import"])
    parser.add_argument("game_data_folder", help="The FF8GameData folder", type=pathlib.Path)
    parser.add_argument("original_com_folder", help="Folder that contains all com file to modify", type=pathlib.Path)
    parser.add_argument("doc_folder", help="Folder that contains all md file containing the ifritCode. Each file must have the same name than the c0mxxx file.", type=pathlib.Path)
    parser.add_argument("output_com_folder", help="Folder that will contains the modified c0mxxx file.", type=pathlib.Path)
    #parser.add_argument("xlsx_file", help="Folder that contains all md file containing the ifritCode. Each file must have the same name than the c0mxxx file.", type=pathlib.Path)
    args = parser.parse_args()

    print(args.original_com_folder)
    print(args.doc_folder)
    print(args.output_com_folder)

    # List all .dat files in com_folder
    dat_files = list(args.original_com_folder.glob('*.dat'))

    if args.export_import == "export":
        # List all .md files in doc_folder
        md_files = list(args.doc_folder.glob('*.md'))

        # Extract filenames without extensions for comparison
        dat_names = {file.stem for file in dat_files}  # Set of filenames without extensions
        md_names = {file.stem for file in md_files}  # Set of filenames without extensions

        # Find common filenames (ignoring extensions)
        common_names = dat_names.intersection(md_names)

        # Create new_list with files from com_folder that have matching names
        com_to_modify_list = [file for file in dat_files if file.stem in common_names]

        # Print results
        print("All .dat files in com_folder:")
        for file in dat_files:
            print(file)

        print("\nAll .md files in doc_folder:")
        for file in md_files:
            print(file)

        # Copy files from new_list to output_com_folder and store their new paths
        copied_files = []
        for file in com_to_modify_list:
            destination = args.output_com_folder / file.name
            shutil.copy(file, destination)
            copied_files.append(destination)

        game_data = GameData(args.game_data_folder)


        for index_file in range(len(copied_files)):
            # Load com file
            game_data.load_all()
            enemy = MonsterAnalyser(game_data)
            enemy.load_file_data(copied_files[index_file], game_data)
            enemy.analyse_loaded_data(game_data)
            #code_widget = CodeWidget(game_data, ennemy_data=enemy, expert_level=3)

            # Read .md file
            # Define the path to the .md file

            # Read the content of the .md file
            with open(md_files[index_file], 'r', encoding='utf-8') as file:
                content = file.read()

            # Use regex to extract all code blocks between ```
            code_blocks = re.findall(r'```.*?\n(.*?)\n```', content, re.DOTALL)

            # Print each extracted code block
            # for i, code in enumerate(code_blocks, start=1):
            #     print(f"Code Block {i}:\n{code}\n{'-' * 40}")

            # Analyse code
            for index_code, code in enumerate(code_blocks):
                code_analyser = CodeAnalyser(game_data, enemy, code.splitlines())
                code_analyser.analyse_code()
                enemy.battle_script_data['ai_data'][index_code] = code_analyser.get_command()
            enemy.write_data_to_file(game_data, copied_files[index_file])



# # Init code
# ```
# stop:
# ```
#
# # Enemy turn
# ```
# stop:
# ```
# # Counter-attack
# ```
# stop:
# ```
# # Death
# ```
# stop:
# ```
# # Before dying or taking a hit
# ```
# stop:
# ```