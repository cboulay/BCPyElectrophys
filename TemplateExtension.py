import numpy as np
import random
import time

class Template(object):
    params = [
              #"Tab:SubSection DataType Name= Value DefaultValue LowRange HighRange // Comment (identifier)",
              #See further details http://bci2000.org/wiki/index.php/Technical_Reference:Parameter_Definition
            "PythonApp:Template        int        TemplateEnable= 1 1 0 1 // Enable: 0 no, 1 yes (boolean)",
        ]
    states = [
              #Name Length(nBits up to 32) Value ByteLocation(in state vector) BitLocation(0 to 7) CRLF
            #http://bci2000.org/wiki/index.php/Technical_Reference:State_Definition
            #Typically, state values change once per block or once per trial.
            #State values are saved per block.
            #"SpecificState 1 0 0 0", #Define states that are specific to this extension.
        ]
    
    @classmethod
    def preflight(cls,app):
        if int(app.params['TemplateEnable'])==1: pass
    
    @classmethod
    def initialize(cls,app):
        if int(app.params['TemplateEnable'])==1: pass
        
    @classmethod
    def halt(cls,app):
        if int(app.params['TemplateEnable'])==1: pass
    
    @classmethod
    def startrun(cls,app):
        if int(app.params['TemplateEnable'])==1: pass
    
    @classmethod
    def stoprun(cls,app):
        if int(app.params['TemplateEnable'])==1: pass
    
    @classmethod
    def transition(cls,app,phase):
        if int(app.params['TemplateEnable'])==1: pass
    
    @classmethod
    def process(cls,app,sig):
        if int(app.params['TemplateEnable'])==1: return sig

    @classmethod
    def event(cls, app, phasename, event):
        if int(app.params['TemplateEnable'])==1: pass