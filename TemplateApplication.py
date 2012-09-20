#   This file is a BCPy2000 application developer file, 
#	for use with BCPy2000
#	http://bci2000.org/downloads/BCPy2000/BCPy2000.html
# 
#	Author:	Chadwick Boulay
#   chadwick.boulay@gmail.com
#   
#===============================================================================
# With the inclusion of some extensions, and without too much modification,
# this BCPy2000 application should support many combinations of the following experimental pieces:
# -TMS or nerve stimulation
# -Task progression contingent on a specified signal remaining within a specified range for some specified duration
#	-The amplitude of the specified signal and the desired range may or may not be displayed.
# -Real-time feedback of a brain-signal
#	-Feedback may be on-screen or through an external device
# -Feedback of an evoked potential
#	-Feedback properties may use information from previous ERPs (e.g., residual of a multivariable model)
#===============================================================================
	
import numpy as np
from random import randint, uniform, random
from math import ceil
import time

import VisionEgg
import SigTools
from AppTools.Boxes import box
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
from AppTools.Shapes import Disc

from ContingencyExtension import ContingencyApp
from ContinuousFeedbackExtension import FeedbackApp
from MagstimExtension import MagstimApp
from DigitimerExtension import DigitimerApp
from ERPExtension import ERPApp

class BciApplication(BciGenericApplication):
	
	def Description(self):
		return "Template application"
		
	#############################################################
	def Construct(self):
		#See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
		#See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
		params = [
			"PythonApp:Design	list	GoCueText=		 2 Imagery Rest % % % // Text for cues (max 2 targets for now)",
			"PythonApp:Design	int		AlternateCues=    0     0     0   1  // Alternate target classes (true) or choose randomly (boolean)",
			"PythonApp:Design  float	IntertrialDur=	  0.5   0.5   0.0 100.0 // Intertrial duration in seconds",
			"PythonApp:Design  float	BaselineDur=		4.0   4.0   0.0 100.0 // Baseline duration in seconds",
			"PythonApp:Design  float	TaskDur=			6.0   6.0   0.0 100.0 // Min task duration in seconds (unless contingency)",
			"PythonApp:Design  float	TaskRand=			3.0   3.0   0.0 100.0 // Additional randomization in seconds (unless contingency)",
			"PythonApp:Display  int		ScreenId=		   -1	-1	 %   %  // on which screen should the stimulus window be opened - use -1 for last",
			"PythonApp:Display  float	WindowSize=		 0.8   1.0   0.0 1.0 // size of the stimulus window, proportional to the screen",
			]
		params.extend(ContingencyApp.params)
		params.extend(MagstimApp.params)
		params.extend(DigitimerApp.params)
		params.extend(ERPApp.params)
		params.extend(FeedbackApp.params)	
		states = [
			#===================================================================
			# "Intertrial 1 0 0 0",
			# "Baseline 1 0 0 0",
			# "GoCue 1 0 0 0",
			# "Task 1 0 0 0",
			# "Response 1 0 0 0",
			# "StopCue 1 0 0 0",
			"TargetCode 4 0 0 0",
			"TaskNBlocks 12 0 0 0",
			"TrialPhase 4 0 0 0",
			#===================================================================
		]
		states.extend(ContingencyApp.states)
		states.extend(MagstimApp.states)
		states.extend(DigitimerApp.states)
		states.extend(ERPApp.states)
		states.extend(FeedbackApp.states)
		return params,states
		
	#############################################################
	def Preflight(self, sigprops):
		#Setup screen
		siz = float(self.params['WindowSize'])
		screenid = int(self.params['ScreenId'])  # ScreenId 0 is the first screen, 1 the second, -1 the last
		fullscreen(scale=siz, id=screenid, frameless_window=(siz==1)) # only use a borderless window if the window is set to fill the whole screen
		
		self.nclasses = len(self.params['GoCueText'])#Must be defined in Preflight because it is used by extension preflight.
		
		ContingencyApp.preflight(self, sigprops)
		MagstimApp.preflight(self, sigprops)
		DigitimerApp.preflight(self, sigprops)
		ERPApp.preflight(self, sigprops)
		FeedbackApp.preflight(self, sigprops)
		
	#############################################################
	def Initialize(self, indim, outdim):
		
		#=======================================================================
		# Screen
		#=======================================================================
		self.screen.color = (0,0,0) #let's have a black background
		self.scrw,self.scrh = self.screen.size #Get the screen dimensions.
		
		#===================================================================
		# Create a box object as the coordinate frame for the screen.
		# Manipulate its properties to get positional information for stimuli.
		#===================================================================
		scrsiz = min(self.scrw,self.scrh)
		siz = (scrsiz, scrsiz)
		b = box(size=siz, position=(self.scrw/2.0,self.scrh/2.0), sticky=True)
		center = b.map((0.5,0.5), 'position')
		self.positions = {'origin': np.matrix(center)} #Save the origin for later.

		#=======================================================================
		# Register the basic stimuli.
		#=======================================================================
		self.stimulus('cue', z=5, stim=VisualStimuli.Text(text='?', position=center, anchor='center', color=(1,1,1), font_size=50, on=False))
		self.stimulus('fixation', z=4.2, stim=Disc(position=center, radius=5, color=(1,1,1), on=False))
		
		#=======================================================================
		# Share some variables with the extensions.
		#=======================================================================
		self.eegfs = self.nominal['SamplesPerSecond'] #Sampling rate
		self.spb = self.nominal['SamplesPerPacket'] #Samples per block/packet
		self.block_dur = 1000*self.spb/self.eegfs#duration (ms) of a sample block

		#=======================================================================
		# State monitors for debugging.
		#=======================================================================
		if int(self.params['ShowSignalTime']):
			# turn on state monitors iff the packet clock is also turned on
			addstatemonitor(self, 'Running', showtime=True)
			addstatemonitor(self, 'CurrentBlock')
			addstatemonitor(self, 'CurrentTrial')
			addstatemonitor(self, 'TargetCode')
			addstatemonitor(self, 'TaskNBlocks')
			addstatemonitor(self, 'TrialPhase')
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

		MagstimApp.initialize(self, indim, outdim)
		DigitimerApp.initialize(self, indim, outdim)
		ContingencyApp.initialize(self, indim, outdim)
		ERPApp.initialize(self, indim, outdim)
		FeedbackApp.initialize(self, indim, outdim)
		
	#############################################################
	def Halt(self):
		if self.params.has_key('MSEnable') and self.params['MSEnable'].val: MagstimApp.halt(self)
		if self.params.has_key('DigitimerEnable') and self.params['DigitimerEnable'].val: DigitimerApp.halt(self)
		if self.params.has_key('ContingencyEnable') and self.params['ContingencyEnable'].val: ContingencyApp.halt(self)
		if self.params.has_key('ERPDatabaseEnable') and self.params['ERPDatabaseEnable'].val: ERPApp.halt(self)
		if self.params.has_key('ContFeedbackEnable') and self.params['ContFeedbackEnable'].val: FeedbackApp.halt(self)
		
	#############################################################
	def StartRun(self):
		#if int(self.params['ShowFixation']):
		self.stimuli['fixation'].on = True
		MagstimApp.startrun(self)
		DigitimerApp.startrun(self)
		ContingencyApp.startrun(self)
		ERPApp.startrun(self)
		FeedbackApp.startrun(self)
		
	#############################################################
	def StopRun(self):
		MagstimApp.stoprun(self)
		DigitimerApp.stoprun(self)
		ContingencyApp.stoprun(self)
		ERPApp.stoprun(self)
		FeedbackApp.stoprun(self)
		
	#############################################################
	def Phases(self):
		# define phase machine using calls to self.phase and self.design
		self.phase(name='intertrial', next='baseline', duration=self.params['IntertrialDur'].val*1000.0)
		self.phase(name='baseline', next='gocue', duration=self.params['BaselineDur'].val*1000.0)
		self.phase(name='gocue', next='task', duration=1000)
		self.phase(name='task', next='response',duration=None)
		self.phase(name='response', next='stopcue',\
				duration=None if int(self.params['ERPDatabaseEnable']) else 100)
		self.phase(name='stopcue', next='intertrial', duration=1000)

		self.design(start='intertrial', new_trial='intertrial')
		
	#############################################################
	def Transition(self, phase):
		# present stimuli and update state variables to record what is going on
		#=======================================================================
		# #Update some states
		# self.states['Intertrial'] = int(phase in ['intertrial'])
		# self.states['Baseline'] = int(phase in ['baseline'])
		# self.states['GoCue'] = int(phase in ['gocue'])
		# self.states['Task'] = int(phase in ['task'])
		# self.states['Response']  = int(phase in ['response'])
		# self.states['StopCue']  = int(phase in ['stopcue'])
		#=======================================================================
		
		if phase == 'intertrial':
			self.states['TrialPhase'] = 0
			
		elif phase == 'baseline':
			self.states['TrialPhase'] = 1
			if int(self.params['AlternateCues']): self.states['TargetCode'] = 1 + self.states['CurrentTrial'] % self.nclasses
			else: self.states['TargetCode'] = randint(1,self.nclasses)
		
		elif phase == 'gocue':
			self.states['TrialPhase'] = 2
			
			t = self.states['TargetCode']
			self.stimuli['cue'].text = self.params['GoCueText'][t-1]
			
		elif phase == 'task':
			self.states['TrialPhase'] = 3
			if int(self.params['ContingencyEnable']):
				self.states['TaskNBlocks'] = 0
			else:
				task_length = self.params['TaskDur'].val + random()*self.params['TaskRand'].val
				self.states['TaskNBlocks'] = task_length * self.eegfs / self.spb
			
		elif phase == 'response':
			self.states['TrialPhase'] = 4
		
		elif phase == 'stopcue':
			self.states['TrialPhase'] = 5
			self.stimuli['cue'].text = "Relax"
			self.states['TargetCode'] = 0
			
		self.stimuli['cue'].on = (phase in ['gocue', 'stopcue'])
		
		MagstimApp.transition(self, phase)
		DigitimerApp.transition(self, phase)
		ContingencyApp.transition(self, phase)
		ERPApp.transition(self, phase)
		FeedbackApp.transition(self, phase)
					
	#############################################################
	def Process(self, sig):
		#Process is called on every packet
		#Phase transitions occur independently of packets
		#Therefore it is not desirable to use phases for application logic in Process
		MagstimApp.process(self, sig)
		DigitimerApp.process(self, sig)
		ContingencyApp.process(self, sig)
		ERPApp.process(self, sig)
		FeedbackApp.process(self, sig)
		
		#If we are in Task, and we are using ContingencyApp or MagstimApp or DigitimerApp
		if self.in_phase('task', min_packets=self.states['TaskNBlocks']):
			contingency_met = not int(self.params['ContingencyEnable']) or self.states['ContingencyOK']
			magstim_ready = not int(self.params['MSEnable']) or self.states['MagstimReady']
			digitimer_ready = not int(self.params['DigitimerEnable']) or self.states['DigitimerReady']
			if contingency_met and magstim_ready and digitimer_ready:
				self.change_phase('response')
			
		#If we are in Response and we are using ERPApp
		if self.in_phase('response') and int(self.params['ERPDatabaseEnable']):
			#Progress from Response to stopcue if the ERP has been collected.
			if self.states['ERPCollected']: self.change_phase('stopcue')
	
	#############################################################
	def Frame(self, phase):
		# update stimulus parameters if they need to be animated on a frame-by-frame basis
		pass
	
	#############################################################
	def Event(self, phase, event):
		MagstimApp.event(self, phase, event)
		DigitimerApp.event(self, phase, event)
		ContingencyApp.event(self, phase, event)
		ERPApp.event(self, phase, event)
		FeedbackApp.event(self, phase, event)
		
#################################################################
#################################################################