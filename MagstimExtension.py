#===============================================================================
# Sets the stimulus parameters during the intertrial phase.
# Application cannot advance to response from task if MSReqStimReady and it isn't ready.
# Triggers the stimulus as soon as the response phase is entered.
#===============================================================================

import numpy as np
import random
import time
import pygame, pygame.locals
from AppTools.StateMonitors import addstatemonitor

class MagstimApp(object):
    params = [
            "PythonApp:Magstim        int        MSEnable= 0 0 0 1 // Enable: 0 no, 1 yes (boolean)",
            "PythonApp:Magstim        string    MSSerialPort= COM4 % % % // Serial port for controlling Magstim",
            "PythonApp:Magstim        int        MSTriggerType= 0 0 0 2 // Trigger by: 0 SerialPort, 1 Contec1, 2 Contec2 (enumeration)",
            "PythonApp:Magstim        int        MSReqStimReady= 0 0 0 1 // Require ready response to trigger: 0 no, 1 yes (boolean)",
            "PythonApp:Magstim        float      MSISIMin= 6 6 2 % // Minimum time s between stimuli",
            "PythonApp:Magstim        intlist    MSIntensityA= 1 50 0 0 100 // TS if single-pulse, CS if double-pulse",
            "PythonApp:Magstim        intlist    MSIntensityB= 1 0 0 0 100 // TS if double-pulse",
            "PythonApp:Magstim        floatlist    MSPulseInterval= 1 0 0 0 999 // Double-pulse interval in ms",
        ]
    states = [
            "MagstimReady 1 0 0 0", #Whether or not the magstim returns ready
            "MSIntensityA 16 0 0 0", #Intensity of StimA
            "MSIntensityB 16 0 0 0", #Intensity of StimA
            "ISIx10 16 0 0 0", #Double-pulse ISI in 0.1ms
        ]

    @classmethod
    def preflight(cls, app, sigprops):
        if int(app.params['MSEnable'])==1:
            app.magstimA = app.params['MSIntensityA'].val if len(app.params['MSIntensityA']) == app.nclasses else [app.params['MSIntensityA'].val[0] for x in range(app.nclasses)]
            app.magstimB = app.params['MSIntensityB'].val if len(app.params['MSIntensityB']) == app.nclasses else [app.params['MSIntensityB'].val[0] for x in range(app.nclasses)]
            app.magstimISI = app.params['MSPulseInterval'].val if len(app.params['MSPulseInterval']) == app.nclasses else [app.params['MSPulseInterval'].val[0] for x in range(app.nclasses)]

    @classmethod
    def initialize(cls, app, indim, outdim):
        if int(app.params['MSEnable'])==1:
            from Magstim.MagstimInterface import Bistim
            serPort=app.params['MSSerialPort'].val
            trigType=int(app.params['MSTriggerType'])
            if trigType==0: app.trigbox=None
            else:
                if hasattr(app,'trigbox') and app.trigbox: app.trigbox.set_TTL(channel=trigType, amplitude=5, width=2.5, offset=0.0)
                else:
                    from Caio.TriggerBox import TTL
                    app.trigbox=TTL(channel=trigType)
            app.magstim=Bistim(port=serPort, trigbox=app.trigbox)
            #app.intensity_detail_name = 'dat_TMS_powerA'
            app.magstim.remocon = True

            app.magstim.intensity = app.magstimA[0]
            app.magstim.intensityb = app.magstimB[0]
            app.magstim.ISI = app.magstimISI[0]
            #app.magstim.armed = True
            app.magstim.remocon = False

            if int(app.params['ShowSignalTime']):
                app.addstatemonitor('MagstimReady')
                app.addstatemonitor('MSIntensityA')
                app.addstatemonitor('MSIntensityB')
                app.addstatemonitor('ISIx10')

    @classmethod
    def halt(cls,app):
        if int(app.params['MSEnable'])==1:
            #Clear magstim from memory, which will also clear the serial port.
            app.magstim.__del__()

    @classmethod
    def startrun(cls,app):
        if int(app.params['MSEnable'])==1:
            app.forget('tms_trig')#Pretend that there was a stimulus at time 0 so that the min ISI check works on the first trial.

    @classmethod
    def stoprun(cls,app):
        if int(app.params['MSEnable'])==1: pass

    @classmethod
    def transition(cls,app,phase):
        if int(app.params['MSEnable'])==1:
            if phase == 'intertrial':
                app.magstim.remocon = False

            elif phase == 'baseline':
                pass

            elif phase == 'gocue': #New TargetCode is set in the application transition to gocue
                #I hope this is enough time to set a new intensity. It should be if we are already armed.
                app.magstim.remocon = True
                app.magstim.intensity = app.magstimA[app.states['TargetCode']-1] if app.magstim.intensity in app.magstimA else app.magstim.intensity
                app.magstim.intensityb = app.magstimB[app.states['TargetCode']-1] if app.magstim.intensityb in app.magstimB else app.magstim.intensityb
                app.magstim.ISI = app.magstimISI[app.states['TargetCode']-1] if app.magstim.ISI in app.magstimISI else app.magstim.ISI
                app.magstim.remocon = False

            elif phase == 'task':
                pass

            elif phase == 'response':
                app.magstim.remocon = True
                #app.magstim.armed = True
                app.magstim.trigger()
                app.states['MSIntensityA'] = app.magstim.intensity
                app.states['MSIntensityB'] = app.magstim.intensityb
                app.states['ISIx10'] = app.magstim.ISI
                app.remember('tms_trig')
                app.magstim.armed = False

            elif phase == 'stopcue':
                pass

    @classmethod
    def process(cls,app,sig):
        if int(app.params['MSEnable'])==1:

            #Arm the coil if it is not armed and should be.
            if not app.magstim.armed and not (app.in_phase('response') or app.in_phase('stopcue')):
                #We avoid arming in response or stopcue so the arming artifact doesn't affect the ERP.
                if not app.magstim.remocon: app.magstim.remocon = True
                app.magstim.armed = True
                app.magstim.remocon = False#Toggle remocon so that we can manually adjust the intensity.

            ####################################
            # Update the StimulatorReady state #
            ####################################
            stim_ready = app.magstim.armed if not app.params['MSReqStimReady'].val else (app.magstim.ready and app.magstim.armed)
            #stim_ready = True #Use this for debugging
            isiok = app.since('tms_trig')['msec'] >= 1000.0 * float(app.params['MSISIMin'])
            app.states['MagstimReady'] = stim_ready and isiok

    @classmethod
    def event(cls, app, phasename, event):
        if int(app.params['MSEnable'])==1 and event.type == pygame.locals.KEYDOWN and event.key in [pygame.K_UP, pygame.K_DOWN]:
            #This has a pretty poor success rate. I wonder if it has to do with toggling the remocon state.
            if not app.magstim.remocon: app.magstim.remocon = True
            if event.key == pygame.K_UP: app.magstim.intensity = app.magstim.intensity + 1
            if event.key == pygame.K_DOWN: app.magstim.intensity = app.magstim.intensity - 1
            app.magstim.remocon = False
            print ("magstim intensity " + str(app.magstim.intensity))