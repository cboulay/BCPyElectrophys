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
# is trapped and passed off to an external application. The stimulator and external application are configurable.
import numpy as np
from random import randint, uniform
from math import ceil
import VisionEgg
import SigTools
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
from AppTools.Shapes import Block
import AppTools.Meters
from EeratAPI.API import *
from MyPythonApps.OnlineAPIExtension import *
from MyBCPyModules.StimExtension import MEP, HR, MAPPING, IOCURVE, SICI
import pygame, pygame.locals
import time

class BciApplication(BciGenericApplication):
	#At the moment, this app is used for:
	#    1 - MEP mapping (no real-time map until Brainsight has API for coordinates)
	#    2 - MEP recruitment curve
	#    3 - MEP SICI
	#    4 - H-reflex hunting (assist finding ideal stim location)
	#    5 - H-reflex recruitment curve
	#
	#In the future, I hope this app can be used for operant conditioning too.
			
	#############################################################
	
	def Description(self):
		return "Provides instantaneous feedback about 1 channel and generates a trigger when some criteria are met."
		
	#############################################################
	
	def Construct(self):
		# supply any BCI2000 definition strings for parameters and
		# states needed by this module
		#See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
		params = [
			#"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
			#See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
			"PythonApp:Contingency  float 		ISIMin= 5 5 2 % // Minimum time s between stimuli",
			"PythonApp:Contingency 	list 		ContingentChannel= 1 EDC % % % // Processed-channel on which the trigger is contingent",
			"PythonApp:Contingency 	float 		DurationMin= 2.6 2.6 0 % // Duration s which signal must continuously meet criteria before triggering",
			"PythonApp:Contingency 	float 		DurationRand= 0.3 0.3 0 % // Randomization s around the duration",
			"PythonApp:Contingency 	float 		MVIC= 600 600 0 % // MVIC in uV",
			"PythonApp:Contingency 	floatlist 	AmplitudeRange= {Min Max} 8 12 0 0 % //Min and Max for signal amplitude criteria in pcnt MVIC",
			#TODO: Some applications might want to trigger only when the signal enters the range in a certain direction.
			#"PythonApp:Contingency 	int 		RangeEnter= 0 0 0 2 // Signal must enter range from: 0 either, 1 below, 2 above (enumeration)",
			
			#Specify how this will be used.
			"PythonApp:Method	int			ExperimentType= 0 0 0 4 // Experiment Type: 0 MEPMapping, 1 MEPRecruitment, 2 MEPSICI, 3 HRHunting, 4 HRRecruitment (enumeration)",
			"PythonApp:Method	float	 	StimIntensity= 30 30 0 100 // 0-50 for DS5, 0-100 for Single-Pulse, 0-100 for Bistim Cond",
			"PythonApp:Method	list		TriggerInputChan= 1 Trig % % % // Name of channel used to monitor trigger / control ERP window",
			"PythonApp:Method	float		TriggerThreshold= 1 1 0 % // If monitoring trigger, use this threshold to determine ERP time 0",
			#"PythonApp:Method   int			UseSoftwareTrigger= 0 0 0 1  // Use phase change to determine trigger onset (boolean)",
			"PythonApp:Method	list		ERPChan= 1 EDC_RAW % % % // Channels to store in database (in addition to trigger)",
			"PythonApp:Method	floatlist	ERPWindow= {Start Stop} -500 500 0 % % // Stored window, relative to trigger onset, in millesconds",
			
			"PythonApp:Display 	string 	CriteriaMetColor= 0x00FF00 0xFFFFFF 0x000000 0xFFFFFF // Color of feedback when signal criteria met (color)",
			"PythonApp:Display 	string 	CriteriaOutColor= 0xCBFFCF 0xFFFFFF 0x000000 0xFFFFFF // Color of feedback when signal criteria not met (color)",
			"PythonApp:Display 	string 	BGColor= 0x000000 0x000000 0x000000 0xFFFFFF // Color of background (color)",
			"PythonApp:Display 	string	InRangeBGColor= 0x000000 0x000000 0x000000 0xFFFFFF // Color of background indicating target range (color)",
			"PythonApp:Display 	int		FeedbackType= 0 0 0 2 // Feedback type: 0 bar, 1 trace, 2 cursor (enumeration)",#Only supports bar for now
			#"PythonApp:Display  int		ShowLastERP=  1 1 0 1  // plot the last trial's ERP (boolean)",
			"PythonApp:Display 	int		RangeMarginPcnt= 20 20 0 % // Percent of the display to use as a margin around the range",
			"PythonApp:Display  int		ScreenId=           -1    -1     %   %  // on which screen should the stimulus window be opened - use -1 for last",
			"PythonApp:Display  float	WindowSize=         0.8   1.0   0.0 1.0 // size of the stimulus window, proportional to the screen",
			]
		#The ExperimentType determines the stimulator, its parameters, the trial criteria, and the data structure.
		#Many of these can be automatic but they also have their own parameters that may need to be set.
		params.extend(MEP.params)
		params.extend(SICI.params)
		params.extend(IOCURVE.params)
			
		states = [
			#Name Length(nBits up to 32) Value ByteLocation(in state vector) BitLocation(0 to 7) CRLF
			#http://bci2000.org/wiki/index.php/Technical_Reference:State_Definition
			#Typically, state values change once per block or once per trial.
			#State values are saved per block.
			
			"Intertrial 1 0 0 0",
			"Inrange 1 0 0 0", #1 for Inrange, 0 for Outrange. This is not a phase state, but actually reflects the signal.
			#"SignalEnterMet 1 0 0 0",
			"SignalCriteriaMetBlocks 16 0 0 0", #in blocks, 16-bit is max 65536
			"ISIExceeded 1 0 0 0",
			"StimulatorIntensity 16 0 0 0", #So it is saved off-line analysis
			"StimulatorReady 1 0 0 0", #Whether or not stimulator is ready to trigger.
			#"Trigger 1 0 0 0",
			"Response 1 0 0 0",
			"Feedback 1 0 0 0",
		]
		states.extend(MEP.states)
		states.extend(SICI.states)
		
		return params,states
		
	#############################################################
	
	def Preflight(self, sigprops):
		#TODO: Warn if ISIMin is less than ITI as determined by phases.

		#Not yet supported
		#if self.params['RangeEnter'].val: raise EndUserError, "RangeEnter not yet supported"
		
		#Setup screen
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
		
		#Check that the amplitude range makes sense.
		amprange=self.params['AmplitudeRange'].val
		if len(amprange)!=2: raise EndUserError, "AmplitudeRange must have 2 values"
		if amprange[0]>amprange[1]: raise EndUserError, "AmplitudeRange must be in increasing order"
		self.amprange=np.asarray(amprange,dtype='float64')
		
		#############
		# ERP CHECK #
		#############
		
		#Trigger
		self.trigchan=None
		#tch = self.params['TriggerInputChan'].val
		tch = self.params['TriggerInputChan']
		if len(tch) != 0:
			if False in [isinstance(x, int) for x in tch]:
				nf = filter(lambda x: not str(x) in chn, tch)
				if len(nf): raise EndUserError, "TriggerChannel %s not in module's list of input channel names" % str(nf)
				self.trigchan = [chn.index(str(x)) for x in tch]
			else:
				nf = [x for x in tch if x < 1 or x > len(chn) or x != round(x)]
				if len(nf): raise EndUserError, "Illegal TriggerChannel: %s" %str(nf)
				self.trigchan = [x-1 for x in tch]
		if self.trigchan:
			trigthresh=self.params['TriggerThreshold'].val
			self.tch=tch #This is used for storing the channel labels.
			self.trigthresh=trigthresh
			
		#Check the ERP channel.
		erpch = self.params['ERPChan'].val
		#erpch = [ec + "_RAW" for ec in erpch]#Append _RAW to each erpchan
		if len(erpch) != 0:
			if False in [isinstance(x, int) for x in erpch]:
				nf = filter(lambda x: not str(x) in chn, erpch)
				if len(nf): raise EndUserError, "ERPChan %s not in module's list of input channel names" % str(nf)
				self.erpchan = [chn.index(str(x)) for x in erpch]
			else:
				nf = [x for x in erpch if x < 1 or x > len(chn) or x != round(x)]
				if len(nf): raise EndUserError, "Illegal ERPChan: %s" % str(nf)
				self.erpchan = [x-1 for x in erpch]
		else:
			raise EndUserError, "Must supply ERPChan"
		
		#Get the list of stored channel ids
		self.stored_chan_ids = self.trigchan + self.erpchan if self.trigchan else self.erpchan
			
		#Check the ERP window.
		erpwin = self.params['ERPWindow'].val
		if len(erpwin)!=2: raise EndUserError, "ERPWindow must have 2 values"
		if erpwin[0]>erpwin[1]: raise EndUserError, "ERPWindow must be in increasing order"
		if erpwin[1]<0: raise EndUserError, "ERPWindow must include up to at least 0 msec after stimulus onset"
		self.erpwin=erpwin
		if self.params['ExperimentType'].val in [1,4]: IOCURVE.preflight(self)
		
	#############################################################
	
	def Initialize(self, indim, outdim):
		#######################################################
		# Get our subject and its current period from the ORM #
		#######################################################
		my_subject_type=get_or_create(Subject_type, Name='BCPy_healthy')
		self.subject=get_or_create(Subject, Name=self.params['SubjectName'], species_type='human')
		if not self.subject.subject_type_id:
			self.subject.subject_type_id=my_subject_type.subject_type_id
		#Determine period_type from ExperimentType 0 MEPMapping, 1 MEPRecruitment, 2 MEPSICI, 3 HRHunting, 4 HRRecruitment
		period_type_name={0:'mep_mapping', 1:'mep_io', 2:'mep_sici', 3:'hr_hunting', 4:'hr_io'}.get(int(self.params['ExperimentType']))
		my_period_type=get_or_create(Datum_type, Name=period_type_name)
		self.period = self.subject.get_most_recent_period(datum_type=my_period_type,delay=0)#Will create period if it does not exist.
		
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
		
		#######################################################
		# (Convert and) Attach contingency parameters to self #
		#######################################################
		self.ISIMin=float(self.params['ISIMin'])
		self.eegfs=self.nominal['SamplesPerSecond'] #Sampling rate
		spb=self.nominal['SamplesPerPacket'] #Samples per block/packet
		self.dmin=int(ceil(self.params['DurationMin'].val * self.eegfs / spb)) #Convert DurationMin to blocks		
		self.drand=int(ceil(self.params['DurationRand'].val * self.eegfs / spb)) #Convert DurationRand to blocks
		self.enterok=False #Init to False
		self.block_dur= 1000*spb/self.eegfs#duration (ms) of a sample block
		
		##################
		# Buffer the ERP #
		##################
		self.post_stim_samples = SigTools.msec2samples(self.erpwin[1], self.eegfs)
		self.pre_stim_samples = SigTools.msec2samples(np.abs(self.erpwin[0]), self.eegfs)
		#Initialize the buffer that contains the full (pre and post) erp.
		#This buffer must contain at least pre_stim_samples + post_stim_samples + 2*spb... but we'll add a few blocks for safety.
		self.leaky_trap=SigTools.Buffering.trap(self.pre_stim_samples + self.post_stim_samples + 5*spb, len(self.stored_chan_ids), leaky=True)
		#We will use a trap buffer that will monitor the trigger. This may only be large enough to store the post-stim erp.
		self.erp_trap = SigTools.Buffering.trap(self.post_stim_samples, len(self.stored_chan_ids),\
											trigger_channel=self.stored_chan_ids.index(self.trigchan[0]), trigger_threshold=self.trigthresh)

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
			#addstatemonitor(self, 'SignalEnterMet')
			addstatemonitor(self, 'SignalCriteriaMetBlocks')
			addstatemonitor(self, 'StimulatorReady')
			addstatemonitor(self, 'ISIExceeded')
			#addstatemonitor(self, 'Trigger')
			addstatemonitor(self, 'Response')
			addstatemonitor(self, 'Feedback')
						
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
		
		#Initialize the stimulator. It depends on the ExperimentType
		#from ExperimentType 0 MEPMapping, 1 MEPRecruitment, 2 MEPSICI, 3 HRHunting, 4 HRRecruitment
		exp_type = int(self.params['ExperimentType'])
		if exp_type in [0,1,2]: MEP.initialize(self)#Stimulator
		elif exp_type in [3,4]: HR.initialize(self)
		if exp_type == 2: SICI.initialize(self)
		if exp_type in [1,4]: IOCURVE.initialize(self)#Detection limit and baseline trials
		elif exp_type == 0: MAPPING.initialize(self)#Subtle differences for controlling stimulator.
		self.stimulator.intensity = self.params['StimIntensity'].val#This might be overwritten in inter-trial (e.g. by IOCURVE)
		
		self.x_vec=np.arange(self.erpwin[0],self.erpwin[1],1000/self.eegfs,dtype=float)
		self.chlbs = self.params['TriggerInputChan'] if self.trigchan else []
		add_names = [ch_name[0:-4] if ch_name.endswith('_RAW') else ch_name for ch_name in self.params['ERPChan']]
		self.chlbs.extend(add_names)
		
	#############################################################
	
	def StartRun(self):
		#Pretend that there was a stimulus at time 0 so that the min ISI check works on the first trial.
		#self.transient("Trigger")
		self.forget('stim_trig')
		#self.trailingsample = None#Used for trigger monitoring
		#self.triggered = False #each new trial has not yet been triggered.
		if int(self.params['ExperimentType']) in [1,4]: IOCURVE.startrun(self)
		
	#############################################################
	
	def Phases(self):
		# define phase machine using calls to self.phase and self.design
		self.phase(name='intertrial', next='outrange', duration=500)#TODO Replace this duration with some parameter
		self.phase(name='outrange', next='inrange', duration=None)
		self.phase(name='inrange', next='response', duration=None)
		self.phase(name='response', next='feedback'\
				, duration=self.params['ERPWindow'].val[1]+(2*self.block_dur)+1)
				#Includes trigger onset. Extra 2 blocks to make sure the response has been captured.
		self.phase(name='feedback', next='intertrial', duration=1000)#TODO Replace this duration with some parameter
		self.design(start='intertrial', new_trial='intertrial')
		#Note that only Process can change phase from outrange, from inrange, and therefore into response
		
	#############################################################
	
	def Transition(self, phase):
		# present stimuli and update state variables to record what is going on
		#Update some states
		self.states['Intertrial'] = int(phase in ['intertrial'])
		#self.states['Trigger'] = int(phase in ['trigger'])
		self.states['Response']  = int(phase in ['response'])
		self.states['Feedback']  = int(phase in ['feedback'])
		#Note: The Inrange state depends on the signal, not on the phase.
		
		if phase == 'response':
			self.stimulator.trigger()
			#self.states['Trigger'] = 1
			self.remember('stim_trig')
			self.states['SignalCriteriaMetBlocks']=0#Reset the number of blocks
			#self.triggered = True #Used to make sure we only process the trigger input when it is relevant to do so.
			self.states['StimulatorIntensity'] = self.stimulator.intensity
		elif phase == 'outrange':
			self.stimuli['target_box'].color = [1, 0, 0]
			#self.states['SignalEnterMet'] = False
		elif phase == 'inrange':
			self.stimuli['target_box'].color = [0, 1, 0]
			#TODO: Check entry direction condition.
			#self.enterok = True
			#self.states['SignalEnterMet'] = self.enterok
		elif phase == 'intertrial':
			self.mindur=self.dmin + randint(-1*self.drand,self.drand)#randomized EMG contingency duration
			#self.triggered = False #each new trial has not yet been triggered.
			
		elif phase == 'feedback':
			#This should begin about 2 blocks after the response window is over.
			#Hopefully Process has detected the trigger and stored the data by now.
			#TODO: If rewarding, reward
			pass
		
		if int(self.params['ExperimentType']) in [0,1,2]: MEP.transition(self,phase)
		if int(self.params['ExperimentType']) == 0: MAPPING.transition(self,phase)
		if int(self.params['ExperimentType'])==2: SICI.transition(self,phase)
		if int(self.params['ExperimentType']) in [1,4]: IOCURVE.transition(self,phase)
					
	#############################################################
	
	def Process(self, sig):
		#Process is called on every packet
		#Phase transitions occur independently of packets
		#Therefore it is not desirable to use phases for application logic in Process
		
		########################################
		# Write the ERP data to our trap.      #
		# Do this every block, no matter what. #
		########################################
		self.leaky_trap.process(sig[self.stored_chan_ids,:])
		self.erp_trap.process(sig[self.stored_chan_ids,:])
		
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
		self.states['SignalCriteriaMetBlocks'] = self.states['SignalCriteriaMetBlocks'] +1 if now_in_range else 0#increment the state tracking for how many blocks we are in range.
		#this state also gets reset to 0 when triggering
		
		################################
		# Update the ISIExceeded state #
		################################
		isiok = self.since('stim_trig')['msec'] >= 1000 * self.ISIMin
		self.states['ISIExceeded'] = isiok #update state
		
		####################################
		# Update the StimulatorReady state #
		####################################
		stim_ready = True if not self.params['ReqStimReady'].val else self.stimulator.ready
		self.states['StimulatorReady'] = stim_ready
		
		##############################################
		# Manually change out of inrange or outrange #
		##############################################
		#try using self.remember and self.since instead of phases.
		phase_inrange=self.in_phase('inrange')
		phase_outrange=self.in_phase('outrange')
		if phase_inrange or phase_outrange:
			if now_in_range:
				if phase_inrange:#phase was correct
					#if self.enterok and isiok and stim_ready and self.stimulator.armed and int(self.states['SignalCriteriaMetBlocks']) >= self.mindur:
					if isiok and stim_ready and int(self.states['SignalCriteriaMetBlocks']) >= self.mindur:
						self.change_phase('response')
				else:#phase was wrong
					self.change_phase('inrange')					
			else:#now not in range
				if ~phase_outrange:#phase is wrong
					self.change_phase('outrange')
		
		#if self.in_phase('response'):self.dbstop()
		if self.erp_trap.full():
			n_excess = (self.erp_trap.nseen-self.erp_trap.sprung_at)-self.erp_trap.nsamples
			self.erp_trap.reset()
			data = self.leaky_trap.read()
			data = data[:,-1*(self.pre_stim_samples+self.post_stim_samples+n_excess):-1*n_excess]
			self.period.trials.append(Datum(subject_id=self.subject.subject_id\
											, datum_type_id=self.period.datum_type_id\
											, span_type='trial'\
											, parent_datum_id=self.period.datum_id\
											, IsGood=1, Number=0))
			my_trial=self.period.trials[-1]
			my_trial.detail_values[self.intensity_detail_name]=str(self.stimulator.intensity)
			if int(self.params['ExperimentType']) == 2:#SICI intensity
				my_trial.detail_values['dat_TMS_powerB']=str(self.stimulator.intensityb)
			#The fature calculation should be asynchronous.
			if isinstance(data,basestring): self.dbstop()
			
			my_trial.store={'x_vec':self.x_vec, 'data':data, 'channel_labels': self.chlbs}
			self.period.EndTime = datetime.datetime.now() + datetime.timedelta(minutes = 5)
				
				#if int(self.params['ShowLastERP'])==1:
					#Pass the plot off to a remote object so it doesn't kill this' rendering.
				#	ch_bool = np.asarray([self.params['ERPChan'][0]==chan_lab for chan_lab in self.chlbs])
				#	self.plot_maker.plot_data(self.x_vec,x[ch_bool,:].T)
				
		##############################
		# Response from ERP analysis #
		##############################
		elif self.in_phase('feedback'):
			pass
			
	#############################################################
	
	def Frame(self, phase):
		# update stimulus parameters if they need to be animated on a frame-by-frame basis
		pass
		
	#############################################################
	
	def Event(self, phase, event):
		if event.type == pygame.locals.KEYDOWN:
			if event.key == pygame.K_UP:
				self.stimulator.intensity = self.stimulator.intensity + 1
				print "stim intensity ++"
			if event.key == pygame.K_DOWN:
				self.stimulator.intensity = self.stimulator.intensity - 1
				print "stim intensity --"
	#############################################################
	
	def StopRun(self):
		pass
	
#################################################################
#################################################################