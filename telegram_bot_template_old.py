#!/usr/bin/env python3
import os
import pdb
import time
import random
import datetime
import schedule
import threading

from telegram.ext import Updater, InlineQueryHandler, CommandHandler


MAIN_FOLDER = os.path.dirname(__file__)
KEY_FILEPATH = os.path.join(MAIN_FOLDER, "key")
CHAT_ID_FOLDER = MAIN_FOLDER
LOG_FILE = open(os.path.join(MAIN_FOLDER, "log.log"), "a")

# utils
def read_file(filename):
	handle = open(filename)
	data = handle.read().strip()
	handle.close()
	return data

def log(s):
	print(s)
	LOG_FILE.write(s)
	LOG_FILE.write('\n')
	LOG_FILE.flush()

# wrappers
def log_command(func):
	def func_wrapper(*args, **kwargs):
		# each function is named "command_something"
		command_name = func.__name__[8:]

		if "scheduled" in kwargs:
			if kwargs["scheduled"]:
				log(f"    [*] scheduled command - {command_name}\t{time.asctime()}")
			kwargs.pop("scheduled")
		else:
			# args[1] is update
			if len(args) > 1 and args[1]:
				command_text = args[1]['message']['text']
			else:
				command_text = "None"
			log(f"    [*] got command - {command_text}\tcalling {command_name}\t{time.asctime()}")

		return func(*args, **kwargs)

	return func_wrapper

def void(*args, **kwargs):
	return None

"""
requires:
	1) self.user_chat_ids - a list of ints
	2) self.user_names    - a list of strings, in the same length as self.user_chat_ids
"""
def whitelisted_command(func):
	def func_wrapper(*args, **kwargs):
		self = args[0]
		if len(args) > 1 and args[1]:
			update = args[1]
			chat_id = update['message']['chat']['id']
			if chat_id in self.user_chat_ids:
				user_name = self.user_names[self.user_chat_ids.index(chat_id)]
				log(f"[+] whitelist - success - {chat_id} - {user_name}")
			else:
				log(f"[-] whitelist - error - {chat_id}")
				log(str(update))
				log('\n')
				return void
		else:
			# scheduled command
			log(f"[*] whitelist - ignored (scheduled)")

		return func(*args, **kwargs)

	return func_wrapper



class TelegramServer(object):
	def __init__(self):
		# server initialization
		self._key = read_file(KEY_FILEPATH)
		self.updater = Updater(self._key, use_context=True)
		self.dp = self.updater.dispatcher

		self._get_all_users()
		print("Current users:")
		for i in range(len(self.user_chat_ids)):
			print(f"{i}) {self.user_names[i]} - {self.user_chat_ids[i]}")


	def _get_all_users(self):
		files = get_folder_files(CHAT_ID_FOLDER)

		user_files = filter(
			lambda file_name: os.path.basename(file_name).startswith("chat_id_"),
			files
		)

		self.user_names    = []
		self.user_chat_ids = []

		for f in user_files:
			self.user_names.append(os.path.basename(f)[8:])
			self.user_chat_ids.append(int(read_file(f)))

	def chat_id(self, update):
		return update['message']['chat']['id']
	
	def send_text(self, text, chat_id):
		self.updater.bot.sendMessage(
			chat_id,
			text
		)

	def send_image(self, image_file, chat_id, **kwargs):
		self.updater.bot.send_photo(
			chat_id,
			photo=image_file,
			**kwargs
		)

	def loop(self):
		print("[*] entering loop")
		self.updater.start_polling()
		self.updater.idle()

class TelegramCommands(object):
	def __init__(self):
		# self.command_reload()
		self.add_all_handlers()

	def _command_name(self, c):
		return c[8:]

	def add_all_handlers(self):
		commands = filter(
			lambda s: s.startswith("command_"),
			dir(self)
		)

		for command_name in commands:
			self.dp.add_handler(CommandHandler(
				self._command_name(command_name),
				getattr(self, command_name)
			))

	def parse_args(self, context, *expected_types):
		result = []
		if context and context.args:
			try:
				for i in range(len(context.args)):
					result.append(expected_types[i](context.args[i]))
			except Exception as e:
				self.send_text(f"command_month error: {e} ; args = {context.args}", self.chat_id())

		# fill default values, if needed
		for i in range(len(result), len(expected_types)):
			result.append(expected_types[i]())

		return result


	# debug
	@whitelisted_command
	@log_command
	def command_pdb(self, update=None, context=None):
		pdb.set_trace()

	@whitelisted_command
	@log_command
	def command_start(self, update, context):
		chat_id = self.chat_id(update)
		log("chat_id = %s" % chat_id)

	@whitelisted_command
	@log_command
	def command_list_commands(self, update=None, context=None):
		commands = filter(
			lambda s: s.startswith("command_"),
			dir(self)
		)

		self.send_text(
			'\n'.join(
				f"{self._command_name(c)} - {self._command_name(c)}"
				for c in commands
			),
			update
		)


class TelegramScheduledCommands(object):
	def __init__(self):
		self.schedule_commands()

	def schedule_commands(self):
		# schedule.every().day.at("05:00").do(
		# 	self.command_reload,
		# 	scheduled=True
		# )


		def run_scheduler():
			while True:
				schedule.run_pending()
				time.sleep(60*60*0.5)

		threading.Thread(target=run_scheduler).start()

class TelegramAPI(TelegramServer, TelegramCommands, TelegramScheduledCommands):
	def __init__(self):
		TelegramServer.__init__(self)
		TelegramCommands.__init__(self)
		TelegramScheduledCommands.__init__(self)


def main():
	log(f"----------------")
	now = datetime.datetime.now().strftime("%Y/%m/%d_%H:%M")
	log(f"[*] Starting: {now}")

	t = TelegramAPI()
	t.loop()
	LOG_FILE.close()

if __name__ == '__main__':
	main()
