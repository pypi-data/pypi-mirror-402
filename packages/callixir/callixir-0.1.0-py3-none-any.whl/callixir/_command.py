class Command:

	def __init__(
			self,
			command_str: str,
			name: str | None = None,
			error: Exception | None = None,
			err_traceback: str = None,
			ppt: int = 0,
			fet: int = 0,
			args: list[str] = [],
			result: str | None = None
	):
		self.name = name
		self.command_str = command_str
		self.error = error
		self.err_traceback = err_traceback
		self.args = args
		self.result = result
		# ppt = preparation time
		self.ppt = ppt
		# fet = function execution time
		self.fet = fet