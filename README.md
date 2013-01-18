These modules are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).

1. Installation
2. TemplateApplication
3. ContingencyExtension
4. MagstimExtension
5. DigitimerExtension
6. ContinuousFeedbackExtension
7. ERPExtension

## Installation
Since these modules are for BCPy2000, you must have
[BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html) installed. Read on for specific BCPy2000 instructions.

BCPy2000 can be installed in an isolated environment (see its FullMonty install) or in conjunction
with an existing Python installation. Since I require packages in addition to those provided by the BCPy2000 installation,
and since I use Python for other things ([see EERF](https://github.com/cboulay/EERF)), I prefer to use a full
Python installation.

Note that many neurophysiology devices do not have 64-bit drivers. Thus, I recommend
you install the 32-bit versions of all the following. 32-bit applications will still run in
a Win64 environment.

### Install BCI2000
The [BCI2000 and BCPy2000 binaries](http://www.bci2000.org/wiki/index.php/BCI2000_Binaries)
are probably good enough, but the Python framework that ships with the compiled binaries is out of date.
The best way to get the latest Python framework is by downloading the code through SVN. Since I'm recommending
you use SVN for part of the job, you may as well use it for the whole job. Follow the instructions
[here](http://www.bci2000.org/wiki/index.php/Programming_Reference:BCI2000_Source_Code).
In brief:

1 Download and install [TortoiseSVN](http://tortoisesvn.net)
2 Download and install [MS Visual Studio 2008 Express](http://www.microsoft.com/en-us/download/details.aspx?id=6506)(vcsetup.exe)
3 Download and install [CMake](http://www.cmake.org/cmake/resources/software.html)
4 Create an [account](http://www.bci2000.org/wiki/index.php/Creating_a_User_Account) on bci2000.org
5 Download the source code (`SVN checkout http://www.bci2000.org/svn/trunk BCI2000 --username <username> --password <password>`). This is around 160 MBytes.
6 Change to the `BCI2000/build/` directory and run `Make VS2008 Project Files.bat`
7 During the make process, be sure to make contributions and BCPy2000
8 Open the BCI2000.sln file in VS2008
9 At the top, change the Debug to Release, from the Build menu select "Build Solution". Wait ~10 minutes.

### Install Python
BCPy2000 currently has some dependencies that require Python <= 2.6.
See [here](http://www.bci2000.org/phpbb/viewtopic.php?f=1&t=1330) for a discussion
on using BCPy2000 with more modern Python.

[Download Python 2.6](http://www.python.org/download/releases/2.6.6/).
Run the installer.
Add the Python directory (usually C:\Python26) to your [PATH environment variable](http://www.computerhope.com/issues/ch000549.htm).
(TODO: Do we need to set the PYTHONHOME directory?)

### Installing BCPy2000 dependencies

1. Download and install [setuptools](http://pypi.python.org/pypi/setuptools)
1. Download and install [pyreadline 1.5](http://pypi.python.org/packages/any/p/pyreadline/pyreadline-1.5-win32-setup.exe)
2. Download and install [IPython 0.10.2](http://archive.ipython.org/release/0.10.2/ipython-0.10.2.win32-setup.exe)
3. From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install
    pywin32, numpy, scipy, matplotlib, PIL, pyaudio, pyopengl
4. Download and install [pygame 1.9.1](http://www.pygame.org/download.shtml)
5. Download and install [VisionEgg](http://www.lfd.uci.edu/~gohlke/pythonlibs/#visionegg)

### Installing BCPy2000 Python packages
(?Copy the included EmbeddedPythonConsole.py into the new framework/BCPy2000 folder. Overwrite the existing file.)
Run `BCI2000/src/contrib/BCPy2000/InstallFramework.bat`

At this point you should test that BCPy2000 is working.
Run `BCI2000/src/contrib/BCPy2000/Merge.bat`
Then run `BCI2000/batch/PythonDemo1_Triangle.bat`

### Installing BCPyElectrophys dependencies
The extensions in this repo have additional dependencies depending on which extensions you intend to use.
These include [EERF](https://github.com/cboulay/EERF),
 my [caio package](https://github.com/cboulay/caio-python),
 my [magstim package](https://github.com/cboulay/magstim-python),
 and these may or may not have their own dependencies.

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