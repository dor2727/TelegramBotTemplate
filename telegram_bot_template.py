#!/usr/bin/env python3
import logging

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
	_wrappers = [wrapper_log, wrapper_whitelist]

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
			# innermost wrapper is the last in the list
			for w in self._wrappers[::-1]:
				func = w(func)
			return func

		# register commands
		for command_name in self._get_all_command_names():
			self.dp.add_handler(
				CommandHandler(
					strip_command_name(command_name),
					getattr(self, command_name)
				)
			)
		# register menus
		for menu_name in self._get_all_menu_names():
			self.dp.add_handler(
				CallbackQueryHandler(
					getattr(self, menu_name),
					pattern=generate_menu_patter(menu_name),
				)
			)


# Implementing various types of commands in order to show the capabilities of a telegram bot
class TelegramCommandsExamples(TelegramCommands):
	def command_send_text(self, update=None, context=None):
		if context is not None and context.args:
			s = "args = " + str(context.args)
		else:
			s = "text"
		self.send_text(s, update)

	def command_send_image(self, update=None, context=None):
		if context is not None and context.args:
			s = "args = " + str(context.args)
		else:
			s = "text"

		from PIL import Image
		from PIL import ImageDraw

		img = Image.new('RGB', (200, 100))
		d = ImageDraw.Draw(img)
		d.text((20, 20), s, fill=(255, 0, 0))

		img.save("/tmp/a.png")
		self.send_image(
			open("/tmp/a.png", "rb"),
			update
		)

	# this will be called from a user
	def command_menu_example_1(self, update, context):
		from telegram import InlineKeyboardButton, InlineKeyboardMarkup

		def kbd(name):
			return InlineKeyboardButton(name, callback_data=f"menu_example_1 {name.replace(' ', '_')}")

		keyboard = [
			[
				kbd("First button"),
				kbd("Second button"),
				InlineKeyboardButton(text="Open google", url="https://www.google.com")
			],
			[
				kbd("First button in second line"),
			]
		]

		update.message.reply_text(
			"Select button:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)
	def menu_example_1(self, update, context):
		data = update.callback_query.data
		callback_name, subject_name = data.split()
		self.send_text(
			f"Clicked the following button: {subject_name}",
			update
		)

	def command_menu_commands(self, update, context):
		from telegram import KeyboardButton, ReplyKeyboardMarkup

		def kbd(name):
			return KeyboardButton(name)

		keyboard = [
			[
				kbd("/send_text text text"),
				kbd("/send_image image text"),
			],
			[
				kbd("/menu_example_1"),
			]
		]

		self.updater.bot.sendMessage(
			self.chat_id(update),
			text="Choose a function",
			reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
		)

	def command_pdb(self, update=None, context=None):
		import ipdb; ipdb.set_trace()


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


class TelegramAPIExample(TelegramSecureServer, TelegramCommandsExamples):
	def __init__(self):
		# TelegramSecureServer
		super().__init__()
		# TelegramCommandsExamples
		self.add_all_handlers()
		# TelegramScheduledCommands
		self.schedule_commands()
		self.start_scheduler()


def test():
	initialize_logger(debug=False)

	# logging.debug("this is debug")
	# logging.info("this is info")
	# logging.warning("this is a warning")
	# logging.error("this is an error")

	t = TelegramAPIExample()
	t.loop()


if __name__ == '__main__':
	test()
