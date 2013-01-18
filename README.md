These modules are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).

1. Requirements
2. TemplateApplication
3. ContingencyExtension
4. MagstimExtension
5. DigitimerExtension
6. ContinuousFeedbackExtension
7. ERPExtension

## Requirements
Since these modules are for BCPy2000, you must have BCPy2000 installed.
BCPy2000 can be installed in an isolated environment (see its FullMonty install) or in conjunction
with an existing Python installation.

Since I require packages in addition to those provided by the BCPy2000 installation, and since I use
Python for other things ([see EERF](https://github.com/cboulay/EERF)), I prefer to use a full
Python installation.

Note that many neurophysiological hardware devices do not have 64-bit drivers. Thus, I recommend
you install the 32-bit versions of all the following. 32-bit applications will still run in
a Win64 environment.

### Installing Python
BCPy2000 currently has some dependencies that require Python <= 2.6.
See [here](http://www.bci2000.org/phpbb/viewtopic.php?f=1&t=1330) for a discussion
on using BCPy2000 with more modern Python.

[Download Python 2.6](http://www.python.org/download/releases/2.6.6/).
Run the installer.
Add the Python directory (usually C:\Python26) to your [PATH environment variable](http://www.computerhope.com/issues/ch000549.htm).
(TODO: Do we need to set the PYTHONHOME directory?)

### Installing BCPy2000 dependencies
The BCPy2000 dependencies are listed [here](http://bci2000.org/downloads/BCPy2000/Python_Packages.html).

The easiest way to install Python packages on Windows is to find the binary installers [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).
Make sure to get the ones built for your version of Windows and Python.

Download (but do not yet run) the latest version installers from the above link for the following packages:
Distribute, NumPy, SciPy, pywin32, pygame, PIL, pyaudio, matplotlib, PyOpenGL, and VisionEgg.

Separately, download these installers:
[IPython 0.10.2](http://archive.ipython.org/release/0.10.2/ipython-0.10.2.win32-setup.exe),
[pyreadline 1.5](http://pypi.python.org/packages/any/p/pyreadline/pyreadline-1.5-win32-setup.exe).

Install the packages in this order:
Distribute, pywin32, pyreadline, ipython, numpy, scipy, matplotlib, PyOpenGL, PIL, pyaudio, pygame, VisionEgg.

VisionEgg sometimes has problems with recent versions of PyOpenGL. On my working system, I have PyOpenGL v 3.0.2a4 and VisionEgg 1.2.1.
(TODO: Maybe the trick is that VisionEgg has to be compiled locally against the recent PyOpenGL install?)

### Installing BCI2000
http://www.bci2000.org/wiki/index.php/BCI2000_Binaries
Get both the latest release build and the contributed code.

### Installing BCPy2000
Download from Option B [here](http://bci2000.org/downloads/BCPy2000/Download.html).
Open the zip file and copy PythonApplication, PythonSignalProcessing, and PythonSource exe files
from BCPy2000-demo-20110710/demo/prog to your BCI2000/prog directory.
Copy the framework folder from BCPy2000-demo-20110710 to somewhere convenient (like your BCI2000 folder).
Copy the included EmbeddedPythonConsole.py into the new framework/BCPy2000 folder. Overwrite the existing file.
Open a console window, change the the new framework folder, and execute
'python setup.py install'

### Installing BCPyElectrophys dependencies
The extensions in this repo have additional dependencies depending on which extensions you intend to use.
These include [EERF](https://github.com/cboulay/EERF),
 my [caio package](https://github.com/cboulay/caio-python),
 my [magstim package](https://github.com/cboulay/magstim-python),
 and possibly a couple other packages that are not published.

### Downloading and installing BCPyElectrophys
TODO: Describe how to use git and/or tag this release for .zip downloads.

# Description

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