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
import os
import time
from math import ceil
import numpy as np
from random import randint
import VisionEgg
import SigTools
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
from AppTools.Shapes import Block
import AppTools.Meters
import BCPy2000.BCI2000Tools.FileReader as FileReader
from EeratAPI.API import *
from MyPythonApps.OnlineAPIExtension import *

class BciApplication(BciGenericApplication):
	
	#############################################################
	
	def Description(self):
		return "Provides feedback about contraction and cumulative duration of sustained contraction."
		
	#############################################################
	
	def Construct(self):
		# supply any BCI2000 definition strings for parameters and
		# states needed by this module
		#See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
		params = [
			#"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
			#See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
			
			"PythonApp:Contingency 	list 		ContingentChannel= 1 EDC % % % // Processed-channel for monitoring EMG",
			"PythonApp:Contingency 	float 		DurationMin= 2.6 2.6 0 % // Duration s which signal must continuously meet criteria before counting",
			"PythonApp:Contingency 	float 		DurationTotal= 60 60 0 % // Cumulative duration (s) of sustained contraction",
			"PythonApp:Contingency 	float 		MVIC= 600 600 0 % // MVIC in uV",
			"PythonApp:Contingency 	floatlist 	AmplitudeRange= {Min Max} 20 40 0 0 % //Min and Max as pcnt MVIC for signal amplitude criteria.",
			
			"PythonApp:Display 	string 	CriteriaMetColor= 0x00FF00 0xFFFFFF 0x000000 0xFFFFFF // Color of feedback when signal criteria met (color)",
			"PythonApp:Display 	string 	CriteriaOutColor= 0xCBFFCF 0xFFFFFF 0x000000 0xFFFFFF // Color of feedback when signal criteria not met (color)",
			"PythonApp:Display 	string 	BGColor= 0x000000 0x000000 0x000000 0xFFFFFF // Color of background (color)",
			"PythonApp:Display 	string	InRangeBGColor= 0x000000 0x000000 0x000000 0xFFFFFF // Color of background indicating target range (color)",
			"PythonApp:Display 	int		FeedbackType= 0 0 0 2 // Feedback type: 0 bar, 1 trace, 2 cursor (enumeration)",#Only supports bar for now
			"PythonApp:Display 	int		RangeMarginPcnt= 20 20 0 % // Percent of the display to use as a margin around the range",
			
			"PythonApp:Screen   int    ScreenId=           -1    -1     %   %  // on which screen should the stimulus window be opened - use -1 for last",
			"PythonApp:Screen   float  WindowSize=         0.8   1.0   0.0 1.0 // size of the stimulus window, proportional to the screen",
		]
		states = [
			#Name Length(nBits up to 32) Value ByteLocation(in state vector) BitLocation(0 to 7) CRLF
			#http://bci2000.org/wiki/index.php/Technical_Reference:State_Definition
			#Typically, state values change once per block or once per trial.
			#State values are saved per block.
			
			"Intertrial 1 0 0 0",
			"Inrange 1 0 0 0", #1 for Inrange, 0 for Outrange. This is not a phase state, but actually reflects the signal.
			"SummingBlocks 1 0 0 0",#Keep track of whether or not we are adding blocks to the cumulative sum.
			"Posttrial 1 0 0 0", #To clear the screen.
			"SignalCriteriaMetBlocks 16 0 0 0", #in blocks, 16-bit is max 65536
			"CumulativeDurationBlocks 16 0 0 0", #in blocks, 16-bit is max 65536
			"PercentComplete 8 0 0 0", #in blocks, 8-bit is max 256
		]
		
		return params,states
		
	#############################################################
	
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

		#TODO: Check that MVIC makes sense.
		self.mvic=self.params['MVIC'].val
		#Check that the range makes sense.
		self.amprange=np.asarray(self.params['AmplitudeRange'].val, dtype='float64')
		if len(self.amprange)!=2: raise EndUserError, "AmplitudeRange must have 2 values"
		if self.amprange[0]>self.amprange[1]: raise EndUserError, "AmplitudeRange must be in increasing order"
		
		###################################
		# Get the subject in the database #
		###################################
		#self.subject=get_or_create(Subject, Name=self.params['SubjectName'])#Should crash if subject not in db.
		
	#############################################################
	
	def Initialize(self, indim, outdim):
		
		##########
		# SCREEN #
		##########
		self.screen.color = (0,0,0) #let's have a black background
		scrw,scrh = self.screen.size #Get the screen dimensions.
		
		#Target box:
		#Convert range from %MVIC to amplitude.
		self.amprange=(self.amprange/100)*self.mvic
		
		#There is a linear transformation from amplitude to screen coordinates for the y-dimension
		#The equation is y=mx+b where y is the screen coordinates, x is the signal amplitude, b is the screen coordinate for 0-amplitude, and m is the slope.
		mgn=float(self.params['RangeMarginPcnt'].val)/100
		margin=(max(self.amprange[1],0)-min(self.amprange[0],0))*mgn	#Add a margin around the full range
		plot_max=max(self.amprange[1]+margin,0+margin)					#With the margin, what is the new max...
		plot_min=min(self.amprange[0]-margin,0-margin)					#... and the new min plot range.
		m=scrh/(plot_max-plot_min)										#From the range we can get the slope
		b=-1*m*plot_min													#From the slope we can get the intercept
		#Setup the target box
		target_box = Block(position=(0,m*self.amprange[0]+b), size=(scrw,m*(self.amprange[1]-self.amprange[0])), color=(1,0,0,0.5), anchor='lowerleft')
		self.stimulus('target_box', z=1, stim=target_box)
		#Setup the feedback bar
		self.addbar(color=(0,1,0), pos=(scrw/2.0,b), thickness=scrw/10, fac=m)
		self.stimuli['bartext_1'].position=(50,50)
		self.stimuli['bartext_1'].color=[0,0,0]
		
		addstatemonitor(self, 'PercentComplete')
		
		#######################################################
		# (Convert and) Attach contingency parameters to self #
		#######################################################
		self.eegfs=self.nominal['SamplesPerSecond'] #Sampling rate
		spb=self.nominal['SamplesPerPacket'] #Samples per block/packet
		self.dmin=int(ceil(self.params['DurationMin'].val * self.eegfs / spb)) #Convert DurationMin to blocks
		self.dtotal=int(ceil(self.params['DurationTotal'].val * self.eegfs / spb)) #Convert DurationMin to blocks
		
		################################
		# State monitors for debugging #
		################################
		if int(self.params['ShowSignalTime']):
			# turn on state monitors iff the packet clock is also turned on
			addstatemonitor(self, 'Running', showtime=True)
			addstatemonitor(self, 'CurrentBlock')
			addstatemonitor(self, 'CurrentTrial')
			addstatemonitor(self, 'Intertrial')
			addstatemonitor(self, 'Inrange')
			addstatemonitor(self, 'SignalCriteriaMetBlocks')
			addstatemonitor(self, 'SummingBlocks')
			addstatemonitor(self, 'CumulativeDurationBlocks')
						
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
		self.states['SignalCriteriaMetBlocks']=0
		self.states['CumulativeDurationBlocks']=0
		self.states['PercentComplete']=0
		
	#############################################################
	
	def Phases(self):
		# define phase machine using calls to self.phase and self.design
		self.phase(name='intertrial', next='outrange', duration=500)#TODO Replace this duration with some parameter
		self.phase(name='outrange', next='inrange', duration=None)
		self.phase(name='inrange', next='posttrial', duration=None)
		self.phase(name='posttrial', next='intertrial', duration=100)
		self.design(start='intertrial', new_trial='intertrial')
		#Note that only Process can change phase from outrange, from inrange, and therefore into intertrial
		
	#############################################################
	
	def Transition(self, phase):
		# present stimuli and update state variables to record what is going on
		#Update some states
		self.states['Intertrial'] = int(phase in ['intertrial'])
		self.states['Posttrial'] = int(phase in ['posttrial'])
		#The Inrange state depends on the signal, not on the phase.
		
		if phase == 'intertrial':#Move trigger to the top so it is processed first.
			self.states['SignalCriteriaMetBlocks']=0#Reset the number of blocks
			self.states['CumulativeDurationBlocks']=0
		elif phase == 'outrange':
			self.stimuli['target_box'].color = [1, 0, 0]
		elif phase == 'inrange':
			self.stimuli['target_box'].color = [0, 1, 0]
			
		self.stimuli['barrect_1'].on = (phase in ['inrange', 'outrange'])
		
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
		self.updatebars(x)#Update visual stimulus based on x

		##############################################################
		# Update whether or not we are in range based on the signal  #
		# Note that the Inrange state is not related to the inrange  #
		# phase as it is possible to be Inrange while in other phases#
		##############################################################
		
		now_in_range = (x >= self.amprange[0]) and (x <= self.amprange[1])
		self.states['Inrange'] = now_in_range #update state
		#Why does SignalCriteriaMetBlocks add up faster than CumulativeDurationBlocks?
		now_adding = now_in_range and self.states['SignalCriteriaMetBlocks'] >= self.dmin
		self.states['SummingBlocks'] = now_adding #update state
		
		#increment the state tracking for how many blocks we are in range.
		self.states['SignalCriteriaMetBlocks'] = self.states['SignalCriteriaMetBlocks'] + 1 if now_in_range else 0
		self.states['CumulativeDurationBlocks'] = self.states['CumulativeDurationBlocks'] + 1 if now_adding else self.states['CumulativeDurationBlocks']
		self.states['PercentComplete'] =int(100 * self.states['CumulativeDurationBlocks'] / self.dtotal)
		
		##############################################
		# Manually change out of inrange or outrange #
		##############################################
		if int(self.states['CumulativeDurationBlocks']) > self.dtotal:
			self.change_phase('intertrial')
		#If we were in range, we can either stay or change to out.
		if self.in_phase('inrange') and not now_in_range:
			self.change_phase('outrange')
		#If we were out of range, we can either stay or change
		elif self.in_phase('outrange') and now_in_range:
			self.change_phase('inrange')
			
	#############################################################
	
	def Frame(self, phase):
		# update stimulus parameters if they need to be animated on a frame-by-frame basis
		pass
		
	#############################################################
	
	def Event(self, phase, event):
		# respond to pygame keyboard and mouse events
		import pygame.locals
		if event.type == pygame.locals.KEYDOWN:
			if event.key == ord('r'): self.color[:] = [1,0,0]
			if event.key == ord('g'): self.color[:] = [0,1,0]
			if event.key == ord('b'): self.color[:] = [0,0,1]
		
	#############################################################
	
	def StopRun(self):
		pass
	
#################################################################
#################################################################