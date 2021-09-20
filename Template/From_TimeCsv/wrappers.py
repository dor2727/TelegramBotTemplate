import time
from TimeCsv.time_utils import log


"""
A function to return from a wrapper in case the call to the function was forbidden
"""
def void(*args, **kwargs):
	return None

"""
A small util, getting the 'message' object from telegram's 'update' object
"""
def get_message(update):
	if update["message"] is not None:
		return update['message']
	else:
		return update['callback_query']['message']


"""
verifies the user calling the function
- there may be no user, if the call was scheduled
- if it was called from telegram, then there has to be a user
	this user must be the same as the only user allowed (this bot is only used by me)
"""
def whitelisted_command(func):
	"""
	requires:
		self._chat_id - int - my user id
	"""
	def func_wrapper(*args, **kwargs):
		self = args[0]
		if len(args) > 1 and args[1]:
			update = args[1]

			chat_id = get_message(update)['chat']['id']

			if chat_id == self._chat_id:
				log(f"[+] whitelist - success - {chat_id}")
			else:
				log(f"[-] whitelist - error - {chat_id}")
				log(str(update))
				log(str(args))
				log(str(kwargs))
				log('\n')
				return void

		# scheduled command
		elif "scheduled" in kwargs and kwargs["scheduled"]:
			log(f"[*] whitelist - ignored (scheduled)")
			return func(*args, **kwargs)

		else:
			# unknown. This should not happen
			log(f"[!] whitelist - got to the forbidden else")
			log(str(args))
			log(str(kwargs))
			return void

	return func_wrapper


"""
logging the call to the function
"""
def log_command(func):
	def func_wrapper(*args, **kwargs):
		# each function is named "command_something"
		if func.__name__.startswith("command_"):
			command_name = func.__name__[8:]
		else:
			command_name = func.__name__

		if "scheduled" in kwargs:
			if kwargs["scheduled"]:
				log(f"    [*] scheduled command - {command_name}\t{time.asctime()}")
			kwargs.pop("scheduled")

		else:
			# args[1] is update
			if len(args) > 1 and args[1]:
				update = args[1]

				if update["message"] is not None:
					command_text = update['message']['text']
				else:
					command_text = update['callback_query']['data']
			else:
				command_text = "None"
			log(f"    [*] got command - {command_text}\tcalling {command_name}\t{time.asctime()}")

		return func(*args, **kwargs)

	return func_wrapper

