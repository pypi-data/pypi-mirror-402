# Callixir

A small and convenient tool for implementing command execution in any application. Suitable for a console application or a social media bot.

Its principle of operation is simple: the user sends a string containing the command name and its arguments, if required. The next step is to execute the corresponding method based on this string.

Developed and tested on Python version **3.12**. Support for other, later versions has not been addressed yet.
___

## Example

```py
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
```

---

## Installing

Install Callixir via pip:

```
pip install callixir
```

## Features

- Convenient handling of arguments, they correspond to the signature of the arguments in the method;
- Support for asynchronous commands;
- Support for named arguments.

## Async example

```py
from callixir import AsyncSimpleShell
import asyncio

shell = AsyncSimpleShell()

@shell.reg("echo")
async def cmdEcho(arg: str):
	return f"Echo {arg}"

@shell.reg("sum")
async def сmdSum(a: int, b: int):
	return a + b

@shell.reg("log")
async def cmdLog(*args: str):
	return ", ".join(args)

async def main():
	result = await shell.execute("echo Hello_World!")
	print(result.result) # Echo Hello_World!

	result = await shell.execute("sum 1 4")
	print(result.result) # 5

	result = await shell.execute("log nova prospekt \"Async cmd\"")
	print(result.result) # nova, prospekt, Async cmd

asyncio.run(main())
```

## Named arguments

The handler can work with function's named arguments (**kwargs). Furthermore, the same arguments undergo data type conversion for example, if the annotation is int, then all kwargs arguments will be converted to int.

A named argument can be specified in the string in two ways: `--argument_name=value`, `--argument_name value`. Values can also be enclosed in double quotes: `--argument_name "multiple values"`.

### Example
```py
from callixir import SimpleShell

shell = SimpleShell()

@shell.reg("info")
def cmdInfo(**kwargs: str):
	data = []

	for key, value in kwargs.items():
		data.append(f"key = {key}\tvalue = {value}")

	return "\n".join(data)

@shell.reg("calc")
def cmdCalc(a: float, b: float, **kwargs: str):
	action = kwargs.get("action", "+")

	if action == "+": return a+b
	elif action == "-": return a-b
	elif action == "*": return a * b
	elif action == "/": return a / b
	else: return "Incorrect type of action"

def main():
	result = shell.execute("info --arg1=value1 --arg2 value2 --apple red --datetime=\"03.11.2025 15:31\"")
	print(result.result)
	'''
	key = arg1	value = value1
	key = arg2	value = value2
	key = apple	value = red
	key = datetime	value = 03.11.2025 15:31
	'''

	result = shell.execute("calc 1 2")
	print(result.result) # 3.0

	result = shell.execute("calc 1 2 --action +")
	print(result.result) # 3.0

	result = shell.execute("calc 1 2 --action *")
	print(result.result) # 2.0

	result = shell.execute("calc 1 2 --action pow")
	print(result.result) # Incorrect type of action

main()
```