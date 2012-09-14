#===============================================================================
# Passes trigger into a buffer for trigger detection and ERP into another buffer. When a trigger is detected,
# the trial's details and its evoked potential are saved into a MySQL database.
# The application will not be able to exit the response phase until the
# ERP has been collected. Storing of the ERP in the database is asynchronous.
# The app might also show feedback 
#===============================================================================
#===============================================================================
# TODO:
# -Cleanup preflight
# -Cleanup initialize. period_type
# -Process: only trigger goes to one trap. ERPChan go to other trap.
# -Use a thread for database interaction.
#===============================================================================

import Queue
import threading
import numpy as np
#import random
#import time
#from EERF.API import *
#from EERF.APIextension.online import *
from AppTools.Shapes import Block
import SigTools

class ERPThread(threading.Thread):
    def __init__(self, queue, app):
        threading.Thread.__init__(self)
        self.app = app
        self.queue = queue
        
    def run(self):
        while True:
            try:#Get a message from the queue
                msg = self.queue.get(True, 0.8)
            except:#Queue is empty -> Do the default action.
                self.queue.put({'default': 0})
            else:#We got a message
                key = msg.keys()[0]
                value = msg[key]
                if key=='save_trial':
                    #===========================================================
                    # value is the erp data for this trial.
                    # Everything else can be extracted from app
                    #===========================================================
                    #self.app.period.trials.append(
                    my_trial = get_or_create(Datum, subject_id=self.app.subject.subject_id\
                                    , span_type='trial'\
                                    , IsGood=1, Number=0, sess=Session.object_session(self.app.period))
                    my_trial.periods = [self.app.period]
                    #Populate a dict of detail_values
                    #Copy relevant detail values from parent period.
                    per_details = self.app.period.detail_values
                    if int(self.app.params['ERPFeedbackDisplay']):
                        if 'BG_start_ms' in per_details:
                            my_trial.detail_values['BG_start_ms'] = per_details['BG_start_ms']
                        if 'BG_stop_ms' in per_details:
                            my_trial.detail_values['BG_stop_ms'] = per_details['BG_stop_ms']
                        if 'MEP' in self.app.params['ERPFeedbackFeature']:
                            if 'MEP_start_ms' in per_details:
                                my_trial.detail_values['MEP_start_ms'] = per_details['MEP_start_ms']
                            if 'MEP_stop_ms' in per_details:
                                my_trial.detail_values['MEP_stop_ms'] = per_details['MEP_stop_ms']
                        elif 'HR' in self.app.params['ERPFeedbackFeature']:
                            if 'MR_start_ms' in per_details:
                                my_trial.detail_values['MR_start_ms'] = per_details['MR_start_ms']
                            if 'MR_stop_ms' in per_details:
                                my_trial.detail_values['MR_stop_ms'] = per_details['MR_stop_ms']
                            if 'HR_start_ms' in per_details:
                                my_trial.detail_values['HR_start_ms'] = per_details['HR_start_ms']
                            if 'HR_stop_ms' in per_details:
                                my_trial.detail_values['HR_stop_ms'] = per_details['HR_stop_ms']
                    
                    #Add detail values from the experimental conditions.
                    my_trial.detail_values['Task_condition'] = str(self.app.states['TargetCode'])
                    my_trial.detail_values['Task_condition'] = str(self.app.states['TargetCode'])
                    if int(self.app.params['DigitimerEnable'])>0:
                        my_trial.detail_values['Nerve_stim_output'] = str(self.app.digistim.intensity)
                    if int(self.app.params['MSEnable'])>0:
                        my_trial.detail_values['TMS_powerA'] = str(self.app.magstim.intensity)
                        if self.app.magstim.ISI > 0:
                            my_trial.detail_values['TMS_powerB'] = str(self.app.magstim.intensityb)
                            my_trial.detail_values['TMS_ISI'] = str(self.app.magstim.ISI)
                    
                    my_trial.store={'x_vec':self.app.x_vec, 'data':value, 'channel_labels': self.app.params['ERPChan']}
                    
                    self.app.period.EndTime = datetime.datetime.now() + datetime.timedelta(minutes = 5)
                    Session.object_session(self.app.period).commit()
                    print 'committing'
                    
                elif key=='default':
                    #===========================================================
                    # TODO: Check the database for the last trial. If it is new, then
                    # retrieve the desired ERP value (ERPFeedbackOf) and then 
                    # change the value of self.app.states['LastERPx100']
                    # Also set last_trial.detail_values['dat_conditioned_result']
                    #===========================================================
                    if int(self.app.params['ERPFeedbackDisplay'])>0:
                        last_trial = self.app.period.trials[-1] if self.app.period.trials.count()>0 else None
                        if last_trial:
                            feature_name = self.app.params['ERPFeedbackFeature']
                            last_trial.detail_values['Conditioned_feature_name'] = feature_name
                            last_trial.calculate_value_for_feature_name(feature_name)
                            feature_value = last_trial.feature_values[feature_name]
                            feature_value = feature_value * self.app.erp_scale
                            self.app.states['LastERPVal'] = np.uint16(feature_value)
                            
                            x = int(np.int16(feature_value))
                            fbthresh = self.app.params['ERPFeedbackThreshold'].val * self.app.erp_scale
                            last_trial.detail_values['Conditioned_result'] = (fbthresh>0 and x>=fbthresh) or (fbthresh<0 and x<=fbthresh)
                    
                elif key=='shutdown': return
                self.queue.task_done()#signals to queue job is done. Maybe the stimulator object should do this?

class ERPApp(object):
    params = [
            "PythonApp:ERPDatabase    int        ERPDatabaseEnable= 1 1 0 1 // Enable: 0 no, 1 yes (boolean)",
            "PythonApp:ERPDatabase    list       TriggerInputChan= 1 Trig % % % // Name of channel used to monitor trigger / control ERP window",
            "PythonApp:ERPDatabase    float      TriggerThreshold= 1 1 0 % // Use this threshold to determine ERP time 0",
            #"PythonApp:ERPDatabase   int            UseSoftwareTrigger= 0 0 0 1  // Use phase change to determine trigger onset (boolean)",
            "PythonApp:ERPDatabase    list       ERPChan= 1 EDC % % % // Channels to store in database",
            "PythonApp:ERPDatabase    floatlist  ERPWindow= {Start Stop} -500 500 0 % % // Stored window, relative to trigger onset, in millesconds",
            "PythonApp:ERPDatabase    int        ERPFeedbackDisplay= 0 0 0 2 // Feedback as: 0 None, 1 TwoColour, 2 Continuous (enumeration)",
            "PythonApp:ERPDatabase    string     ERPFeedbackFeature= MEP_p2p % % % // Name of feature for feedback",
            "PythonApp:ERPDatabase    float      ERPFeedbackThreshold= 3.0 0 % % // Threshold for correct erp feedback",
        ]
    states = [
            "LastERPVal 16 0 0 0", #Last ERP's feature value
            "ERPCollected 1 0 0 0", #Whether or not the ERP was collected this trial.
        ]
    
    @classmethod
    def preflight(cls, app, sigprops):
        if int(app.params['ERPDatabaseEnable'])==1:
            chn = app.inchannels()
            #Trigger
            app.trigchan=None
            tch = app.params['TriggerInputChan']
            if len(tch) != 0:
                if False in [isinstance(x, int) for x in tch]:
                    nf = filter(lambda x: not str(x) in chn, tch)
                    if len(nf): raise EndUserError, "TriggerChannel %s not in module's list of input channel names" % str(nf)
                    app.trigchan = [chn.index(str(x)) for x in tch]
                else:
                    nf = [x for x in tch if x < 1 or x > len(chn) or x != round(x)]
                    if len(nf): raise EndUserError, "Illegal TriggerChannel: %s" %str(nf)
                    app.trigchan = [x-1 for x in tch]
            #TODO: Check the trigger threshold
            if app.trigchan:
                trigthresh=app.params['TriggerThreshold'].val
                app.trig_label=tch #This is the channel label.
                app.trigthresh=trigthresh
                
            #ERP channel(s)
            erpch = app.params['ERPChan'].val
            if len(erpch) != 0:
                if False in [isinstance(x, int) for x in erpch]:
                    nf = filter(lambda x: not str(x) in chn, erpch)
                    if len(nf): raise EndUserError, "ERPChan %s not in module's list of input channel names" % str(nf)
                    app.erpchan = [chn.index(str(x)) for x in erpch]
                else:
                    nf = [x for x in erpch if x < 1 or x > len(chn) or x != round(x)]
                    if len(nf): raise EndUserError, "Illegal ERPChan: %s" % str(nf)
                    app.erpchan = [x-1 for x in erpch]
            else:
                raise EndUserError, "Must supply ERPChan"
                
            #ERP window
            erpwin = app.params['ERPWindow'].val
            if len(erpwin)!=2: raise EndUserError, "ERPWindow must have 2 values"
            if erpwin[0]>erpwin[1]: raise EndUserError, "ERPWindow must be in increasing order"
            if erpwin[1]<0: raise EndUserError, "ERPWindow must include up to at least 0 msec after stimulus onset"
            app.erpwin=erpwin
    
    @classmethod
    def initialize(cls, app, indim, outdim):
        if int(app.params['ERPDatabaseEnable'])==1:
            # Get our subject from the DB API.
            app.subject=get_or_create(Subject, Name=app.params['SubjectName'])
                
            # Get our period from the DB API.
            app.period = app.subject.get_most_recent_period(delay=0)#Will create period if it does not exist.
            
            #===================================================================
            # Prepare the buffers for saving the data
            # -leaky_trap contains the data to be saved (trap size defined by pre_stim_samples + post_stim_samples + some breathing room
            # -trig_trap contains only the trigger channel
            #===================================================================
            app.x_vec=np.arange(app.erpwin[0],app.erpwin[1],1000/app.eegfs,dtype=float)#Needed when saving trials
            app.post_stim_samples = SigTools.msec2samples(app.erpwin[1], app.eegfs)
            app.pre_stim_samples = SigTools.msec2samples(np.abs(app.erpwin[0]), app.eegfs)
            app.leaky_trap=SigTools.Buffering.trap(app.pre_stim_samples + app.post_stim_samples + 5*app.spb, len(app.params['ERPChan']), leaky=True)
            app.trig_trap = SigTools.Buffering.trap(app.post_stim_samples, 1, trigger_channel=0, trigger_threshold=app.trigthresh)
            
            #===================================================================
            # Use a thread for database interactions because sometimes they will be slow.
            # (saving a trial also calculates all of that trial's features)
            #===================================================================
            app.erp_thread = ERPThread(Queue.Queue(), app)
            app.erp_thread.setDaemon(True) #Dunno, always there in the thread examples.
            app.erp_thread.start() #Starts the thread.
            
            #===================================================================
            # Setup the ERP feedback elements.
            # -Screen will range from -2*fbthresh to +2*fbthresh
            # -Calculated ERP value will be scaled so 65536(int16) fills the screen. 
            #===================================================================
            if int(app.params['ERPFeedbackDisplay'])==2:
                fbthresh = app.params['ERPFeedbackThreshold'].val
                app.erp_scale = (2.0**16) / (4.0*np.abs(fbthresh))
                if fbthresh < 0:
                    fbmax = fbthresh * app.erp_scale
                    fbmin = 2.0 * fbthresh * app.erp_scale
                else:
                    fbmax = 2.0 * fbthresh * app.erp_scale
                    fbmin = fbthresh * app.erp_scale
                m=app.scrh/float(2**16)#Conversion factor from signal amplitude to pixels.
                b_offset=app.scrh/2.0 #Input 0.0 should be at this pixel value.
                app.addbar(color=(1,0,0), pos=(0.9*app.scrw,b_offset), thickness=0.1*app.scrw, fac=m)
                n_bars = len(app.bars)
                #app.stimuli['bartext_1'].position=(50,50)
                app.stimuli['bartext_' + str(n_bars)].color=[0,0,0]
                erp_target_box = Block(position=(0.8*app.scrw,m*fbmin+b_offset), size=(0.2*app.scrw,m*(fbmax-fbmin)), color=(1,0,0,0.5), anchor='lowerleft')
                app.stimulus('erp_target_box', z=1, stim=erp_target_box)
        
    @classmethod
    def halt(cls,app):
        app.erp_thread.queue.put({'shutdown':None})#Kill the thread
    
    @classmethod
    def startrun(cls,app):
        if int(app.params['ERPDatabaseEnable'])==1:
            app.states['ERPCollected'] = False
        
    @classmethod
    def stoprun(cls,app):
        if int(app.params['ERPDatabaseEnable'])==1:
            Session.object_session(app.period).flush()
    
    @classmethod
    def transition(cls,app,phase):
        if int(app.params['ERPDatabaseEnable'])==1:
            if phase == 'intertrial':
                pass
                
            elif phase == 'baseline':
                pass
            
            elif phase == 'gocue':
                pass
                
            elif phase == 'task':
                pass
                
            elif phase == 'response':
                pass
            
            elif phase == 'stopcue':
                app.states['ERPCollected'] = False
    
    @classmethod
    def process(cls,app,sig):
        if int(app.params['ERPDatabaseEnable'])==1:
            app.trig_trap.process(sig[app.trigchan,:])
            app.leaky_trap.process(sig[app.erpchan,:])
                        
            if app.in_phase('response') and app.trig_trap.full():
                n_excess = (app.trig_trap.nseen-app.trig_trap.sprung_at)-app.trig_trap.nsamples
                data = app.leaky_trap.read()
                data = data[:,-1*(app.pre_stim_samples+app.post_stim_samples+n_excess):-1*n_excess]
                app.erp_thread.queue.put({'save_trial':data})
                app.states['ERPCollected'] = True
                app.trig_trap.reset()
                
            if app.changed('LastERPVal'):
                if int(app.params['ERPFeedbackDisplay'])==2:
                    x = int(np.int16(app.states['LastERPVal']))
                    app.updatebars(x,barlist=[app.bars[-1]])
                    fbthresh = app.params['ERPFeedbackThreshold'].val * app.erp_scale
                    erp_inrange = (fbthresh>0 and x>=fbthresh) or (fbthresh<0 and x<=fbthresh)
                    app.stimuli['erp_target_box'].color = [1-erp_inrange, erp_inrange, 0]
                    n_bars = len(app.bars)
                    app.stimuli['barrect_' + str(n_bars)].color = [1-erp_inrange, erp_inrange, 0]
    @classmethod
    def event(cls, app, phasename, event):
        if int(app.params['ERPDatabaseEnable'])==1: pass