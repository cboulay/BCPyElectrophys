These modules are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).

1. TemplateApplication
2. ContingencyExtension
3. MagstimExtension
4. DigitimerExtension
5. ContinuousFeedbackExtension
6. ERPExtension

## TemplateApplication

This BCPy2000 application does not do much except define the phases of each trial
and call on the extensions.
The phases are: intertrial, baseline, gocue, task, response, stopcue
The duration of gocue and stopcue are coded to be 1000 ms, the other phases have durations
that can either be set by parameters (intertrial, baseline), or that might be determined
by events occuring in the extensions.

## ContingencyExtension

This extension is named for historical reasons. I should change its name.
This extension blocks the trial from progressing past the task phase
unless a signal feature that it is monitoring remains in some range for
some duration + some other random duration.

## MagstimExtension

This extension is for interacting with a magstim device. It can trigger single-pulse
or bistim TMS when the task transitions into the 'response' phase. This extension
requires my [magstim-python](https://github.com/cboulay/magstim-python) package. It is also
possible to trigger the Magstim device with a TTL over BNC and for that I use a
Contec USB D/A device, requiring my [caio-python](https://github.com/cboulay/caio-python) package.

## DigitimerExtension

This extension is for activating nerve stimulation using a Digitimer device. The stimulus
timing and amplitude is determined by a Contec USB D/A device, requiring my
[caio-python](https://github.com/cboulay/caio-python) package.

## ContinuousFeedbackExtension

This extension enables continuous feedback of some (brain) signal. Feedback may be auditory,
visual (a bar or a cursor), passive movement operated by a custom device we have,
or neuromuscular stimulation controlled by a custom device we have. Both the passive movement
and NMES devices require another Python package that I have. I have not published this
package because I am uncertain if it reveals any intellectual property. If you are 
interested in this package then please contact me directly.

## ERPExtension

This extension enables storing of ERPs into a custom database, and then
possibly providing feedback about the amplitude of an ERP feature. This
extension requires my [EERF python](https://github.com/cboulay/EERF) repo.