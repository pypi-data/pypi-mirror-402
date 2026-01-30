




class HWriter(object):

	################################################################################################################################
	## Constants
	################################################################################################################################

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	def __init__(self):
		self.__bIsNewLine = True		# are we at a new line position?
		self.__bHasContent = False		# do we already have content in this line?
		self.__allParts:list[str] = []
		self.__prefix = ""
		self.__nIndent = 0
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def incrementIndent(self):
		self.__nIndent += 1
		if self.__nIndent > len(self.__prefix):
			self.__prefix += "\t"
	#

	def decrementIndent(self):
		if self.__nIndent == 0:
			raise Exception("Indentation error!")
		self.__nIndent -= 1
	#

	def write(self, *items):
		# print("write( " + repr(items) + " )")

		if self.__bIsNewLine:
			self.__bIsNewLine = False

		for item in items:
			if isinstance(item, str):
				if not self.__bHasContent:
					self.__allParts.append(self.__prefix[:self.__nIndent])
				self.__allParts.append(item)
				self.__bHasContent = True
			elif hasattr(type(item), "__iter__"):
				for i in item:
					if len(i) > 0:
						if not self.__bHasContent:
							self.__allParts.append(self.__prefix[:self.__nIndent])
						self.__allParts.append(i)
						self.__bHasContent = True
			else:
				if len(item) > 0:
					if not self.__bHasContent:
						self.__allParts.append(self.__prefix[:self.__nIndent])
					self.__allParts.append(item)
					self.__bHasContent = True
	#

	def writeLn(self, *items):
		# print("writeLn( " + repr(items) + " )")

		if self.__bIsNewLine:
			self.__bIsNewLine = False

		for item in items:
			if isinstance(item, str):
				if not self.__bHasContent:
					self.__allParts.append(self.__prefix[:self.__nIndent])
				self.__allParts.append(item)
				self.__bHasContent = True
			elif hasattr(type(item), "__iter__"):
				for i in item:
					if len(i) > 0:
						if not self.__bHasContent:
							self.__allParts.append(self.__prefix[:self.__nIndent])
						self.__allParts.append(i)
						self.__bHasContent = True
			else:
				if len(item) > 0:
					if not self.__bHasContent:
						self.__allParts.append(self.__prefix[:self.__nIndent])
					self.__allParts.append(item)
					self.__bHasContent = True

		self.lineBreak()
	#

	#
	# Add a line break if (and only if) the last item was not a line break.
	# Typically you won't want to use this method but <c>writeLn</c> instead.
	# <c>writeLn</c> will add a line in any case.
	#
	def lineBreak(self):
		if not self.__bIsNewLine:
			self.__bHasContent = False
			self.__allParts.append("\n")
			self.__bIsNewLine = True
	#

	#
	# Get a list of lines (without line breaks).
	#
	def getLines(self) -> list:
		ret = []
		iStart = 0
		iMax = len(self.__allParts)
		for i in range(0, iMax):
			if self.__allParts[i] == "\n":
				ret.append("".join(self.__allParts[iStart:i]))
				iStart = i + 1
		if iMax > iStart:
			ret.append("".join(self.__allParts[iStart:]))
		return ret
	#

	def toString(self) -> str:
		self.lineBreak()
		return "".join(self.__allParts)
	#

	def __str__(self):
		self.lineBreak()
		return "".join(self.__allParts)
	#

	def __repr__(self):
		return "HWriter<" + str(len(self.__allParts)) + " parts>"
	#

	################################################################################################################################
	## Public Static Methods
	################################################################################################################################

#







