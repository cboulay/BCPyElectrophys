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
from random import randint, uniform, random, shuffle
from math import ceil
import time
import BCPyOgreRenderer.OgreRenderer as OgreRenderer
import SigTools
from AppTools.Boxes import box
from AppTools.Displays import fullscreen
from AppTools.StateMonitors import addstatemonitor, addphasemonitor
from AppTools.Shapes import Disc
from GatingExtension import GatingApp

class BciApplication(BciGenericApplication):

    def Description(self):
        return "Template application"

    #############################################################
    def Construct(self):
        #See here for already defined params and states http://bci2000.org/wiki/index.php/Contributions:BCPy2000#CurrentBlock
        #See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
        params = [
            "PythonApp:Design	list	GoCueText=		 	2 Imagery Rest % % % // Text for cues. Defines N targets",
            "PythonApp:Design	int		ClusterTargets=    	1     1     0   %  // Size of pseudorandomized target clusters or cycle(0)",
            "PythonApp:Design	matrix  TargetRange= {1 2} {Min Max} -100.0 -80.0 80.0 100.0 0 -100 100 //Row for each target, Cols for Min(-100), Max(+100)",
            "PythonApp:Design  float    PreRunDuration=     5.0   5.0   0.0 100.0 // PreRunDelay before the task starts",
            "PythonApp:Design  float	IntertrialDur=	  	0.5   0.5   0.0 100.0 // Intertrial duration in seconds",
            "PythonApp:Design  float	BaselineDur=		4.0   4.0   0.0 100.0 // Baseline duration in seconds",
            "PythonApp:Design   float	GoCueDur=	  		1.0   1.0   0.0 100.0 // GoCue duration in seconds",
            "PythonApp:Design  float	TaskDur=			6.0   6.0   0.0 100.0 // Min task duration in seconds (unless Gating)",
            "PythonApp:Design  float	TaskRand=			3.0   3.0   0.0 100.0 // Additional randomization in seconds (unless Gating)",
            "PythonApp:Design  float	TaskMax=			5.0   5.0   0.0 100.0 // Timeout task (s) if Gating fails",
            "PythonApp:Design   float	ResponseDur=	  	0.2   0.2   0.0 100.0 // Response duration in seconds (unless ERP)",
            "PythonApp:Design   float	StopCueDur=	  		1.0   1.0   0.0 100.0 // StopCue duration in seconds",
            "PythonApp:Display  int		ScreenId=		   -1	-1	 %   %  // on which screen should the stimulus window be opened - use -1 for last",
            "PythonApp:Display  float	WindowSize=		 	0.8   1.0   0.0 1.0 // size of the stimulus window, proportional to the screen",
            ]
        states = [
            #===================================================================
            # "Intertrial 1 0 0 0",
            "Baseline 1 0 0 0",
            "GoCue 1 0 0 0",
            "Task 1 0 0 0",
            # "Response 1 0 0 0",
            # "StopCue 1 0 0 0",
            "TargetCode 4 0 0 0", #Set to target int in gocue and 0 in stopcue
            "LastTargetCode 4 0 0 0", #Set to target int in gocue, not turned off. Needed for baseline feedback and inrange.
            "TaskNBlocks 12 0 0 0",
            #"TrialPhase 4 0 0 0",#TrialPhase unnecessary. Use built-in PresentationPhase
            #===================================================================
        ]
        params.extend(GatingApp.params)
        states.extend(GatingApp.states)
        return params,states

    #############################################################
    def Preflight(self, sigprops):
        #Setup screen
        siz = float(self.params['WindowSize'])
        screenid = int(self.params['ScreenId'])  # ScreenId 0 is the first screen, 1 the second, -1 the last
        fullscreen(scale=siz, id=screenid, frameless_window=(siz==1)) # only use a borderless window if the window is set to fill the whole screen

        self.nclasses = len(self.params['GoCueText'])#Must be defined in Preflight because it is used by extension preflight.

        n_trials = self.params['TrialsPerBlock'].val * self.params['BlocksPerRun'].val
        trials_per_class = int(n_trials / self.nclasses)
        if self.params['ClusterTargets'].val>0 and not (trials_per_class % self.params['ClusterTargets'].val == 0):
            raise EndUserError, "ClusterTargets must be a integer factor of the number of trials per target"

        #If using gating or visual feedback, check that the target ranges make sense.
        if ('GatingEnable' in self.params and int(self.params['GatingEnable'].val) or ('ContFeedbackEnable' in self.params and self.params['ContFeedbackEnable'].val)==1):
            targrange=self.params['TargetRange'].val
            if targrange.shape[0] != self.nclasses: raise EndUserError, "TargetRange must have entries for each target"
            if targrange.shape[1]!=2: raise EndUserError, "TargetRange must have Min and Max values"
            if any([ar[(0,0)] > ar[(0,1)] for ar in targrange]): raise EndUserError, "TargetRange must be in increasing order"
            self.target_range=np.asarray(targrange,dtype='float64')

        if 'GatingEnable' in self.params:	GatingApp.preflight(self, sigprops)


    #############################################################
    def Initialize(self, indim, outdim):

        #=======================================================================
        # Set the list of targetCodes (pseudorandomized)
        #=======================================================================
        n_trials = self.params['TrialsPerBlock'].val * self.params['BlocksPerRun'].val
        classes_per_cluster = self.params['ClusterTargets'].val
        trials_per_class = int(n_trials / self.nclasses)
        if classes_per_cluster == 0: #We will cycle through targets.
            self.target_codes = [item for sublist in [range(self.nclasses) for j in range(trials_per_class)] for item in sublist]
            self.target_codes = [x+1 for x in self.target_codes]
        elif classes_per_cluster ==1:
            self.target_codes = [1 + x / trials_per_class for x in range(n_trials)] #Forcing int yields e.g., [0,0,0,1,1,1,2,2,2]
            shuffle(self.target_codes)
        else:
            n_clusters = trials_per_class / classes_per_cluster
            temp = []
            for cc in range(n_clusters):
                temp2 = [[j for jj in range(classes_per_cluster)] for j in range(self.nclasses)] #Generate a list of clusters, one per target
                shuffle(temp2) #Shuffle the list of clusters
                temp.append(temp2) #Append the list of clusters to what we have already.
            self.target_codes = 1 + [x2 for x3 in [item for sublist in temp for item in sublist] for x2 in x3] #Flatten

        #=======================================================================
        # Screen
        #=======================================================================
        self.screen.color = (0,0,0) #let's have a black background
        self.scrw,self.scrh = self.screen.size #Get the screen dimensions.

        #=======================================================================
        # Make a few variables easier to access.
        #=======================================================================
        self.eegfs = self.nominal['SamplesPerSecond'] #Sampling rate
        self.spb = self.nominal['SamplesPerPacket'] #Samples per block/packet
        self.block_dur = 1000*self.spb/self.eegfs#duration (ms) of a sample block
        self.task_timeout_blocks = self.params['TaskMax'].val*1000/self.block_dur
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

        #=======================================================================
        # Create the hand
        #=======================================================================
        HandStimulus = OgreRenderer.HandStimulus
        self.stimulus('hand', HandStimulus, position=(400,300))
        self.hand = self.stimuli['hand'].obj
        self.hand.on = True
        #We want the hand to go from 0 to open in the time it takes to pass through the response phase.
        resp_dur = self.params['ResponseDur'].val
        self.hand_speed = 100./(resp_dur*1000/self.block_dur) #100 positions in the response period
        self.hand_switch = False

        #=======================================================================
        # State monitors for debugging.
        #=======================================================================
        if int(self.params['ShowSignalTime']):# turn on state monitors if the packet clock is also turned on
            addstatemonitor(self, 'Running', showtime=True)
            addstatemonitor(self, 'CurrentBlock')
            addstatemonitor(self, 'CurrentTrial')
            addstatemonitor(self, 'TargetCode')
            addstatemonitor(self, 'LastTargetCode')
            addstatemonitor(self, 'TaskNBlocks')
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

        if 'GatingEnable' in self.params:	GatingApp.initialize(self, indim, outdim)

    #############################################################
    def Halt(self):
        if 'GatingEnable' in self.params:	GatingApp.halt(self)

    #############################################################
    def StartRun(self):
        #if int(self.params['ShowFixation']):
        self.states['LastTargetCode'] = self.target_codes[0]
        self.stimuli['fixation'].on = True
        if 'GatingEnable' in self.params:	GatingApp.startrun(self)

    #############################################################
    def StopRun(self):
        if 'GatingEnable' in self.params:	GatingApp.stoprun(self)

    #############################################################
    def Phases(self):
        # define phase machine using calls to self.phase and self.design
        self.phase(name='preRun', next='intertrial', duration=self.params['PreRunDuration'].val*1000.0)
        self.phase(name='intertrial', next='baseline', duration=self.params['IntertrialDur'].val*1000.0)
        self.phase(name='baseline', next='gocue', duration=self.params['BaselineDur'].val*1000.0)
        self.phase(name='gocue', next='task', duration=self.params['GoCueDur'].val*1000.0)
        self.phase(name='task', next='response',duration=None)
        self.phase(name='response', next='stopcue', duration=self.params['ResponseDur'].val*1000.0)
        self.phase(name='stopcue', next='intertrial', duration=self.params['StopCueDur'].val*1000.0)
        self.phase(name='postRun', duration=1000.0)

        self.design(start='preRun', new_trial='intertrial', end='postRun')

    #############################################################
    def Transition(self, phase):
        # present stimuli and update state variables to record what is going on
        #=======================================================================
        # #Update some states
        # self.states['Intertrial'] = int(phase in ['intertrial'])
        self.states['Baseline'] = int(phase in ['baseline'])
        self.states['GoCue'] = int(phase in ['gocue'])
        self.states['Task'] = int(phase in ['task'])
        # self.states['Response']  = int(phase in ['response'])
        # self.states['StopCue']  = int(phase in ['stopcue'])
        #=======================================================================

        if phase == 'intertrial':
            pass

        elif phase == 'baseline':
            pass
        #Do I need the new TargetCode in baseline for any of the addons?
        #If not, then it belongs in gocue for consistency with regular BCI2000 modules.

        elif phase == 'gocue':
            self.states['TargetCode'] = self.target_codes[self.states['CurrentTrial']-1]
            t = self.states['TargetCode'] #It's useful to pull from states in case "enslave states" is used.
            self.states['LastTargetCode'] = t#LastTargetCode maintains throughout baseline.
            self.stimuli['cue'].text = self.params['GoCueText'][t-1]

        elif phase == 'task':
            app.remember('task_start')
            
        elif phase == 'response':
            self.hand_switch = True

        elif phase == 'stopcue':
            self.hand_switch = False
            self.hand.setPose(0)
            self.stimuli['cue'].text = "Relax"
            self.states['TargetCode'] = 0 #Note we don't turn off the LastTargetCode

        self.stimuli['cue'].on = (phase in ['gocue', 'stopcue'])

        if 'GatingEnable' in self.params:	GatingApp.transition(self, phase)

    #############################################################
    def Process(self, sig):
        #Process is called on every packet
        #Phase transitions occur independently of packets
        #Therefore it is not desirable to use phases for application logic in Process
        GatingApp.process(self, sig)
        if self.states['GatingOK']: self.change_phase('response')
        if self.in_phase('task', min_packets=self.task_timeout_blocks): self.change_phase('stopcue')
        if self.hand_switch:
            self.hand.setPose(ceil(self.hand.getPose() + self.hand_speed))

    #############################################################
    def Frame(self, phase):
        # update stimulus parameters if they need to be animated on a frame-by-frame basis
        pass

    #############################################################
    def Event(self, phase, event):
        if 'GatingEnable' in self.params:	GatingApp.event(self, phase, event)

#################################################################
#################################################################