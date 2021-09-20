import logging

from TelegramBots.utils import *


"""
verifies the user calling the function
- there may be no user, if the call was scheduled
- if it was called from telegram, then there has to be a user
"""
def wrapper_whitelist(func):
	"""
	requires:
		self._chat_id - int - my user id
	"""
	def func_wrapper(*args, **kwargs):
		# scheduled command
		if "scheduled" in kwargs and kwargs["scheduled"]:
			log(f"[*] whitelist - ignored (scheduled)")
			kwargs.pop("scheduled")

		elif len(args) > 1 and args[1]:
			self = args[0]
			update = args[1]
			chat_id = get_chat_id(update)

			if chat_id in self.user_chat_ids:
				user_name = self.user_names[self.user_chat_ids.index(chat_id)]
				logging.info(f"    Whitelist - success - {chat_id} - {user_name}")
			else:
				logging.warning(f"    Whitelist - failed - {chat_id}")
				logging.warning(f"    Whitelist - failed - update: {str(update)}")
				logging.warning(f"    Whitelist - failed - args: {str(args)}")
				logging.warning(f"    Whitelist - failed - kwargs: {str(kwargs)}")
				return None

		else:
			logging.error(f"    Whitelist - got to the forbidden else")
			logging.warning(f"    Whitelist - failed - args: {str(args)}")
			logging.warning(f"    Whitelist - failed - kwargs: {str(kwargs)}")
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

def wrapper_log(func):
	def func_wrapper(*args, **kwargs):
		command_name = func.__name__
		
		if "scheduled" in kwargs and kwargs["scheduled"]:
			logging.info(f"    Command - scheduled - {command_name}")
			# kwargs.pop("scheduled")

		else:
			# args[1] is update
			if len(args) > 1 and args[1]:
				command_text = _get_command_text(args[1])
			else:
				command_text = "None"

			logging.info(f"    Command - from user - {command_name} - text: {command_text}")

		return func(*args, **kwargs)

	return func_wrapper

