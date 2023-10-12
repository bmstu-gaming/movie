import json
from pymenu import Menu
from pymenu import select_menu

import movie


empty_menu = Menu('exec menu')
# empty_menu.add_option("Hello", lambda: print(f"Hello"))

def config_verification():
	with open('config.json') as file_config_json:
		data = json.load(file_config_json)
		print(f'{data["FFMPEG"] = }')
		print(f'{data["MOVIES_PATH"] = }')
		print(f'{data["BASE_TEMPLATE"] = }')

menu = Menu('Menu title')
menu.add_option("Config verification", lambda: config_verification())
menu.add_option('Exit', exit)
menu.show()
