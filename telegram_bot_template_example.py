#!/usr/bin/env python3
import schedule

from TelegramBots.consts import *
from TelegramBots.utils import *
from TelegramBots.wrappers import *
from TelegramBots.telegram_bot_template import *


# Implementing various types of commands in order to show the capabilities of a telegram bot
class TelegramCommands_Examples(TelegramCommands):
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


class TelegramScheduledCommands_Examples(TelegramScheduledCommands):
	def schedule_hourly(self):
		schedule.every().hour.at(":30").do(
			self.send_text,
			"text",
			scheduled=True
		)

class TelegramAPIExample(
		TelegramSecureServer,
		TelegramCommands_Examples,
		TelegramScheduledCommands_Examples
	):
	def __init__(self):
		# TelegramSecureServer
		super().__init__()
		# TelegramCommandsExamples
		self.add_all_handlers()
		# TelegramScheduledCommands
		self.schedule_commands()
		self.start_scheduler()

		# alternatively, one can call:
		# 	TelegramSecureServer.__init__(self)
		# 	TelegramCommandsExamples.__init__(self)
		# 	TelegramScheduledCommands.__init__(self)


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
