from typing import Callable, Any
from callixir import SyncDispatcher
from callixir._command import Command
import traceback

class SimpleShell(SyncDispatcher):

	def __init__(self, arg_overflow: bool = True, on_execute: Callable | None = None, on_error: Callable | None = None):
		self.__on_execute = on_execute
		self.__on_error = on_error
		super().__init__(arg_overflow=arg_overflow)

	def __call_event(self, func: Callable, arg: Any) -> None:
		if callable(func): func(arg)

	def execute(self, command_str: str) -> Command | None:
		try:
			result = super().execute(command_str)
			self.__call_event(self.__on_execute, result)
			return result
		except Exception as e:
			err_traceback = traceback.format_exc()
			result = Command(
				command_str=command_str,
				error=e,
				err_traceback=err_traceback
			)
			self.__call_event(self.__on_error, result)
			return result