class BeautifulHelpFormat:

	def __init__(self):
		self.cmd: str = "{name} - {desc}\n\targs: {args}"
		self.default_desc: str = "none"
		self.required_arg = "<{name}:{type}>"
		self.positional_arg = "*{name}:{type}"
		self.optional_arg = "[{name}:{type} = {default}]"
		self.named_arg = "**{name}:{type}"
		self.arg_separator = ", "
		self.cmd_separator = "\n"