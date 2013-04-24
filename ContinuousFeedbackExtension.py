import numpy as np
import random
from AppTools.StateMonitors import addstatemonitor
from AppTools.Boxes import box
#from AppTools.Shapes import PolygonTexture, Disc, Block
from BCPyOgreRenderer.OgreRenderer import HandStimulus, Disc, Block, Text
import WavTools

class FeedbackApp(object):
    params = [
              #"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
              #See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
            "Feedback:Design    int          ContFeedbackEnable=  0 0 0 1 // Enable. Choose feedback below.: 0 no, 1 yes (boolean)",
            "Feedback:Design    list         FeedbackChannels=    1 1 % % % // Channel(s) for feedback",
            #Sometimes we want to save some data (via ERPExtension) that is not fed back,
            #so the signal processing module will pass in more data than we need for feedback. Thus we need to select FeedbackChannels.
            "Feedback:Design    int          BaselineFeedback=    0 % % % // Should feedback be provided outside task? (boolean)",
            "Feedback:Design    int          BaselineConstant=    0 % % % // Should non-task feedback be constant? (boolean)",
            "Feedback:Design    int          FakeFeedback=        0 % % % // Make feedback contingent on an external file (boolean)",
            "Feedback:Design    string       FakeFile=            % % % % // Path to fake feedback csv file (inputfile)",
            "Feedback:Visual    int          VisualFeedback=      0 0 0 1 // Show online feedback? (boolean)",
            "Feedback:Visual    intlist      VisualType=          1 0 0 0 2 // Feedback type: 0 bar, 1 cursor, 2 color_change, 3 none",
            "Feedback:Audio     int          AudioFeedback=       0 0 0 1 // Play continuous sounds? (boolean)",
            "Feedback:Audio     matrix       AudioWavs=           2 1 300hz.wav 900hz.wav % % % // feedback wavs",
            "Feedback:Handbox   int          HandboxFeedback=     0 0 0 1 // Move handbox? (boolean)",
            "Feedback:Handbox   string       HandboxPort=         COM7 % % % // Serial port for controlling Handbox",
            "Feedback:NMES      int          NMESFeedback=        0 % 0 1 // Enable neuromuscular stim feedback? (boolean)",
            "Feedback:NMES      floatlist    NMESRange=           {Mid Max} 7 15 0 0 % //Midpoint and Max stim intensities",
            "Feedback:NMES      string       NMESPort=            COM10 % % % // Serial port for controlling NMES",
        ]
    states = [
              #Name Length(nBits up to 32) Value ByteLocation(in state vector) BitLocation(0 to 7) CRLF
            #http://bci2000.org/wiki/index.php/Technical_Reference:State_Definition
            #Typically, state values change once per block or once per trial.
            #State values are saved per block.
            #"SpecificState 1 0 0 0", #Define states that are specific to this extension.
            "FBValue    16 0 0 0", #in blocks, 16-bit is max 65536
            "FBBlock   16 0 0 0", #Number of blocks that feedback has been on. Necessary for fake feedback.
            "Feedback 1 0 0 0", #Whether or not stimuli are currently presented.
        ]

    @classmethod
    def preflight(cls, app, sigprops):
        if int(app.params['ContFeedbackEnable'])==1:
            # Check FeedbackChannels
            chn = app.inchannels()
            fch = app.params['FeedbackChannels'].val
            if len(fch)==0: raise EndUserError, "Must supply FeedbackChannel"
            if False in [isinstance(x, int) for x in fch]:
                nf = filter(lambda x: not str(x) in chn, fch)
                if len(nf): raise EndUserError, "FeedbackChannel %s not in module's list of input channel names" % str(nf)
                app.fbchan = [chn.index(str(x)) for x in fch]
            else:
                nf = [x for x in fch if x < 1 or x > len(chn) or x != round(x)]
                if len(nf): raise EndUserError, "Illegal FeedbackChannel: %s" % str(nf)
                app.fbchan = [x-1 for x in fch]

            app.fbchan = app.fbchan if len(app.fbchan) == app.nclasses else [app.fbchan[0] for x in range(app.nclasses)]
            app.vfb_type = app.params['VisualType'].val if len(app.params['VisualType']) == app.nclasses else [app.params['VisualType'].val[0] for x in range(app.nclasses)]

    @classmethod
    def initialize(cls, app, indim, outdim):
        if int(app.params['ContFeedbackEnable'])==1:
            if int(app.params['ShowSignalTime']):
                app.addstatemonitor('FBValue')
                app.addstatemonitor('FBBlock')
                app.addstatemonitor('Feedback')

            #===================================================================
            # Load fake data if we will be using fake feedback.
            #===================================================================
            if int(app.params['FakeFeedback']):
                import csv
                fp=app.params['FakeFile']
                app.fake_data = np.genfromtxt(fp, delimiter=',')
                np.random.shuffle(app.fake_data)

            #===================================================================
            # We need to know how many blocks per feedback period
            # so (non-bar) feedback can be scaled appropriately.
            #===================================================================
            fbdur = app.params['TaskDur'].val #feedback duration
            fbblks = fbdur * app.eegfs / app.spb #feedback blocks

            #===================================================================
            # Visual Feedback
            #===================================================================
            if app.params['VisualFeedback'].val:
                #===================================================================
                # Set a coordinate frame for the screen.
                #===================================================================
                scrsiz = min(app.scrw,app.scrh)
                siz = (scrsiz, scrsiz)
                b = box(size=siz, position=(app.scrw/2.0,app.scrh/2.0), sticky=True)
                #b is now our perfect box taking up as much of our screen as we are going to use.
                #its center is the center pixel, its width and height are equal to the smallest of screen width and height
                center = b.map((0.5,0.5), 'position') #what is the center pixel value? e.g.([400.0, 225.0])

                #===================================================================
                # TODO: Get the arrows working for more than 2 targets
                #===================================================================
                #===============================================================
                # b.scale(x=0.25,y=0.4)#How big should the arrow be, relative to the screen size
                # arrow = PolygonTexture(frame=b, vertices=((0.22,0.35),(0,0.35),(0.5,0),(1,0.35),(0.78,0.35),(0.78,0.75),(0.22,0.75),),\
                #                    color=(1,1,1), on=False, position=center)
                # app.stimulus('arrow', z=4.5, stim=arrow)#Register the arrow stimulus.
                #
                # b.scale(x=4.0, y=2.5)#Reset the box
                # b.anchor='center'#Reset the box
                #===============================================================

                #===============================================================
                # Target rectangles.
                #===============================================================
                targtw = 0.5
                for x in range(app.nclasses):
                    my_target = app.target_range[x]
                    targ_h = int((my_target[1] - my_target[0]) * scrsiz / 200.0)
                    targ_y = int(center[1] + (my_target[0] + my_target[1]) * scrsiz / 400.0)
                    targ_stim = Block(position = [center[0], targ_y], size = [targtw * scrsiz, targ_h], color=(1, 0.1, 0.1, 0.5), on=False)
                    app.stimulus('target_'+str(x), z=2, stim=targ_stim)

                #Our feedback will range from -10 to +10
                app.m=app.scrh/20.0#Conversion factor from signal amplitude to pixels.
                app.b_offset=app.scrh/2.0 #Input 0.0 should be at this pixel value.

                #===============================================================
                # Add feedback elements
                #===============================================================
                app.vfb_keys = []
                for j in range(app.nclasses):
                    if app.vfb_type[j]==0: #Bar
                        app.addbar(color=(0,0.9,0), pos=(app.scrw/2.0,app.b_offset), thickness=app.scrw/10, fac=app.m)
                        app.vfb_keys.append('barrect_' + str(len(app.bars)))
                        app.stimuli['bartext_'+ str(len(app.bars))].position=(50,50)#off in the lower corner
                        #app.stimuli['bartext_'+ str(len(app.bars))].color=[0,0,0]#hide it
                        app.stimuli['bartext_'+ str(len(app.bars))].on = False#hide it

                    elif app.vfb_type[j]==1: #Cursor
                        app.stimulus('cursor_'+str(j), z=3, stim=Disc(position=(app.scrw/2.0,app.b_offset), radius=10, color=(0.9,0.9,0.9), on=False))
                        app.vfb_keys.append('cursor_'+str(j))
                        #Set cursor speed so that it takes entire feedback duration to go from bottom to top at amplitude 1 (= 1xvar; =10% ERD; =10%MVC)
                        app.curs_speed = scrsiz / fbblks #pixels per block

                    elif app.vfb_type[j]==2: #Color-change circle.
                        app.col_zero = (0, 1, 0)#Green in the middle.
                        app.stimulus('col_circle_'+str(j), z=3, stim=Disc(position=center, radius=100, color=app.col_zero, on=False))
                        app.col_speed = 2*(2 / fbblks) #Colors will be mapped from -1 to +1. #Trying to double the speed to see if that helps.
                        app.vfb_keys.append('col_circle_'+str(j))

                    elif app.vfb_type[j]==3: #None
                        app.stimulus('cursor_'+str(j), z=-10, stim=Disc(radius=0, color=(0,0,0,0), on=False))
                        app.vfb_keys.append('cursor_'+str(j))

            #===================================================================
            # Audio Feedback
            #===================================================================
            if app.params['AudioFeedback'].val:
            # load, and silently start, the sounds
            # They will be used for cues and for feedback.
                app.sounds = []
                wavmat = app.params['AudioWavs']
                for i in range(len(wavmat)):
                    wavlist = wavmat[i]
                    if len(wavlist) != 1: raise EndUserError, 'FeedbackWavs matrix should have 1 column'
                    try: snd = WavTools.player(wavlist[0])
                    except IOError: raise EndUserError, 'failed to load "%s"'%wavlist[0]
                    app.sounds.append(snd)
                    snd.vol = 0
                    snd.play(-1)
                #Set the speed at which the fader can travel from -1 (sounds[0]) to +1 (sounds[1])
                app.fader_speed = 2 / fbblks

            #===================================================================
            # Handbox Feedback
            #===================================================================
            if app.params['HandboxFeedback'].val:
                from Handbox.HandboxInterface import Handbox
                serPort=app.params['HandboxPort'].val
                app.handbox=Handbox(port=serPort)
                #When x is +1, we have ERD relative to baseline
                #It should take fbblks at x=+1 to travel from 90 to 0
                app.hand_speed = -90 / fbblks #hand speed in degrees per block when x=+1

            #===================================================================
            # Neuromuscular Electrical Stimulation Feedback
            #===================================================================
            if app.params['NMESFeedback'].val:
                stimrange=np.asarray(app.params['NMESRange'].val,dtype='float64')#midpoint and max
                stim_min = 2*stimrange[0] - stimrange[1]
                from Handbox.NMESInterface import NMES
                serPort=app.params['NMESPort'].val
                app.nmes=NMES(port=serPort)
                app.nmes.width = 1.0

                #from Caio.NMES import NMESFIFO
                ##from Caio.NMES import NMESRING
                #app.nmes = NMESFIFO()
                ##app.nmes = NMESRING()
                #app.nmes.running = True

                #It should take fbblks at x=+1 to get intensity from min to max
                app.nmes_baseline = stimrange[0]
                app.nmes_max = stimrange[1]
                app.nmes_i = app.nmes.intensity
                app.nmes_speed = (stimrange[1]-stim_min) / float(fbblks) #nmes intensity rate of change per block when x=+1

                #app.nmes_baseline = stimrange[0]
                #app.nmes_max = stimrange[1]
                #for i in np.arange(0.1,2*app.nmes_baseline-app.nmes_max,0.1):
                #    app.nmes.amplitude = i
                #    time.sleep(0.1)
                #app.nmes_speed = float(2) * (app.nmes_max - app.nmes_baseline) / float(fbblks)

    @classmethod
    def halt(cls,app):
        if int(app.params['ContFeedbackEnable'])==1:
            #TODO: Delete app.nmes, app.handbox, remove the meters.
            pass

    @classmethod
    def startrun(cls,app):
        if int(app.params['ContFeedbackEnable'])==1:
            if 1 in app.vfb_type:
                for j in range(app.nclasses):
                    if app.vfb_type[j]==1:
                        app.stimuli['cursor_'+str(j)].position = app.positions['origin'].A.ravel().tolist()
            if int(app.params['NMESFeedback']):
                app.nmes_i = 0
                app.nmes.intensity = 0

    @classmethod
    def stoprun(cls,app):
        if int(app.params['ContFeedbackEnable'])==1:
            if app.params['AudioFeedback'].val:
                for snd in app.sounds: snd.vol = 0.0
            if int(app.params['NMESFeedback']):
                app.nmes.stop()

    @classmethod
    def transition(cls,app,phase):
        if app.params['ContFeedbackEnable'].val:
            #What target are we on?
            #TargetCode and LastTargetCode are updated to the current target on GoCue transition.
            #LastTargetCode will maintain the value of the most recent TargetCode even in Baseline.
            t = app.states['LastTargetCode']
            app.states['Feedback'] = phase=='task' or app.params['BaselineFeedback'].val#Will we provide feedback this phase?

            #===================================================================
            # For every transition, we will manage the on/off state of our feedback elements.
            #===================================================================

            # Visual feedback elements (bars, cursors, etc)
            if app.params['VisualFeedback'].val:
                for j in range(app.nclasses):
                    app.stimuli[app.vfb_keys[j]].on = app.states['Feedback'] and j==t-1
            # Non-visual feedback should be turned off when states['Feedback'] is off.
            if not app.states['Feedback']:
                if app.params['AudioFeedback'].val:
                    for snd in app.sounds: snd.vol=0.0
                if int(app.params['NMESFeedback']):
                    app.nmes.intensity = 0
                if int(app.params['HandboxFeedback']):
                    app.handbox.position = 45

            #===================================================================
            # Transition specific management
            #===================================================================
            if phase == 'intertrial':
                app.states['FBBlock']=0 #Reset how many blocks we've been giving feedback for this trial.
            elif phase == 'baseline':
                pass #Feedback elements don't change in transition to baseline.
            elif phase == 'gocue': #We have our new target code.
                if app.params['VisualFeedback'].val: #Visual _targets_
                    for j in range(app.nclasses):
                        app.stimuli['target_'+str(j)].on = j==t-1#Update which targets are on

                    if app.vfb_type[t-1] == 2:#Colored circles.
                        is_rest = app.params['GoCueText'][t-1].lower() == "rest".lower()
                        app.screen.color = [0,0.5,1] if is_rest else [1,0.5,0]#Target is blue for rest or orange for anything else.
#                    else:
#                        app.screen.color = [0,0,0]#Shouldn't be necessary because we go black during stopcue
                    #===========================================================
                    # app.stimuli['arrow'].color = map(lambda x:int(x==t), [2,1,3])
                    # app.stimuli['arrow'].angle = 180*(2 - t)
                    #===========================================================
                    #Individual feedback elements are checked on every phase transition (above)

                if app.params['AudioFeedback'].val:
                    for j in range(app.nclasses): app.sounds[j].vol = float(j==t-1)
            elif phase == 'task':
                pass
            elif phase == 'response':
                #Keep the target on if it was already on and feedback is provided outside of task.
                #Else turn it off
                for j in range(app.nclasses):
                    app.stimuli['target_'+str(j)].on = app.stimuli['target_'+str(j)].on and app.states['Feedback']
            elif phase == 'stopcue':
                app.screen.color = [0,0,0]

    @classmethod
    def process(cls,app,sig):
        if int(app.params['ContFeedbackEnable'])==1 and app.states['Feedback']:
            t = app.states['LastTargetCode'] #Use LastTargetCode because this does not become 0 between trials.

            if app.params['FakeFeedback'].val:
                trial_i = app.states['CurrentTrial']-1 if app.states['CurrentTrial'] < app.fake_data.shape[0] else random.uniform(0,app.params['TrialsPerBlock'])
                fake_block_ix = np.min((app.fake_data.shape[1],app.states['FBBlock']))
                x = app.fake_data[trial_i,fake_block_ix]
            else:
                #===============================================================
                # Inputs from standard modules will have mean 0, variance 1, and extremes of ~ -10 to +10
                # My ERD input will have mean 0, and extremes of -10 (=-100%) and + ~20 (=+200% baseline). May be inverted (-20 to +10)
                # My EMG input will have a non-zero mean, a min of 0 and a max of 10 (=100% MVC)
                #===============================================================
                x = sig[app.fbchan,:].mean(axis=1)#Extract the feedback channels.
                x = x.A.ravel()[t-1]/3#Transform x to a measure mostly ranging from -3.26 to +3.26 SDs->Necessary for 16-bit integer state
            #Save x to a state of uint16
            x = min(x, 3.26)
            x = max(x, -3.26)
            temp_x = x * 10000
            app.states['FBValue'] = np.uint16(temp_x) #0-32767 for positive, 65536-32768 for negative
            app.states['FBBlock'] = app.states['FBBlock'] + 1

            #Pull x back from the state into the range -10,10. This is useful in case enslave states is used.
            x = np.int16(app.states['FBValue']) * 3.0 / 10000.0

            if app.params['VisualFeedback'].val:
                this_fb = app.stimuli[app.vfb_keys[t-1]]
                if app.vfb_type[t-1]==0:#bar
                    update_by = 0.0 if not app.in_phase('task') and app.params['BaselineConstant'] else x
                    app.bars[int(app.vfb_keys[t-1][-1])-1].set(update_by) #e.g. "barrect_1" take the "1"
                elif app.vfb_type[t-1] == 1: #cursor
                    if not app.in_phase('task') and app.params['BaselineConstant']:
                        this_fb.position = app.positions['origin'].A.ravel().tolist()
                    else:
                        next_pos = this_fb.y + app.curs_speed * x#speed is pixels per block
                        next_pos = min(next_pos, app.scrh) #Never move the position off the top
                        next_pos = max(next_pos, 0) #Never move the position off the bottom
                        this_fb.y = next_pos
                elif app.vfb_type[t-1] == 2: #color-changing circle.
                    fake_y = this_fb.color[0] - this_fb.color[2]#convert old color to a position on -1 to +1 scale.
                    fake_y = fake_y + app.col_speed * x#increment the position
                    fake_y = max(-1, fake_y)
                    fake_y = min(1, fake_y)
                    new_r = fake_y if fake_y >= 0 else 0
                    new_g = 1-0.5*abs(fake_y)
                    new_b = -1*fake_y if fake_y<=0 else 0
                    new_color = app.col_zero if not app.in_phase('task')\
                        and app.params['BaselineConstant'] else [new_r, new_g, new_b]#convert the position to color
                    #if app.states['FBBlock']>150: app.dbstop()
                    this_fb.color = new_color

                #===============================================================
                # Modify the color of the visual targets if we are in range.
                #===============================================================
                if app.params['GatingEnable'].val:
                    in_range = app.states['InRange']
                else:
                    in_range = (10*x >= app.target_range[t-1][0]) and (10*x <= app.target_range[t-1][1])

                for j in range(app.nclasses):
                    app.stimuli['target_'+str(j)].color = [1-in_range, in_range, 0]
                #app.stimuli['fixation'].color = [1-in_range, in_range, 0]#fixation color doesn't need to change.

            if app.params['AudioFeedback'].val and not app.in_phase('gocue'):
                #app.fader_val from -1 to +1
                #can increment or decrement at app.fader_speed
                app.fader_val = app.fader_val + app.fader_speed * x
                app.fader_val = min(1, app.fader_val)
                app.fader_val = max(-1, app.fader_val)
                if not app.in_phase('task') and app.params['BaselineConstant']: app.fader_val = 0
                app.sounds[0].vol = 0.5 * (1 - app.fader_val)
                app.sounds[1].vol = 0.5 * (1 + app.fader_val)

            if app.params['HandboxFeedback'].val:
                angle = app.handbox.position
                angle = angle + app.hand_speed * x
                if not app.in_phase('task') and app.params['BaselineConstant']: angle = 45
                app.handbox.position = angle

            if app.params['NMESFeedback'].val:
                app.nmes_i = app.nmes_i + app.nmes_speed * x
                app.nmes_i = min(app.nmes_i, app.nmes_max)
                app.nmes_i = max(app.nmes_i, 2*app.nmes_baseline - app.nmes_max, 0)
                if not app.in_phase('task') and app.params['BaselineConstant']:
                    if abs(app.nmes_i-app.nmes_baseline)<1: app.nmes_i = app.nmes_baseline
                    elif app.nmes_i > app.nmes_baseline: app.nmes_i = app.nmes_i - app.nmes_speed
                    elif app.nmes_i < app.nmes_baseline: app.nmes_i = app.nmes_i + app.nmes_speed
                elif not (app.nmes.intensity==int(app.nmes_i)): app.nmes.intensity = int(app.nmes_i)

    @classmethod
    def event(cls, app, phasename, event):
        if int(app.params['ContFeedbackEnable'])==1: pass