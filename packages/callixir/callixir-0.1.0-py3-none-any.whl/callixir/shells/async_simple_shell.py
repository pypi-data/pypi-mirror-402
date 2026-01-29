from typing import Callable, Any
from callixir import AsyncDispatcher
from callixir._command import Command
import traceback
import asyncio

class AsyncSimpleShell(AsyncDispatcher):

	def __init__(self, arg_overflow: bool = True, on_execute: Callable | None = None, on_error: Callable | None = None):
		self.__on_execute = on_execute
		self.__on_error = on_error
		super().__init__(arg_overflow=arg_overflow)

	def __call_event(self, func: Callable, arg: Any, loop) -> None:
		if callable(func):
			task = loop.create_task(func(arg))

	async def execute(self, command_str: str) -> Command | None:
		loop = asyncio.get_running_loop()
		try:
			main_task = loop.create_task(super().execute(command_str, loop))
			result = await main_task
			self.__call_event(self.__on_execute, result, loop)
			return result
		except Exception as e:
			err_traceback = traceback.format_exc()
			result = Command(
				command_str=command_str,
				error=e,
				err_traceback=err_traceback
			)
			self.__call_event(self.__on_error, result, loop)
			return result