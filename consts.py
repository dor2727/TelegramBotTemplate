import os

MAIN_FOLDER      = os.path.dirname(__file__)
BOT_DATA_FOLDER  = os.path.join(MAIN_FOLDER, "Data")
KEY_FILEPATH     = os.path.join(BOT_DATA_FOLDER, "key")
# may either have a folder with many different user_ids, or a single file
USER_ID_FILEPATH = USER_ID_FOLDER = os.path.join(BOT_DATA_FOLDER, "user_id")

LOG_FOLDER       = os.path.join(MAIN_FOLDER, "Logs")
LOG_FILE_PATH    = os.path.join(LOG_FOLDER, "main.log")

#
# Scheduler
#
SCHEDULER_SLEEP_AMOUNT_IN_HOURS   = 0.5
SCHEDULER_SLEEP_AMOUNT_IN_SECONDS = 60 * 60 * SCHEDULER_SLEEP_AMOUNT_IN_HOURS
