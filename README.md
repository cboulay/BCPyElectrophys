These modules are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).

1. Installation
2. TemplateApplication
3. ContingencyExtension
4. MagstimExtension
5. DigitimerExtension
6. ContinuousFeedbackExtension
7. ERPExtension

## Installation

### Prerequisites

These modules only work with BCPy2000.
BCPy2000 can be installed in an isolated manner (see its [FullMonty 
install] (http://bci2000.org/downloads/BCPy2000/Download.html)) 
or alongside an existing Python installation.
Since I require packages in addition to those provided by the BCPy2000 installation,
and since I use Python for other things ([see EERF](https://github.com/cboulay/EERF)),
I prefer to use a full Python installation. Below I explain how to do that.

### Installing Python

#### Which version?
BCPy2000 currently has some dependencies that require Python 2.6.
See [here](http://www.bci2000.org/phpbb/viewtopic.php?f=1&t=1330) for a discussion
on using BCPy2000 with modern packages. Briefly, BCPy2000 works best with VisionEgg as its renderer,
and VisionEgg requires older versions of PyOpenGL that are incompatible with Python >= 2.7.
Also, BCPy2000 requires IPython 0.10, which is incompatible with Python >= 2.7.

[Download Python 2.6](http://www.python.org/download/releases/2.6.6/).
Run the installer.
Add the Python directory (usually C:\Python26) to your PATH System Variable.
Also add the Scripts directory (C:\Python26\Scripts) to your PATH System Variable.
(Do we need to set the PYTHONHOME, PYTHONPATH, PYTHONROOT system variable?)

### Installing BCPy2000 dependencies
The BCPy2000 dependencies are listed [here](http://bci2000.org/downloads/BCPy2000/Python_Packages.html).

The easiest way to install Python packages on Windows is to find the pre-compiled installers [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/).
Make sure to get the ones built for your version of Windows and Python.

This will only work for some of the packages:
numpy, scipy, pywin32, pygame, PIL, setuptools, pyaudio, matplotlib, visionegg
For other packages we need older versions:
[IPython 0.10.2](http://archive.ipython.org/release/0.10.2/),
[pyreadline 1.5](https://launchpad.net/pyreadline/1.5/1.5/+download/pyreadline-1.5-win32-setup.exe),
[PyOpenGL 2.0.2.01](http://sourceforge.net/projects/pyopengl/files/PyOpenGL/2.0.2.01%20%28alpha%29/)

PyOpenGL 2.0.2.01 does not come precompiled for Python 2.6. You will have to
[build it yourself](http://pyopengl.sourceforge.net/documentation/installation-v2.html).
Its compilation on Windows requires [Visual Studio Express 2008](http://www.microsoft.com/en-us/download/details.aspx?id=14597) (Get vcsetup.exe).
VS2008 will also be used to compile BCI2000 from source (see below).

### Installing BCPyElectrophys dependencies
BCPyElectrophys have additional dependencies depending on which extensions you intend to use.
ERPExtension requires [EERF](https://github.com/cboulay/EERF),
DigitimerExtension, or MagstimExtension might require [my caio package](https://github.com/cboulay/caio-python),
MagstimExtension requires [my magstim package](https://github.com/cboulay/magstim-python), 
ContinuousFeedbackExtension may require a couple other packages that are not published (for Handbox or NMES).
For each of these, installation requires first downloading the files then running `python setup.py install`

### Installing BCI2000
You can either [download the source code and compile it yourself](http://www.bci2000.org/wiki/index.php/Programming_Reference:BCI2000_Source_Code),
or [download precompiled binaries](http://www.bci2000.org/wiki/index.php/BCI2000_Binaries).
Unfortunately the precompiled binaries do not contain the executables for BCPy2000,
and the only downloadable binaries for BCPy2000 are rather old. Thus it is probably necessary
for you to install BCI2000 using the source code method so you can get BCPy2000 as well. Follow the instructions in the link above.

Alternatively, you can install using the binaries and e-mail me for more recent versions of BCPy2000.
With either method, you will need to create an account and agree to the license to download BCI2000.

### Installing BCPy2000
If you compiled BCI2000 yourself from source then during the CMake process you should have seen the option to
Make BCPy2000 and chosen to Make it then have compiled it alongside BCI2000.
If you cannot compile from the BCI2000 source, and you installed
BCI2000 from the binaries above, then you need to e-mail me so that I may provide you with
the latest BCPy2000 executables. At some point in the (hopefully near) future, the
[BCPy2000 download site](http://bci2000.org/downloads/BCPy2000/Download.html)
should be updated with more recent files.

Locate your BCI2000/src/contrib/BCPy2000/ directory.
Run InstallFramework.bat

### Using these modules
TODO: Attach a demo batch file and parameter file.

## TemplateApplication

This BCPy2000 application does not do much except define the phases of each trial
and call on the extensions.
The phases are: intertrial, baseline, gocue, task, response, stopcue
The phase durations can either be set by parameters (intertrial, baseline), or that might be determined
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