

import typing

import jk_prettyprintobj




from .TextChunk import TextChunk





class HWriter2(jk_prettyprintobj.DumpMixin):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	def __init__(self):
		self.__lines:list[str] = []				# holds all completed lines
		self.__buffer:list[str] = []			# holds all fragments for the next line to add
		self.__stack = [{}]
		self.__chunkConverters:dict[str,typing.Callable[[typing.Any],str]] = {}
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	@property
	def _nIndentLevel(self) -> int:
		return (len(self.__stack) - 1)
	#

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def _dump(self, ctx:jk_prettyprintobj.DumpCtx):
		ctx.dumpVar("__lines", self.__lines)
		ctx.dumpVar("__buffer", self.__buffer)
	#

	def __toStr(self, item) -> str|None:
		if isinstance(item, TextChunk):
			conv = self.__chunkConverters.get(item.chunkType)
			if conv is None:
				raise Exception("No converter registered for chunk type " + repr(item.chunkType) + "!")
			item = conv(item)
			if item is not None:
				assert isinstance(item, str)
				if item:
					return item
			return None
		else:
			return str(item)
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def registerTextChunkConverter(self, chunkType:str, converterCallback:typing.Callable[[typing.Any],str]):
		assert isinstance(chunkType, str)
		assert callable(converterCallback)

		self.__chunkConverters[chunkType] = converterCallback
	#

	def __len__(self):
		if self.__buffer:
			s = "".join(self.__buffer).rstrip()
			if s:
				return len(self.__lines) + 1
		else:
			return len(self.__lines)
	#

	def write(self, *items):
		for item in items:
			if isinstance(item, TextChunk):
				item = self.__toStr(item)
				if item:
					self.__buffer.append(item)
			elif isinstance(item, str):
				if item:
					self.__buffer.append(item)
			elif hasattr(type(item), "__iter__"):
				for item2 in item:
					s = self.__toStr(item2)
					if s:
						self.__buffer.append(s)
			else:
				s = str(item)
				if s:
					self.__buffer.append(s)
	#

	def lineBreak(self):
		if self.__buffer:
			s = "".join(self.__buffer).rstrip()
			if s:
				self.__lines.append("\t" * self._nIndentLevel + s)
			self.__buffer.clear()
	#

	def doubleLineBreak(self):
		self.lineBreak()
		if self.__lines and self.__lines[-1]:
			self.__lines.append("")
	#

	def writeLn(self, *items):
		self.write(*items)
		self.lineBreak()
	#

	def __enter__(self):
		if self.__buffer:
			self.lineBreak()
		self.__stack.append({})
	#

	def __exit__(self, ex, exType, exStackTrace):
		if self.__buffer:
			self.lineBreak()
		if self._nIndentLevel == 0:
			raise Exception("Deindentation error!")
		self.__stack.pop()
	#

	def incrementIndent(self):
		if self.__buffer:
			self.lineBreak()
		self.__stack.append({})
	#

	def decrementIndent(self):
		if self.__buffer:
			self.lineBreak()
		if self._nIndentLevel == 0:
			raise Exception("Deindentation error!")
		self.__stack.pop()
	#

	#
	# Get a list of lines (without line breaks).
	#
	def toLines(self) -> typing.List[str]:
		self.lineBreak()
		return list(self.__lines)
	#

	def toStr(self) -> str:
		self.lineBreak()
		return "\n".join(self.__lines)
	#

	def __str__(self):
		self.lineBreak()
		return "\n".join(self.__lines)
	#

	def __repr__(self):
		return "HWriter<" + str(len(self.__lines)) + " lines>"
	#

	def __getitem__(self, key:str):
		for stackVars in reversed(self.__stack):
			if key in stackVars:
				return stackVars[key]
		return None
	#

	def __setitem__(self, key:str, value):
		self.__stack[-1][key] = value
	#

#






