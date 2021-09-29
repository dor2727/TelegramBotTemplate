"""
There are 3 wrappers defined here:
- wrapper_log
	logs the command, as well as its arguments.
	This wrapper is used when no security measures (whilelisting users) is used.
- wrapper_log_secure
	logs the command, its arguments, and which user called the command
	This wrapper is used when security measures are used.
- wrapper_whitelist
	Verifies user identity before calling the function being wrapped.
"""
import logging
import telegram

from TelegramBots.utils import *


"""
verifies the user calling the function
- there may be no user, if the call was scheduled
- if it was called from telegram, then there has to be a user
"""
def wrapper_whitelist(func, **wrapper_kwargs):
	def func_wrapper(*args, **kwargs):
		# scheduled command
		if "scheduled" in kwargs and kwargs["scheduled"]:
			log(f"[*] whitelist - ignored (scheduled)")
			kwargs.pop("scheduled")

		elif len(args) >= 1 and type(args[0]) is telegram.update.Update:
			update = args[0]
			chat_id = get_chat_id(update)
			# [!] expecting 'self' to be sent in **wrapper_kwargs
			self = wrapper_kwargs["self"]

			if chat_id in self.user_chat_ids:
				user_name = self.user_names[self.user_chat_ids.index(chat_id)]
				logging.info(f"  [+] Whitelist - success - {chat_id} - {user_name}")
			else:
				logging.warning(f"  [-] Whitelist - failed - {chat_id}")
				logging.warning(f"  [-] Whitelist - failed - update: {str(update)}")
				logging.warning(f"  [-] Whitelist - failed - args: {str(args)}")
				logging.warning(f"  [-] Whitelist - failed - kwargs: {str(kwargs)}")
				return None

		else:
			logging.error(f"  [-] Whitelist - got to the forbidden else")
			logging.warning(f"  [-] Whitelist - failed - args: {str(args)}")
			logging.warning(f"  [-] Whitelist - failed - kwargs: {str(kwargs)}")
			return None

		return func(*args, **kwargs)

	return func_wrapper


"""
logging the call to the function
"""
def _get_command_text(update):
	if update["message"] is not None:
		command_text = update['message']['text']
	else:
		command_text = update['callback_query']['data']

def wrapper_log(func, **wrapper_kwargs):
	def func_wrapper(*args, **kwargs):
		if "func_name" in wrapper_kwargs:
			command_name = wrapper_kwargs["func_name"]
		else:
			command_name = func.__name__


		if "scheduled" in kwargs and kwargs["scheduled"]:
			logging.info(f"[*] Command - scheduled - {command_name}")

		else:
			# args[1] is update
			if len(args) >= 1 and type(args[0]) is telegram.update.Update:
				command_text = _get_command_text(args[0])
			else:
				command_text = "None"

			logging.info(f"[*] Command ({command_name}) - text: {command_text}")

		return func(*args, **kwargs)

	return func_wrapper


def _get_user_name_from_update(update=None, **kwargs):
	if type(update) is not telegram.update.Update:
		return "None"

	if "self" not in kwargs:
		return "None"

	self = kwargs["self"]

	chat_id = get_chat_id(update)

	if chat_id in self.user_chat_ids:
		return self.user_names[
			self.user_chat_ids.index(
				chat_id
			)
		]
	else:
		try:
			nickname = update["message"]["chat"]["username"]
		except:
			nickname = "<No username found>"

		return f"Unknown user ({chat_id} : {nickname})"

def wrapper_log_secure(func, **wrapper_kwargs):
	def func_wrapper(*args, **kwargs):
		if "func_name" in wrapper_kwargs:
			command_name = wrapper_kwargs["func_name"]
		else:
			command_name = func.__name__


		if "scheduled" in kwargs and kwargs["scheduled"]:
			logging.info(f"[*] Command - scheduled - {command_name}")

		else:
			if len(args) >= 1 and type(args[0]) is telegram.update.Update:
				command_text = _get_command_text(args[0])
				user_name = _get_user_name_from_update(args[0], **wrapper_kwargs)
			else:
				command_text = "None"
				user_name = "None"

			logging.info(f"[*] Command ({command_name}) - from user ({user_name}) - text: {command_text}")

		return func(*args, **kwargs)

	return func_wrapper

"""
When the wrapper is defined as such:
class SomeClass:
	@first_wrapper
	@second_wrapper
	def function(self, *args, **kwargs):
		pass

Then 'func_wrapper' gets:
	args = [self, update]
	# probably there's also context, but I've never used it in a wrapper, so I'm not sure

However, when the wrappers are defined as:
for w in self._wrappers[::-1]:
	func = w(func)

Then 'func_wrapper' gets:
	args = [update, context]
"""
