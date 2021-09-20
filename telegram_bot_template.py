import time
import socket
import logging
import schedule
import threading

from TelegramBots.consts import *
from TelegramBots.utils import *
from TelegramBots.wrappers import *

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler


class TelegramServer(object):
	_wrappers = [wrapper_log]
	def __init__(self):
		self.updater = Updater(
			read_file(KEY_FILEPATH),
			use_context=True
		)

	@property
	def dp(self):
		return self.updater.dispatcher

	def chat_id(self, update):
		return get_chat_id(update)

	def send_text(self, text, update, **kwargs):
		self.updater.bot.sendMessage(
			self.chat_id(update),
			text,
			**kwargs
		)

	def send_image(self, image_file, update, **kwargs):
		self.updater.bot.send_photo(
			self.chat_id(update),
			photo=image_file,
			**kwargs
		)

	def loop(self):
		logging.info("Entering loop")
		self.updater.start_polling(timeout=123)
		self.updater.idle()

	def loop_no_error(self):
		while True:
			try:
				self.loop()

			# socket.gaierror: [Errno -3] Temporary failure in name resolution
			except socket.gaierror as exc:
				if exc.errno == -3:
					logging.warning(f"[*] Caught socket.gaierror (-3) in main (loop) - continue")
				else:
					logging.warning(f"[*] Caught socket.gaierror ({exc.errno}) in main (loop) - continue")
					logging.warning(str(exc))

				continue

			except Exception as exc:
				logging.warning(f"[!] Caught general error in main (loop) - quitting")
				logging.warning(exception_message())
				raise exc


class TelegramSecureServer(TelegramServer):
	# log first, then check the whitelist (so that 'bad' calls are logged)
	_wrappers = [wrapper_log_secure, wrapper_whitelist]

	# may have one of the following values:
	# 1) None - no main user
	# 2) a string - the name of the main user
	# 3) a number - the chat_id of the main user
	MAIN_USER = None

	def __init__(self):
		super().__init__()

		self._get_all_users()
		self._print_all_users()

	def _get_all_users(self):
		files = get_folder_files(CHAT_ID_FILEPATH)

		user_files = filter(
			is_chat_id,
			files
		)

		self.user_names    = []
		self.user_chat_ids = []

		for f in user_files:
			self.user_names.append(os.path.basename(f)[8:])
			self.user_chat_ids.append(int(read_file(f)))

		self.users = dict(zip(self.user_names, self.user_chat_ids))

	def _print_all_users(self):
		logging.info("Current users:")
		for i in range(len(self.user_chat_ids)):
			logging.info(f"    {i}) {self.user_names[i]} - {self.user_chat_ids[i]}")

	# changing function declaration - allowing `update` to be None - meaning the MAIN_USER
	def chat_id(self, update=None):
		if update:
			return super().chat_id(update)
		else:
			if type(self.MAIN_USER) is int:
				if self.MAIN_USER in self.user_chat_ids:
					return self.MAIN_USER
				else:
					logging.error(f"MAIN_USER ({self.MAIN_USER}) not in user_chat_ids ({str(self.user_chat_ids)})")
					raise ValueError("MAIN_USER is not a registered user")
			elif type(self.MAIN_USER) is str:
				if self.MAIN_USER in self.user_names:
					return self.users[self.MAIN_USER]
				else:
					logging.error(f"MAIN_USER ({self.MAIN_USER}) not in user_names ({str(self.user_names)})")
					raise ValueError("MAIN_USER is not a registered user")
			elif self.MAIN_USER is None:
				raise ValueError("No update was given with no MAIN_USER defined")
			else:
				logging.error(f"MAIN_USER = {type(self.MAIN_USER)} : {str(self.MAIN_USER)}")
				raise NotImplemented("An invalid value for self.MAIN_USER was given")

	def send_text(self, text, update=None, **kwargs):
		super().send_text(text, update, **kwargs)

	def send_image(self, image_file, update=None, **kwargs):
		super().send_image(image_file, update, **kwargs)



class TelegramCommands(object):
	def _get_all_command_names(self):
		return filter(
			is_command_name,
			dir(self)
		)
	def _get_all_menu_names(self):
		return filter(
			is_menu_name,
			dir(self)
		)

	def add_all_handlers(self):
		def wrap(func):
			func_name = func.__name__
			# innermost wrapper is the last in the list
			for w in self._wrappers[::-1]:
				func = w(func, self=self, func_name=func_name)
			return func

		# register commands
		for command_name in self._get_all_command_names():
			self.dp.add_handler(
				CommandHandler(
					strip_command_name(command_name),
					wrap( getattr(self, command_name) )
				)
			)
		# register menus
		for menu_name in self._get_all_menu_names():
			self.dp.add_handler(
				CallbackQueryHandler(
					wrap( getattr(self, menu_name) ),
					pattern=generate_menu_patter(menu_name),
				)
			)



class TelegramScheduledCommands(object):
	def schedule_commands(self):
		self.schedule_hourly()
		self.schedule_daily()
		self.schedule_weekly()

	def schedule_hourly(self):
		pass

	def schedule_daily(self):
		pass

	def schedule_weekly(self):
		pass

	def start_scheduler(self):
		def run_scheduler():
			while True:
				try:
					schedule.run_pending()
					time.sleep(SCHEDULER_SLEEP_AMOUNT_IN_SECONDS)

				# socket.gaierror: [Errno -3] Temporary failure in name resolution
				except socket.gaierror as exc:
					if exc.errno == -3:
						logging.warning(f"[*] Caught socket.gaierror (-3) in main (loop) - continue")
					else:
						logging.warning(f"[*] Caught socket.gaierror ({exc.errno}) in main (loop) - continue")
						logging.warning(str(exc))

					continue

				except Exception as exc:
					log(f"[!] Caught general error in run_scheduler - quitting")
					log(exception_message())
					raise exc

		threading.Thread(target=run_scheduler).start()

