#
# Callixir is a simple tool for implementing commands.
# Based on the input string, which contains the command name
# and its possible arguments, the corresponding function will be called
#
# Developed VordyV aka Vladislav Netievsky
#
from ._core import BasicDispatcher
from ._exceptions import (
	UnknownCommand,
	ConvertArg,
	CommandAlreadyReg
)
from .dispatchers import (
	SyncDispatcher,
	AsyncDispatcher
)
from .shells import (
	SimpleShell,
	AsyncSimpleShell
)


__version__ = "0.1.0"

__all__ = [
	"BasicDispatcher",
	"UnknownCommand",
	"ConvertArg",
	"CommandAlreadyReg",
	"SyncDispatcher",
	"SimpleShell"
]

'''
Example:

from callixir import SimpleShell

shell = SimpleShell()

@shell.reg("echo")
def cmdEcho(arg: str):
	return f"Echo {arg}"

@shell.reg("sum")
def сmdSum(a: int, b: int):
	return a + b

@shell.reg("log")
def cmdLog(*args: str):
	return ", ".join(args)

result = shell.execute("echo Hello_World!")
print(result.result) # Echo Hello_World!

result = shell.execute("sum 1 2")
print(result.result) # 3

result = shell.execute("log 1 2 Hi 10 J 100 \"many words in one\" 999 71")
print(result.result) # 1, 2, Hi, 10, J, 100, many words in one, 999, 71
'''