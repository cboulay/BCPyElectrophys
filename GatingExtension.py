#===============================================================================
# The application will not be able to exit out of the Task phase
# unless the criteria are met.
# Gating criteria are only evaluated during process.
# Expects GatingChannel's signal to be scaled so +1.0 is the top of the screen
#  -e.g., isometric contraction: EMG input between 0 and 1, and 1=MVC
#  -e.g., ERD threshold: channel input has mean 0 and variance=1
#===============================================================================

from math import ceil
from random import randint
import numpy as np
#import random
#import time
from AppTools.Shapes import Block
from AppTools.StateMonitors import addstatemonitor

class GatingApp(object):
    params = [
              #"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
              #See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
            "PythonApp:Gating    int          GatingEnable= 0 0 0 1 // Enable: 0 no, 1 yes (boolean)",
            "PythonApp:Gating    list         GatingChannel= 1 1 % % % // Input channel on which the criteria are evaluated",
            "PythonApp:Gating    float        DurationMin= 2.6 2.6 0 % // Duration s which signal must continuously meet criteria before triggering",
            "PythonApp:Gating    float        DurationRand= 0.3 0.3 0 % // Randomization s around the duration",
            "PythonApp:Gating    int          GatingReset= 1 1 0 1 // Counter resets when exiting range: 0 no, 1 yes (boolean)",
            #"PythonApp:Gating     int         RangeEnter= 0 0 0 2 // Signal must enter range from: 0 either, 1 below, 2 above (enumeration)",

        ]
    states = [
            "InRange 1 0 0 0", #1 for InRange, 0 for Outrange. This is not a phase state, but actually reflects the signal.
            "GatingOK 1 0 0 0", #Boolean if all Gating paramaters are currently satisfied.
            "msecInRange 16 0 0 0", #Number of milliseconds in range, max 65536
        ]

    @classmethod
    def preflight(cls, app, sigprops):
        if int(app.params['GatingEnable'])==1:
            #Not yet supported
            #if app.params['RangeEnter'].val: raise EndUserError, "RangeEnter not yet supported"

            # Make sure GatingChannel is in the list of channels.
            chn = app.inchannels()
            pch = app.params['GatingChannel'].val
            use_process = len(pch) != 0
            if use_process:
                if False in [isinstance(x, int) for x in pch]:
                    nf = filter(lambda x: not str(x) in chn, pch)
                    if len(nf): raise EndUserError, "GatingChannel %s not in module's list of input channel names" % str(nf)
                    app.gatechan = [chn.index(str(x)) for x in pch]
                else:
                    nf = [x for x in pch if x < 1 or x > len(chn) or x != round(x)]
                    if len(nf): raise EndUserError, "Illegal GatingChannel: %s" % str(nf)
                    app.gatechan = [x-1 for x in pch]
            else:
                raise EndUserError, "Must supply GatingChannel"

    @classmethod
    def initialize(cls, app, indim, outdim):
        if int(app.params['GatingEnable'])==1:
            if int(app.params['ShowSignalTime']):
                app.addstatemonitor('InRange')
                app.addstatemonitor('GatingOK')
            if int(app.params['GatingReset'])==0:
                app.addstatemonitor('msecInRange')

    @classmethod
    def halt(cls,app):
        pass

    @classmethod
    def startrun(cls,app):
        if int(app.params['GatingEnable'])==1:
            app.forget('range_ok')
            app.states['msecInRange']=0

    @classmethod
    def stoprun(cls,app):
        if int(app.params['GatingEnable'])==1: pass

    @classmethod
    def transition(cls,app,phase):
        if int(app.params['GatingEnable'])==1:

            if phase == 'intertrial':
                app.mindur = 1000*app.params['DurationMin'].val + randint(int(-1000*app.params['DurationRand'].val),int(1000*app.params['DurationRand'].val))#randomized EMG Gating duration

            elif phase == 'baseline':
                pass

            elif phase == 'gocue':
                pass

            elif phase == 'task':
                app.remember('range_ok')
                app.states['msecInRange'] = 0

            elif phase == 'response':
                pass

            elif phase == 'stopcue':
                pass

    @classmethod
    def process(cls,app,sig):
        if int(app.params['GatingEnable'])==1:
            x = sig[app.gatechan,:].mean(axis=1)#still a matrix
            x=float(x)#single value

            #===================================================================
            # Target ranges are specified in the range -100 to +100
            # EMG signals are expected to range from 0 to 10 (10 = 100 % MVC)
            # ERD signals are expected to range from -10 to +10 (10 = 100% baseline)
            # Standard signals are expected to have mean 0 and unit variance, extremes -10 and +10
            # Thus, multiply our signal by 10 when testing if it is in range
            #===================================================================
            x = x * 10.0
            t = app.states['LastTargetCode'] #Keeps track of the previous trial's targetcode for feedback purposes.
            app.states['InRange'] = (x >= app.target_range[t-1][0]) and (x <= app.target_range[t-1][1])
            if app.changed('InRange', only=1) or not app.states['InRange']:
                app.remember('range_ok') #Resets range_ok unless we were already inrange.
                if int(app.params['GatingReset']): app.states['msecInRange'] = 0 #Resets the timer
            app.states['msecInRange'] = app.states['msecInRange'] + int(app.states['InRange'])*int(app.block_dur)
            rangeok = app.states['msecInRange'] >= app.mindur
            enterok = True #TODO: Check entry direction condition.
            app.states['GatingOK'] = rangeok and enterok

    @classmethod
    def event(cls, app, phasename, event):
        if int(app.params['GatingEnable'])==1: pass