#################################################################
#################################################################

class BciSignalProcessing(BciGenericSignalProcessing):	
	
	#############################################################
	
	def Description(self):
		return "Does nothing."
	
	#############################################################
	
	def Construct(self):
		parameters = [
			
		]
		states = [
			
		]
		return (parameters, states)
		
	#############################################################
	
	def Preflight(self, sigprops):
		pass
				
	#############################################################TMSTrigc TMSTriga NerveTrigc NerveTriga EDCc EDCa FCRc FCRa
	
	def Initialize(self, indim, outdim):
		pass		
	#############################################################
	
	def Process(self, sig):
		return sig
	
#################################################################
#################################################################