import sys
import logging

from .consts import *


#
# getting the key
#
def read_file(filename):
	handle = open(filename)
	data = handle.read().strip()
	handle.close()
	return data


def get_folder_files(folder, recursive=False):
	w = os.walk(folder)

	if recursive:
		all_files = []
		for folder_name, folders, files in w:
			all_files += list(map(
				lambda file_name: os.path.join(folder_name, file_name),
				files
			))
		return all_files

	else:
		folder_name, folders, files = next(w)
		return list(map(
			lambda file_name: os.path.join(folder_name, file_name),
			files
		))


#
# Logging
#
def initialize_logger(debug=False):
	logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

	rootLogger = logging.getLogger()
	if debug:
		rootLogger.setLevel(logging.DEBUG)
	else:
		rootLogger.setLevel(logging.INFO)

	fileHandler = logging.FileHandler(LOG_FILE_PATH)
	fileHandler.setFormatter(logFormatter)
	rootLogger.addHandler(fileHandler)

	consoleHandler = logging.StreamHandler(sys.stdout)
	consoleHandler.setFormatter(logFormatter)
	rootLogger.addHandler(consoleHandler)

	rootLogger.info("---------------------------------------")



"""
A small util, getting the 'message' object from telegram's 'update' object
"""
def get_message(update):
	if update["message"] is not None:
		return update['message']
	else:
		return update['callback_query']['message']
"""
"""
def get_chat_id(update):
	return get_message(update)['chat']['id']

	# another way
	# return context._chat_id_and_data[0]
	# return context._user_id_and_data[0]


#
# Handling functions' names
#
def strip_command_name(command_name):
	return command_name[8:]
def is_command_name(command_name):
	return command_name.startswith("command_")

def generate_menu_patter(menu_name):
	return f"^{menu_name}\\b"
def is_menu_name(menu_name):
	return menu_name.startswith("menu_")

