#!/usr/bin/env python3
import os
import pdb
import time
import shlex
import schedule
import threading

import TimeCsv.cli
from TimeCsv.parsing import DataFolder, ParseError

from TimeCsv.consts import *
from TimeCsv.filters import *
from TimeCsv.statistics import *
from TimeCsv.time_utils             import read_telegram_file, log
from TimeCsv.functions.productivity import get_productivity_pie
from TimeCsv.Telegram_Bot.wrappers  import get_message, whitelisted_command, log_command

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class TelegramServer(object):
	def __init__(self):
		# server initialization
		self._key = read_telegram_file("key")
		self._chat_id = int(read_telegram_file("chat_id"))

		self.updater = Updater(self._key, use_context=True)
		self.dp = self.updater.dispatcher

		# get a handle to DataFolder
		self.datafolder = DataFolder()

	def chat_id(self, update=None):
		if update:
			return get_message(update)['chat']['id']
		else:
			# todo: if there are multiple _chat_id -> create a file chat_id__main which is a symlink to some chat_id, and make it the default
			return self._chat_id

	def send_text(self, text, update=None):
		self.updater.bot.sendMessage(
			self.chat_id(update),
			text
		)

	def send_image(self, image_file, update=None):
		self.updater.bot.send_photo(
			self.chat_id(update),
			photo=image_file
		)

	def loop(self):
		log("[*] entering loop")
		self.updater.start_polling(timeout=123)
		self.updater.idle()

class TelegramCommands(object):
	def _command_name(self, c):
		return c[8:]

	def add_all_handlers(self):
		# register commands
		commands = filter(
			lambda s: s.startswith("command_"),
			dir(self)
		)

		for command_name in commands:
			self.dp.add_handler(CommandHandler(
				self._command_name(command_name),
				getattr(self, command_name)
			))

		# register menus
		menus = filter(
			lambda s: s.startswith("menu_"),
			dir(self)
		)

		for menu_name in menus:
			self.dp.add_handler(CallbackQueryHandler(
				getattr(self, menu_name),
				pattern=f"^{menu_name}\\b",
			))

	def parse_args(self, context, *expected_types):
		result = []
		if context and context.args:
			try:
				for i in range(len(context.args)):
					result.append(expected_types[i](context.args[i]))
			except Exception as e:
				self.send_text(
					f"command_month error: {e} ; args = {context.args}",
					# send it to me, not to the user (avoiding information disclosure)
					self.chat_id()
				)

		# fill default values, if needed
		for i in range(len(result), len(expected_types)):
			result.append(expected_types[i]())

		return result


	@whitelisted_command
	@log_command
	def command_cli(self, update, context):
		args_list = ["--telegram"] + shlex.split(' '.join(context.args))

		result = TimeCsv.cli.main(self.datafolder, args_list)

		if type(result) is str:
			self.send_text( result, update)
		elif isinstance(result, io.TextIOBase): # is it a file
			self.send_image(result, update)
		else:
			raise ValueError(f"invalid result from command_cli {type(result)}")

	#
	# text report
	#
	def filtered_time_command(self, f, update=None):
		g = GroupedStats_Group(
			f % self.datafolder.data,
			selected_time=f.get_selected_time(),
			group_value="time"
		)

		self.send_text(
			g.to_telegram(),
			update
		)

	@whitelisted_command
	@log_command
	def command_text_report(self, update, context):
		def kbd(name):
			return InlineKeyboardButton(name, callback_data=f"menu_text_report {name}")

		keyboard = [
			[kbd("today"), kbd("yesterday"), kbd("week"), kbd("last_week")],
			[kbd("month"), kbd("year"), kbd("all")],
		]
		update.message.reply_text(
			"Select date:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)

	@whitelisted_command
	@log_command
	def menu_text_report(self, update, context):
		data = update.callback_query.data
		callback_name, filter_name = data.split()

		self.filtered_time_command(
			get_named_filter(filter_name),
			update
		)


	@whitelisted_command
	@log_command
	def command_text_report_month(self, update=None, context=None):
		month, year = self.parse_args(context, int, int)
		self.filtered_time_command(TimeFilter_Month(month, year), update)

	@whitelisted_command
	@log_command
	def command_text_report_year(self, update=None, context=None):
		year, = self.parse_args(context, int)
		self.filtered_time_command(TimeFilter_Year(year), update)

	#
	# pie reports
	#
	def pie_command(self, g_cls, f, update=None):
		g = g_cls(
			f % self.datafolder.data,
			selected_time=f.get_selected_time(),
			group_value="time"
		)

		# TODO:
		# this initializes self.headers_sorted, self.values_sorted
		# there should be a better (and automated) way to initialize them
		g.group()

		pie_file = g.to_pie()

		self.send_image(pie_file, update)

	MENU_PIE_SUBJECTS = {
		"homework" : GroupedStats_Homework,
		"lecture"  : GroupedStats_Lecture,
		"gaming"   : GroupedStats_Games,
		"youtube"  : GroupedStats_Youtube,
	}

	@whitelisted_command
	@log_command
	def command_pie(self, update, context):
		def kbd(name):
			return InlineKeyboardButton(name, callback_data=f"menu_pie {name}")

		keyboard = [
			[kbd(i) for i in self.MENU_PIE_SUBJECTS.keys()],
		]
		update.message.reply_text(
			"Select subject:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)

	@whitelisted_command
	@log_command
	def menu_pie(self, update, context):
		data = update.callback_query.data
		callback_name, subject_name = data.split()

		self.pie_command(
			self.MENU_PIE_SUBJECTS[subject_name],
			TimeFilter_Days(7),
			update
		)

	#
	# productive pie
	#
	def send_productive_pie(self, f, update=None, **kwargs):
		pie_file = get_productivity_pie(
			data=f % self.datafolder.data,
			save=True,
			**kwargs
		)

		self.send_image(pie_file, update)

	@whitelisted_command
	@log_command
	def command_productive_pie(self, update, context):
		focused, = self.parse_args(context, int) # taking a boolean value as int. Expecting only 0 or 1.

		def kbd(name):
			return InlineKeyboardButton(name, callback_data=f"menu_productive_pie {name} {focused}")

		keyboard = [
			[kbd("today"), kbd("yesterday"), kbd("week"), kbd("last_week")],
			[kbd("month"), kbd("year"), kbd("all")],
		]
		update.message.reply_text(
			"Select date:",
			reply_markup=InlineKeyboardMarkup(keyboard)
		)

	@whitelisted_command
	@log_command
	def menu_productive_pie(self, update, context):
		data = update.callback_query.data
		callback_name, filter_name, focused = data.split()

		self.send_productive_pie(
			get_named_filter(filter_name),
			focused=bool(int(focused)),
			selected_time=filter_name,
			update=update,
		)

	@whitelisted_command
	@log_command
	def command_productive_pie_month(self, update=None, context=None):
		month, year, focused = self.parse_args(context, int, int, int)
		f = TimeFilter_Month(month, year)

		self.send_productive_pie(
			f,
			focused=bool(focused),
			selected_time=f._selected_time,
			update=update,
		)

	@whitelisted_command
	@log_command
	def command_productive_pie_year(self, update=None, context=None):
		year, focused = self.parse_args(context, int, int)
		f = TimeFilter_Year(year)

		self.send_productive_pie(
			f,
			focused=bool(focused),
			selected_time=f._selected_time,
			update=update,
		)

	#
	# others
	#
	@whitelisted_command
	@log_command
	def command_test(self, update=None, context=None):
		s = "test"
		if context is not None and context.args:
			s += ": " + str(context.args)
		self.send_text(s, update)

	@whitelisted_command
	@log_command
	def command_pdb(self, update=None, context=None):
		pdb.set_trace()

	@whitelisted_command
	@log_command
	def command_reload(self, update=None, context=None):
		self.datafolder.reload()
		log(f"    [r] reloaded : {time.asctime()}")

		# if update is None - we are called from the scheduler
		# only answer the user if the user asks the reload
		if update is not None:
			self.send_text("reload - done", update)

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
	def schedule_commands(self):
		self.schedule_daily()
		self.schedule_weekly()

		# reload
		schedule.every().hour.at(":57").do(
			self.command_reload,
			scheduled=True
		)

		self.scheduler_start()


	def schedule_daily(self):
		#
		# daily log
		#
		log("Daily filter - yesterday - " + str(get_named_filter("yesterday")))
		# yesterday text report
		schedule.every().day.at("08:00").do(
			self.filtered_time_command,
			get_named_filter("yesterday"),
		)
		# yesterday productive pie
		schedule.every().day.at("08:00").do(
			self.send_image,
			get_productivity_pie(
				data=get_named_filter("yesterday") % self.datafolder.data,
				selected_time="yesterday",
				save=True,
				focused=False
			)
		)

	def schedule_weekly(self):
		#
		# weekly log
		#
		# last week text report
		schedule.every().sunday.at("08:00").do(
			self.filtered_time_command,
			get_named_filter("last_week"),
		)
		# weekly productive pie
		schedule.every().sunday.at("08:00").do(
			self.send_image,
			get_productivity_pie(
				data=get_named_filter("last_week") % self.datafolder.data,
				selected_time="last_week",
				save=True,
				focused=False
			)
		)
		# homework pie
		schedule.every().sunday.at("08:00").do(
			self.pie_command,
			GroupedStats_Homework,
			TimeFilter_Days(7),
		)
		# gaming pie
		schedule.every().sunday.at("08:00").do(
			self.pie_command,
			GroupedStats_Games,
			TimeFilter_Days(7),
		)

	def scheduler_start(self):
		def run_scheduler():
			while True:
				try:
					schedule.run_pending()
					time.sleep(60*60*0.5)

				except ParseError as pe:
					# log error to screen + log file
					log(f"[*] Caught ParseError in run_scheduler. retrying in {RETRY_SLEEP_AMOUNT_IN_HOURS} hours")
					log(f"Caught ParseError:\n{str(pe)}")

					# send error to the main user
					self.send_text(f"Caught ParseError:\n{str(pe)}")

					# re-sync with dropbox
					log(f"    [*] starting sleep")
					time.sleep(RETRY_SLEEP_AMOUNT_IN_SECONDS)

					log(f"    [*] sleep ended")

				except Exception as exc:
					log(f"[!] Caught general error in run_scheduler - quitting")
					log(exception_message())
					raise exc

		threading.Thread(target=run_scheduler).start()



class TelegramAPI(TelegramServer, TelegramCommands, TelegramScheduledCommands):
	def __init__(self):
		super().__init__()
		self.add_all_handlers()
		self.schedule_commands()

def main():
	log(f"----------------")
	now = datetime.datetime.now().strftime("%Y/%m/%d_%H:%M")
	log(f"[*] Starting: {now}")

	while True:
		# an exception can either happen in __init__, when self.datafolder is created
		# or in loop, where the `reload` method is called

		try:
			t = TelegramAPI()

		except ParseError as pe:
			log(f"[*] Caught ParseError in main (__init__). retrying in {RETRY_SLEEP_AMOUNT_IN_HOURS} hours")
			log(f"Caught ParseError:\n{str(pe)}")
			time.sleep(RETRY_SLEEP_AMOUNT_IN_SECONDSE)
			os.system(DAILY_WGET_PATH)

		except Exception as exc:
			log(f"[!] Caught general error in main (__init__) - quitting")
			log(exception_message())
			raise exc


		try:
			t.loop()

		except ParseError as pe:
			log(f"[*] Caught ParseError in main (loop). retrying in {RETRY_SLEEP_AMOUNT_IN_HOURS} hours")
			log(f"Caught ParseError:\n{str(pe)}")
			time.sleep(RETRY_SLEEP_AMOUNT_IN_SECONDSE)
			os.system(DAILY_WGET_PATH)

		# socket.gaierror: [Errno -3] Temporary failure in name resolution
		except socket.gaierror as exc:
			if exc.errno == -3:
				log(f"[*] Caught socket.gaierror (-3) in run_scheduler. continue.")
				continue
			else:
				log(f"[*] Caught socket.gaierror ({exc.errno}) in run_scheduler. continue.")
				log(str(exc))
				continue

		except Exception as exc:
			log(f"[!] Caught general error in main (loop) - quitting")
			log(exception_message())
			raise exc

	LOG_FILE.close()

if __name__ == '__main__':
	main()