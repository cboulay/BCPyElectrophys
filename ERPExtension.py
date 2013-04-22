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
from BCPy2000.BCI2000Tools.FileReader import ListDatFiles
import os
import sys
sys.path.append(os.path.abspath('d:/tools/eerf/python/eerf'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eerf.settings")
from AppTools.Shapes import Block
import SigTools

try: from eerfd.models import *
except: pass
class ERPThread(threading.Thread):
    def __init__(self, queue, app):
        threading.Thread.__init__(self)
        self.app = app
        self.queue = queue

    #The app must have setup the subject and period before the thread can be run.
    def run(self):
        while True:
            try:#Get a message from the queue
                msg = self.queue.get(True, 0.5)
            except:#Queue is empty -> Do the default action.
                self.queue.put({'default': 0})
                msg = self.queue.get(True, 0.5)
            finally:#We got a message
                key = msg.keys()[0]
                value = msg[key]
                if key=='save_trial':
                    #===========================================================
                    # value is the erp data for this trial.
                    # Everything else can be extracted from self.app
                    #===========================================================
                    my_trial = Datum.objects.create(subject=self.app.subject,
                                                    span_type='trial'
                                                    )
                    #self.app.period.trials.add(my_trial)

                    #Copy detail values from self.app.period to my_trial (if they exist)
                    #my_trial.copy_details_from(self.app.period)

                    #Add detail values from the experimental conditions.
                    my_trial.update_ddv('Task_condition',str(self.app.states['TargetCode']))
                    if int(self.app.params['DigitimerEnable'])>0:
                        my_trial.update_ddv('Nerve_stim_output',str(self.app.digistim.intensity))
                    if int(self.app.params['MSEnable'])>0:
                        my_trial.update_ddv('TMS_powerA',str(self.app.magstim.intensity))
                        if self.app.magstim.ISI > 0:
                            my_trial.update_ddv('TMS_powerB',str(self.app.magstim.intensityb))
                            my_trial.update_ddv('TMS_ISI',str(self.app.magstim.ISI))

                    #Save the erp data to datumstore.
                    my_store = DatumStore(datum=my_trial,
                                          x_vec=self.app.x_vec,
                                          channel_labels=self.app.params['ERPChan'])
                    #value's dim0 is channels and dim1 is samples.
                    if value.shape[0] != len(self.app.params['ERPChan']):
                        value = value.T
                    my_store.data = value #this will set erp, n_channels and n_samples and save.
                    self.app.states['ERPCollected'] = True
                    #===========================================================
                    # last_trial = self.app.period.trials.order_by('-datum_id').all()[0]
                    # self.app.states['LastTrialNumber'] = int(last_trial.number)
                    #===========================================================
                    # self.app.period.extend_stop_time()

                elif key=='default':
                    if int(self.app.params['ERPFeedbackDisplay'])>0:
                        trial_query = self.app.subject.data.filter(span_type__exact=3).order_by('-datum_id')
                        last_trial = trial_query.all()[0] if trial_query.count()>0 else None
                        if last_trial:
                            feature_name = self.app.params['ERPFeedbackFeature']
                            last_trial.update_ddv('Conditioned_feature_name', feature_name)
                            last_trial.calculate_value_for_feature_name(feature_name) #This may take a while.
                            feature_value = last_trial.feature_values_dict()[feature_name]
                            feature_value = feature_value * self.app.erp_scale
                            self.app.states['LastERPVal'] = np.uint16(feature_value)

                            x = int(np.int16(feature_value))
                            fbthresh = self.app.params['ERPFeedbackThreshold'].val * self.app.erp_scale
                            last_trial.update_ddv('Conditioned_result',
                                                  (fbthresh>0 and x>=fbthresh) or (fbthresh<0 and x<=fbthresh))

                elif key=='shutdown':
                    return

                self.queue.task_done()

class ERPApp(object):
    params = [
            "PythonApp:ERPDatabase    int        ERPDatabaseEnable= 0 0 0 1 // Enable: 0 no, 1 yes (boolean)",
            "PythonApp:ERPDatabase    list       TriggerInputChan= 1 Trig % % % // Name of channel used to monitor trigger / control ERP window",
            #"PythonApp:ERPDatabase    float      TriggerThreshold= 1 1 0 % // Use this threshold to determine ERP time 0",
            "PythonApp:ERPDatabase    floatlist      TriggerThreshold= 1 1 1 0 % // Use this threshold to determine ERP time 0",
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
            #"LastTrialNumber 24 0 0 0",
        ]

    @classmethod
    def preflight(cls, app, sigprops):
        if int(app.params['ERPDatabaseEnable'])==1:
            chn = app.inchannels()
            app.trigchan=None#Trigger
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
            if app.trigchan:#TODO: Check the trigger threshold
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
            if int(app.params['ShowSignalTime']):
                app.addstatemonitor('LastERPVal')
                app.addstatemonitor('ERPCollected')

            #===================================================================
            # Prepare the buffers for saving the data
            # -leaky_trap contains the data to be saved (trap size defined by pre_stim_samples + post_stim_samples + some breathing room
            # -trig_trap contains only the trigger channel
            #===================================================================
            app.x_vec=np.arange(app.erpwin[0],app.erpwin[1],1000.0/app.eegfs,dtype=float)#Needed when saving trials
            app.post_stim_samples = SigTools.msec2samples(app.erpwin[1], app.eegfs)
            app.pre_stim_samples = SigTools.msec2samples(np.abs(app.erpwin[0]), app.eegfs)
            app.leaky_trap=SigTools.Buffering.trap(app.pre_stim_samples + app.post_stim_samples + 5*app.spb, len(app.params['ERPChan']), leaky=True)
            app.trig_trap = SigTools.Buffering.trap(app.post_stim_samples, 1, trigger_channel=0, trigger_threshold=app.trigthresh[0])

            #===================================================================
            # Prepare the models from the database.
            #===================================================================
            app.subject = Subject.objects.get_or_create(name=app.params['SubjectName'])[0]
            #===================================================================
            # app.period = app.subject.get_or_create_recent_period(delay=0)
            # app.subject.periods.update()
            # app.period = app.subject.periods.order_by('-datum_id').all()[0]
            #===================================================================

            #===================================================================
            # Use a thread for database interactions because sometimes they will be slow.
            # (especially when calculating a trial's features)
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
        if int(app.params['ERPDatabaseEnable'])==1:
            app.erp_thread.queue.put({'shutdown':None})#Kill the thread

    @classmethod
    def startrun(cls,app):
        if int(app.params['ERPDatabaseEnable'])==1:
			app.states['ERPCollected'] = False
            #===================================================================
            # Create a string of where this file is stored, what the period number is, and what the previous trial number is.
            #===================================================================
			last_trial_number = app.subject.data.order_by('-datum_id').all()[0].number if app.subject.data.count() >0 else 0
			files = ListDatFiles(app.params['DataDirectory'] + '\\' + app.params['SubjectName'] + app.params['SubjectSession'])
			if len(files)>0:
				fname = files[-1]
				fname = fname.replace(fname[-6:-4], str(int(fname[-6:-4])+1))
			else:
				fname = '%s/%s%s/%sS%sR01.dat' % (
							app.params['DataDirectory'],
							app.params['SubjectName'], app.params['SubjectSession'],
							app.params['SubjectName'], app.params['SubjectSession'])
			log_entry = "%s opened after trial %i" % (fname, last_trial_number)
			SubjectLog.objects.create(subject=app.subject, entry=log_entry)#Store the string in a subject log.

    @classmethod
    def stoprun(cls,app):
        if int(app.params['ERPDatabaseEnable'])==1:
            last_trial_n = app.subject.data.order_by('-datum_id').all()[0].number if app.subject.data.count()>0 else 0
            log_entry = "Run stopped after trial %i" % (last_trial_n)
            SubjectLog.objects.create(subject=app.subject, entry=log_entry)

    @classmethod
    def transition(cls,app,phase):
        if int(app.params['ERPDatabaseEnable'])==1:
            if phase == 'intertrial':
                pass

            elif phase == 'baseline':
                app.states['ERPCollected'] = False

            elif phase == 'gocue':
                app.trig_trap.trigger_threshold = app.trigthresh[app.states['TargetCode']-1] if len(app.trigthresh) >= app.states['TargetCode'] else app.trigthresh[-1]

            elif phase == 'task':
                pass

            elif phase == 'response':
                pass

            elif phase == 'stopcue':
                pass

    @classmethod
    def process(cls,app,sig):
        if int(app.params['ERPDatabaseEnable'])==1:
            #Input signals should have mean=0, variance=1. Most signals will have extremes of -10 and +10
            #Except digital triggers are not processed
            app.leaky_trap.process(sig[app.erpchan,:])
            trig_dat = sig[app.trigchan,:]# if app.in_phase('response') else 0*sig[app.trigchan,:]
            app.trig_trap.process(trig_dat)

            if app.in_phase('response') and app.trig_trap.full():
                n_excess = (app.trig_trap.nseen-app.trig_trap.sprung_at)-app.trig_trap.nsamples
                data = app.leaky_trap.read()
                data = data[:,-1*(app.pre_stim_samples+app.post_stim_samples+n_excess):-1*n_excess]
                app.erp_thread.queue.put({'save_trial':data})
                app.trig_trap.reset()

            if int(app.params['ERPFeedbackDisplay'])==2 and app.changed('LastERPVal'):
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