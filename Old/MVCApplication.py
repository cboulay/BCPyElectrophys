#   This file is a BCPy2000 application developer file, 
#	for use with BCPy2000
#	http://bci2000.org/downloads/BCPy2000/BCPy2000.html
# 
#	Author:	Chadwick Boulay
#   chadwick.boulay@gmail.com
#   
#   This program is free software: you can redistribute it
#   and/or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

# This application provides feedback about the amplitude of a specific
# (processed) input channel. Whenever some criteria are met, then
# a trigger is sent out through a stimulator. The evoked response
# is trapped and passed off to an external application.
import numpy as np
from random import randint
from math import ceil
import VisionEgg
import SigTools
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
from AppTools.Shapes import Block
import AppTools.Meters
from EeratAPI.API import *
from MyPythonApps.OnlineAPIExtension import *

class BciApplication(BciGenericApplication):
	
	#############################################################
	
	def Description(self):
		return "Cues contraction and provides instantaneous feedback about 1 channel."
		
	#############################################################
	
	def Construct(self):
		# supply any BCI2000 definition strings for parameters and
		# states needed by this module
		#See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
		params = [
			#"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
			#See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
			
			"PythonApp:MVC 	float 		MVCDuration= 5 5 0 % // Duration s of contraction",
			"PythonApp:MVC 	float 		MVCRest= 45 60 0 % // Duration s of rest between trials",
			"PythonApp:MVC 	list 		ContingentChannel= 1 EDC % % % // Processed-channel which modulates feedback.",
			"PythonApp:MVC 	floatlist 	AmplitudeRange= {Min Max} 0 100 0 0 % //Starting Min and Max range for plotting.",
			
			"PythonApp:Display 	string 	BGColor= 0x000000 0x000000 0x000000 0xFFFFFF // Color of background (color)",
			"PythonApp:Display 	int		RangeMarginPcnt= 10 10 0 % // Percent of the display to use as a margin around the range",
			
			"PythonApp:Screen   int    ScreenId=           -1    -1     %   %  // on which screen should the stimulus window be opened - use -1 for last",
			"PythonApp:Screen   float  WindowSize=         0.8   1.0   0.0 1.0 // size of the stimulus window, proportional to the screen",
		]
		states = [
			#Name Length(nBits up to 32) Value ByteLocation(in state vector) BitLocation(0 to 7) CRLF
			#http://bci2000.org/wiki/index.php/Technical_Reference:State_Definition
			#Typically, state values change once per block or once per trial.
			#State values are saved per block.
			
			"Cue 1 0 0 0",
			"MVC 1 0 0 0",
			"Rest 1 0 0 0",
			"Value 16 0 0 0", #in blocks, 16-bit is max 65536
		]
		
		return params,states
		
	def Halt(self):
		#Use this hook to cleanup things from initialize
		pass
	
	def Preflight(self, sigprops):
		
		##############################################
		# http://visionegg.org/manual/visionegg.html #
		##############################################
		# Here is where you would set VisionEgg.config parameters,
		# either using self.screen.setup(), or (for more advanced
		# options) directly like, e.g. this to make the window draggable:
		#VisionEgg.config.VISIONEGG_FRAMELESS_WINDOW = 0  # gives the window a title bar
		siz = float(self.params['WindowSize'])
		screenid = int(self.params['ScreenId'])  # ScreenId 0 is the first screen, 1 the second, -1 the last
		fullscreen(scale=siz, id=screenid, frameless_window=(siz==1)) # only use a borderless window if the window is set to fill the whole screen
		
		###############################
		# CONTINGENCY PARAMETER CHECK #
		###############################

		# Make sure ContingentChannel is in the list of channels.
		chn = self.inchannels()
		pch = self.params['ContingentChannel'].val
		use_process = len(pch) != 0
		if use_process:
			if False in [isinstance(x, int) for x in pch]:
				nf = filter(lambda x: not str(x) in chn, pch)
				if len(nf): raise EndUserError, "ContingentChannel %s not in module's list of input channel names" % str(nf)
				self.procchan = [chn.index(str(x)) for x in pch]
			else:
				nf = [x for x in pch if x < 1 or x > len(chn) or x != round(x)]
				if len(nf): raise EndUserError, "Illegal ContingentChannel: %s" % str(nf)
				self.procchan = [x-1 for x in pch]		
		else:
			raise EndUserError, "Must supply ContingentChannel"
		
		#Check that the range makes sense.
		amprange=self.params['AmplitudeRange'].val
		if len(amprange)!=2: raise EndUserError, "AmplitudeRange must have 2 values"
		if amprange[0]>amprange[1]: raise EndUserError, "AmplitudeRange must be in increasing order"
		self.amprange=amprange
		
		#This should crash if the subject does not exist in the db because we have not provided all the keys.
		self.subject=get_or_create(Subject, Name=self.params['SubjectName'])
		
	#############################################################
	
	def Initialize(self, indim, outdim):
		
		##########
		# SCREEN #
		##########
		self.screen.color = (0,0,0) #let's have a black background
		scrw,scrh = self.screen.size #Get the screen dimensions.
		
		#There is a linear transformation from amplitude to screen coordinates for the y-dimension
		#The equation is y=mx+b where y is the screen coordinates, x is the signal amplitude, b is the screen coordinate for 0-amplitude, and m is the slope.
		bar_fac,bar_pos=self.getBarParms(x=0)
		
		#Setup the feedback bar
		#self.addbar(color=(0,0,1), font_size=26, pos=None, thickness=10, fliplr=False, baseline=0.0, fac=200.0/10.0, horiz=False, fmt='%+.2f', font_name=None)
		#addbar sets bartext_1 and barrect_1 stimuli as bcibar.textobj and bcibar.rectobj
		#I don't know if updating bcibar will cause the on-screen bar to change.
		#We might have to remove the bar then add another.
		self.bcibar=self.addbar(color=(0,1,0), pos=bar_pos, thickness=scrw/10, fac=bar_fac)
		self.stimuli['bartext_1'].position=(50,50)
		self.stimuli['bartext_1'].color=[0,0,0]
		
		#Setup the text cues
		self.stimulus('cue', z=1, stim=VisualStimuli.Text(text='?', position=(scrw/2,scrh/2), anchor='center', color=(1,1,1), font_size=50, on=False))
		
		# set up the strings that are going to be presented in the 'cue' stimulus
		self.cuetext = ['GET READY', 'relax']
		
		#######################################################
		# (Convert and) Attach contingency parameters to self #
		#######################################################
		self.eegfs=self.nominal['SamplesPerSecond'] #Sampling rate
		spb=self.nominal['SamplesPerPacket'] #Samples per block/packet
		
		
		################################
		# State monitors for debugging #
		################################
		if int(self.params['ShowSignalTime']):
			# turn on state monitors iff the packet clock is also turned on
			addstatemonitor(self, 'Running', showtime=True)
			addstatemonitor(self, 'CurrentBlock')
			addstatemonitor(self, 'CurrentTrial')
			addstatemonitor(self, 'Cue')
			addstatemonitor(self, 'MVC')
			addstatemonitor(self, 'Rest')
						
			addphasemonitor(self, 'phase', showtime=True)

			m = addstatemonitor(self, 'fs_reg')
			m.func = lambda x: '% 6.1fHz' % x._regfs.get('SamplesPerSecond', 0)
			m.pargs = (self,)
			m = addstatemonitor(self, 'fs_avg')
			m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('global', 0)
			m.pargs = (self,)
			m = addstatemonitor(self, 'fs_run')
			m.func = lambda x: '% 6.1fHz' % x.estimated.get('SamplesPerSecond',{}).get('running', 0)
			m.pargs = (self,)
			m = addstatemonitor(self, 'fr_run')
			m.func = lambda x: '% 6.1fHz' % x.estimated.get('FramesPerSecond',{}).get('running', 0)
			m.pargs = (self,)

			self.stimuli['bartext_1'].color=[0,1,0]
		
	#############################################################
	
	def StartRun(self):
		pass
		
	#############################################################
	
	def Phases(self):
		# define phase machine using calls to self.phase and self.design
		self.phase(name='intertrial', next='startcue', duration=500)
		self.phase(name='startcue', next='mvc', duration=2000)
		self.phase(name='mvc', next='restcue', duration=1000*self.params['MVCDuration'].val)
		self.phase(name='restcue', next='intertrial', duration=1000*self.params['MVCRest'].val if self.states['CurrentTrial']<self.params['TrialsPerBlock'].val else 100)
		self.design(start='intertrial', new_trial='intertrial')
		
	#############################################################
	
	def Transition(self, phase):
		# present stimuli and update state variables to record what is going on
		#Update some states
		self.states['Cue'] = int(phase in ['startcue'])
		self.states['MVC'] = int(phase in ['mvc'])
		self.states['Rest'] = int(phase in ['restcue'])
		
		self.stimuli['cue'].on = (phase in ['startcue', 'restcue'])
		self.stimuli['barrect_1'].on = (phase in ['mvc'])
		
		if phase == 'restcue':
			self.stimuli['cue'].text = self.cuetext[1]
		elif phase == 'startcue':
			self.stimuli['cue'].text = self.cuetext[0]
		
	#############################################################
	
	def Process(self, sig):
		#Process is called on every packet
		#Phase transitions occur independently of packets
		#Therefore it is not desirable to use phases for application logic in Process
		
		###############################################
		# Update the feedback pos based on the signal #
		###############################################
		#Convert input signal to scalar
		x = sig[self.procchan,:].mean(axis=1)#still a matrix
		x=float(x)#single value
		
		bar_fac,bar_pos=self.getBarParms(x=x)
		self.bcibar.fac=bar_fac
		self.stimuli['barrect_1'].position=tuple(bar_pos)
		self.updatebars(x)#Update visual stimulus based on x
		self.states['Value']=int(x)
		
	#############################################################
	
	def Frame(self, phase):
		# update stimulus parameters if they need to be animated on a frame-by-frame basis
		pass
		
	#############################################################
	
	def Event(self, phase, event):
		pass
		
	#############################################################
	
	def StopRun(self):
		pass
	
	def getBarParms(self, x=0):
		scrw,scrh = self.screen.size
		mgn=self.params['RangeMarginPcnt'].val/100
		self.amprange[0]=min(self.amprange[0],x)
		self.amprange[1]=max(self.amprange[1],x)
		margin=(max(self.amprange[1],0)-min(self.amprange[0],0))*mgn	#Add a margin around the full range
		plot_max=max(self.amprange[1]+margin,x+margin)					#With the margin, what is the new max...
		plot_min=min(self.amprange[0]-margin,0-margin)					#... and the new min plot range.
		m=scrh/(plot_max-plot_min)										#From the range we can get the slope
		b=-1*m*plot_min													#From the slope we can get the intercept
		return m,(scrw/2.0,b)
	
#################################################################
#################################################################