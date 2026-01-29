from typing import Callable, Any, Dict
from ._fingerprint import Fingerprint

class CommandMeta:

	def __init__(self, name: str, func: Callable, fingerprint: Fingerprint, desc: str):
		self.name = name
		self.func = func
		self.fingerprint = fingerprint
		self.desc = desc

	def __repr__(self):
		return f"CommandMeta(name={self.name})"
