import numpy as np

class FakeFeedback(object):
	params = [
			"PythonApp:Feedback    int		FakeFeedback=       0 % % %         // Yoke feedback to previous data? (boolean)",
			"PythonApp:Feedback    matrix	FakeFiles=        	2 1 none none % % % // Path to file/s",
		]
	@classmethod
	def preflight(cls,app):
		#TODO: Make sure the files exist
		pass
	@classmethod
	def initialize(cls,app):
		#Load the file
		#Extract the value from states
		#Close the file?
		pass
	@classmethod
	def startrun(cls,app):
		pass
	@classmethod
	def transition(cls,app,phase):
		pass