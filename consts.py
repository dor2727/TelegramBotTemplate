"""
The expected file structure is as follows:
ROOT_DIRECTORY/
	Data/
		key
		chat_id/
			chat_id_first_user_name
			chat_id_second_user_name
			chat_id_third_user_name
		# chat_id may be a file, instead of a folder, in case where only one user is used.
	Logs/
		main.log

	consts.py
	telegram_bot_template.py
	utils.py
	wrappers.py
"""
import os

MAIN_FOLDER      = os.path.dirname(__file__)
BOT_DATA_FOLDER  = os.path.join(MAIN_FOLDER, "Data")
KEY_FILEPATH     = os.path.join(BOT_DATA_FOLDER, "key")
# may either have a folder with many different user_ids, or a single file
CHAT_ID_FILEPATH = CHAT_ID_FOLDER = os.path.join(BOT_DATA_FOLDER, "chat_id")

LOG_FOLDER       = os.path.join(MAIN_FOLDER, "Logs")
LOG_FILE_PATH    = os.path.join(LOG_FOLDER, "main.log")

#
# Scheduler
#
SCHEDULER_SLEEP_AMOUNT_IN_HOURS   = 0.5
SCHEDULER_SLEEP_AMOUNT_IN_SECONDS = 60 * 60 * SCHEDULER_SLEEP_AMOUNT_IN_HOURS
