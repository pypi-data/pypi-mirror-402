from typing import Callable, Dict, List, Any

from ._exceptions import CommandAlreadyReg, UnknownCommand
from ._fingerprint import Fingerprint
from ._command_meta import CommandMeta
from ._command import Command
from ._formats import BeautifulHelpFormat
from inspect import signature, Parameter
import functools
import abc

class BasicDispatcher(abc.ABC):

	def __init__(self, beautiful_help_format: BeautifulHelpFormat = BeautifulHelpFormat()):
		self.beautiful_help_format = beautiful_help_format

		self.__commands: Dict[str, CommandMeta] = {}

	def _get_fingerprint(self, func: Callable) -> Fingerprint:
		sig = signature(func)
		param_types = {}
		has_varargs = False
		keyword_arg = None

		for param_name, param in sig.parameters.items():
			if param.kind == Parameter.VAR_POSITIONAL:
				has_varargs = True
			if param.kind == Parameter.VAR_KEYWORD:
				keyword_arg = param_name

			param_types[param_name] = param.annotation if param.annotation != param.empty else None

		return Fingerprint(
			signature=sig,
			param_types=param_types,
			has_varargs=has_varargs,
			keyword_arg=keyword_arg
		)

	def _register_command(self, name: str, func: Callable, desc: str):
		if name in self.__commands: raise CommandAlreadyReg(f"Cannot register the same command twice: '{name}'")
		command = CommandMeta(
			name=name,
			func=func,
			fingerprint=self._get_fingerprint(func),
			desc=desc
		)
		self.__commands[name] = command
		return command

	def register(self, name: str, func: Callable, desc: str = ""):
		self._register_command(name=name, func=func, desc=desc)

	# Decorator
	def reg(self, name: str, desc: str = ""):

		def decorator(func: Callable):
			self._register_command(name=name, func=func, desc=desc)
			return func

		return decorator

	@property
	def commands(self) -> List[CommandMeta]: return [cmd for cmd in self.__commands.values()]

	def execute(self, command_str: str) -> Command: pass

	def _convert_arg(self, value: str, param_type: Callable) -> Any: pass

	def _get_command(self, name: str) -> CommandMeta: return self.__commands.get(name)

	@property
	def beautiful_help(self) -> str:
		data = []

		for cmd in self.commands:

			args = []

			for name, param in cmd.fingerprint.signature.parameters.items():

				if param.kind == Parameter.VAR_POSITIONAL:
					args.append(self.beautiful_help_format.positional_arg.format(name=name, type=param.annotation.__name__, default=param.default))
				elif param.kind == Parameter.POSITIONAL_OR_KEYWORD and param.default == Parameter.empty:
					args.append(self.beautiful_help_format.required_arg.format(name=name, type=param.annotation.__name__, default=param.default))
				elif param.kind == Parameter.POSITIONAL_OR_KEYWORD and param.default != Parameter.empty:
					args.append(self.beautiful_help_format.optional_arg.format(name=name, type=param.annotation.__name__, default=param.default))
				elif param.kind == Parameter.VAR_KEYWORD:
					args.append(self.beautiful_help_format.named_arg.format(name=name, type=param.annotation.__name__, default=param.default))

			data.append(self.beautiful_help_format.cmd.format(name=cmd.name, desc=cmd.desc if cmd.desc else self.beautiful_help_format.default_desc, args=self.beautiful_help_format.arg_separator.join(args)))

		return self.beautiful_help_format.cmd_separator.join(data)

	def unregister(self, name: str):
		if name not in self.__commands: raise UnknownCommand(f"Cannot unregister a command '{name}' that does not exist")
		del self.__commands[name]