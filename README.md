This work is supported by the Japan Society for the Promotion of Science Postdoctoral Fellowship.
This is being developed primarily as part of my postdoctoral fellowship in the Ushiba Lab
at Keio University in Yokohama, Japan.

1. Installation
2. TemplateApplication
3. ContingencyExtension
4. MagstimExtension
5. DigitimerExtension
6. ContinuousFeedbackExtension
7. ERPExtension

## Installation

The Python files in this repository are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).
BCPy2000 comprises, among other things, BCI2000 signal-source, signal-processing, and application modules
which act as interfaces for Python. Thus, BCI2000 can run Python programs through these modules.

BCPy2000 thus requires a Python interpreter to be available. An isolated Python environment can suffice (see its FullMonty install).
However, BCPyElectrophys requires packages in addition to those included with BCPy2000 FullMonty, and I use Python for other things 
(e.g., [EERF](https://github.com/cboulay/EERF)), thus I prefer to use a full Python installation.

Instructions on how to install Python and the necessary packages follow.

### Decide on 32-bit or 64-bit

Your Python interpreter, any precompiled Python packages you install, any DLLs Python might load, and the BCI2000 Python modules must all have the same architecture.
One of my BCPyElectrophys extensions (for interfacing with a Contec device) loads a 32-bit dll and thus I need 32-bit Python and BCI2000 Python modules.
You can mix and match architectures between modules (e.g., a 64-bit gUSBampSource module and a 32-bit PythonApplication module).

### Install Python

Python can be installed manually or as part of a larger "Python Distribution". The distributions usually include
the most recent stable versions of Python (2.7 as of this writing), many additional packages that are common to specific fields, and some additional tools to help manage and edit your Python files.

While recently there have been some changes to BCPy2000 to support Python 2.7, I still cannot get it to work.
Thus the primary installation method outlined here will be the manual method for Python 2.6.
I include some notes for other installation methods, including Manual 2.7 and the Anaconda and Canopy Python Distributions, but those methods do not work for me.

#### Manual (Python 2.6)

1. [Download Python 2.6 MSI Installer](http://www.python.org/download/releases/2.6.6/).
2. Run the installer.
3. Add the Python directory and its Scripts subdirectory (usually `C:\Python26;C:\Python26\Scripts`) to your [PATH environment variable](http://www.computerhope.com/issues/ch000549.htm).

#### Manual (Python 2.7)

1. [Download Python 2.7 MSI Installer](http://www.python.org/download).
2. Run the installer.
3. Add the Python directory and its Scripts subdirectory (usually `C:\Python27;C:\Python27\Scripts`) to your [PATH environment variable](http://www.computerhope.com/issues/ch000549.htm).

#### Anaconda

1. [Download Anaconda](http://continuum.io/downloads)
2. Add its directory and Scripts subdirectory to the Path.

#### Canopy

1. [Download Canopy](https://www.enthought.com/products/canopy/academic/).
2. Install Canopy.
3. Add its Users\<username>\AppData\Local\Enthought\Canopy32\?\Scripts directory to the Path.

### Install BCPy2000 package dependencies

BCPy2000 requires the following packages: IPython, pywin32, numpy, scipy, matplotlib, pyaudio, pyopengl, PIL, pygame, VisionEgg
IPython in windows also depends on pyreadline.

#### Manual Python 2.6 for 32-bit

(If the version number is listed, then you must use that specific version)

1. Download and install [setuptools](http://pypi.python.org/pypi/setuptools)
	1. Download [ez_setup.py](https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py)
	2. From the command-line, run `python ez_setup.py`
2. Download and install [pyreadline 1.5](http://pypi.python.org/packages/any/p/pyreadline/pyreadline-1.5-win32-setup.exe)
3. Download and install [IPython 0.10.2](http://archive.ipython.org/release/0.10.2/ipython-0.10.2.win32-setup.exe)
4. From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install the latest
    pywin32, numpy (MKL version is OK), scipy, matplotlib, pyaudio, Pillow, and pyopengl
    (be sure to get the files ending in win32-py2.6.exe). matplotlib has additional dependencies. See the webpage.
5. Download and install [pygame 1.9.1](http://www.pygame.org/download.shtml)
6. Download and install [VisionEgg](http://www.lfd.uci.edu/~gohlke/pythonlibs/#visionegg)

#### Manual Python 2.7

From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install
setuptools, pyreadline, IPython, pywin32, numpy, scipy, matplotlib, pyaudio, pyopengl, pillow, pygame, VisionEgg
Alternatively, many of these can be skipped with [SciPy-Stack](http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy-stack),
leaving only pywin32, pyaudio, pyopengl, pygame, VisionEgg

#### Anaconda

From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install pyopengl, pygame, VisionEgg

#### Canopy

1. Use its Package Manager to install VisionEgg.
2. From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install pygame
Note the Canopy Package Manager will not launch if the PYTHONHOME environment variable is set to anything.

### Install BCI2000

You can download pre-compiled binaries (Easy Way) or download the source and compile it yourself (Hard Way).
Which way you choose is up to you. For both methods, you will need to start by doing the following:

1. Create an [account](http://www.bci2000.org/wiki/index.php/Creating_a_User_Account) on bci2000.org

#### The Easy Way

1. BCI2000 itself should be installed from the [pre-compiled binaries](http://www.bci2000.org/wiki/index.php/BCI2000_Binaries#Contributed_Code).
Get `BCI2000Contrib.exe`. For the remainder of this section let us consider the directory where BCI2000 was extracted as $BCI2000PATH.

#### The Hard Way

If you are a developer and you expect to change the BCI2000 source code, then you should get access to the source code and compile it yourself.

Follow the instructions
[here](http://www.bci2000.org/wiki/index.php/Programming_Reference:BCI2000_Source_Code).
In brief (on Windows):

1. Download and install [TortoiseSVN](http://tortoisesvn.net)
2. Download and install [MS Visual Studio 2008 Express](http://www.microsoft.com/en-us/download/details.aspx?id=6506)(vcsetup.exe)
3. Download and install [CMake](http://www.cmake.org/cmake/resources/software.html)
4. Download the source code (`SVN checkout http://www.bci2000.org/svn/trunk BCI2000 --username <username> --password <password>`). This is around 160 MBytes. We will call the location of the created directory `$BCI2000PATH`.
5. Change to the `$BCI2000PATH/build/` directory and run the script appropriate for you (e.g., `Make VS2008 Project Files.cmd`)
6. During the make process, be sure to answer yes to make contributions and BCPy2000
7. Open the BCI2000.sln file in VS2008
8. At the top, change "Debug" to "Release".
9. From the Build menu select "Build Solution". Wait ~10 minutes.
10. Copy 


### Install BCPy2000

#### The Easy Way

If you did "The Hard Way" for BCI2000 installation then all you need to do is run `$BCI2000PATH/src/contrib/BCPy2000/InstallFramework.bat`.

If you did "The Easy Way" for BCI2000 installation then do the following:

1. Download the BCPy2000 foundation files (i.e. the BCI2000 modules that will execute the Python code) from the 
[BCPy2000-demo](http://bci2000.org/downloads/BCPy2000/Download.html) (see Option B BCPy2000-demo-X.zip).
2. Extract the archive somewhere.
3. From the extracted archive's `demo` directory, merge the `batch`, `parms`, and `python` directories with those of $BCI2000PATH.
4. From the extracted archive's `demo\prog` directory, copy `PythonApplication.exe`, `PythonSignalProcessing.exe`, and `PythonSource.exe` into `$BCI2000PATH\prog`.
4. Install the BCPy2000 Python packages.
	1. Open a command prompt.
	2. Change to the extracted archive's `framework` directory. (e.g., `cd Downloads\BCPy2000-demo-20110710\framework`)
	3. `python setup.py install`

#### The Hard Way

If you need the latest fixes to BCPy2000 then use this method.

1. If you did not do "The Hard Way" for the BCI2000 installation above, then do so now.
2. Copy this URL to your clipboard: `http://www.bci2000.org/svn/trunk/src/contrib/BCPy2000/framework/BCPy2000`
3. Change to your Python site-packages directory (e.g., `C:\Python26\Lib\site-packages`)
4. Right-click in empty space and do an SVN checkout. It should automatically get the URL from the clipboard, if not paste it in and start the download.

#### Extra steps for all

1. Edit C:\Python27\Lib\site-packages\BCPy2000\AppTools\Shapes.py
	1. Change `import Image, ImageDraw` to `from PIL import Image, ImageDraw` or overwrite it with the file from this_repo\BCPyframework
2. Edit C:\Python27\Lib\site-packages\VisionEgg\Textures.py
	1. Change `import Image, ImageDraw` to `from PIL import Image, ImageDraw`
	2. Comment out lines 41-42

#### Extra steps for Python 2.7 (including distributions)

1. Replace C:\Python27\Lib\site-packages\BCPy2000\EmbeddedPythonConsole.py with the one from this repo.
2. Edit C:\Python27\Lib\site-packages\pyreadline\console\console.py
	1. Change Line 606 from `if sys.version_info[:2] < (2, 6):` to if sys.version_info[:2] < (2, 8):`

### Stop and Test

At this point you should test that BCPy2000 is working.
1. Edit `$BCI2000PATH/batch/PythonDemo1_Triangle.bat` and comment out the call to portable.bat by prepending that line with `::`.
2. Run `$BCI2000PATH/batch/PythonDemo1_Triangle.bat`

### Installing BCPyElectrophys dependencies

BCPyElectrophys has no dependencies in addition to the BCPy2000 dependencies unless you plan to use
the Ogre3D renderer (as part of ContinuousFeedbackExtension),
a Magstim stimulator (as part of MagstimExtension),
or ERPExtension (for online analysis and visualization of ERPs).
See below for an explanation of each extension and their requirements.

### Downloading and installing BCPyElectrophys

You can either use git or download the tagged version.

Git:

You need a git client. Either [Git](http://git-scm.com/downloads)(command-line) or [SourceTree](http://sourcetreeapp.com/)(GUI).
Change to BCI2000's parent directory. `git clone git://github.com/cboulay/BCPyElectrophys.git`

Tag:

Click on Tags near the top right of this page. Download the source code in an archive.
Extract the contents of the archive (i.e., its root folder) into BCI2000's parent folder.
Rename this folder from "BCPyElectrophys-<tagname>" to "BCPyElectrophys".
You should have `\parent\BCI2000` and `\parent\BCPyElectrophys`

### Stop and Test (again)

Test by changing to the BCPyElectrophys folder and running `test.bat`.
Nothing is enabled by default, but you should be able to see the debug information showing task progression.

# Description

## TemplateApplication

`TemplateApplication.py` is a BCPy2000 [developer file](http://bci2000.org/downloads/BCPy2000/Developer_Files.html).
This file describes a BciApplication class. The application class has several [hooks](http://bci2000.org/downloads/BCPy2000/Hook.html)
that BCI2000/BCPy2000 will call automatically at the appropriate time. You can get more detailed information
about each of these hooks [here](http://bci2000.org/downloads/BCPy2000/BciGenericApplication.html).

`TemplateApplication.py` does not do much except define the phases of each trial
and call on the application extensions.
I have defined the phases as "intertrial", "baseline", "gocue", "task", "response", and "stopcue".
Each trial cycles through these phases. The durations of each phase might be defined by parameters
or they might be determined by an extension.

## GatingExtension

This extension blocks the trial from progressing past the "task" phase
unless a signal feature that it is monitoring remains in some range for
some duration + some other random duration.

## MagstimExtension

This extension is for interacting with a Magstim device. It can trigger single-pulse
or bistim TMS when the task transitions into the 'response' phase. This extension
makes use of my [magstim-python](https://github.com/cboulay/magstim_python) package.
That package is already included as a submodule of BCPyElectrophys. To download the
submodule, in a git-bash prompt, change to the BCPyElectrophys directory and enter: `git submodule update --init`.

Note that the Magstim stimulator also requires [pyserial](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyserial).

It is also possible to trigger the Magstim device with a TTL over BNC and for that I use a
Contec USB D/A device, requiring my [caio-python](https://github.com/cboulay/caio_python) package.
This package is also included as a submodule of BCPyElectrophys.

## DigitimerExtension

This extension is for activating nerve stimulation using a Digitimer device. The stimulus
timing and amplitude is determined by a Contec USB D/A device, requiring my
[caio-python](https://github.com/cboulay/caio_python) package.
That package is already included as a submodule of BCPyElectrophys. To download the
submodule, in a git-bash prompt, change to the BCPyElectrophys directory and enter: `git submodule update --init`.

## ContinuousFeedbackExtension

This extension enables continuous feedback of some signal. Feedback may be auditory,
visual (e.g., a bar, a cursor, the color of a circle), passive movement operated by a custom device we have,
or neuromuscular stimulation controlled by a custom device we have. Both the passive movement
and NMES devices require another Python package that I have. I have not published this
package because I am uncertain if it reveals any intellectual property. If you are
interested in this package then please contact me directly.

If you want to use the Ogre3D engine for visual feedback then you'll need my
[BCPyOgreRenderer](https://github.com/cboulay/BCPyOgreRenderer) package.
That package is already included as a submodule of BCPyElectrophys. To download the
submodule, in a git-bash prompt, change to the BCPyElectrophys directory and enter: `git submodule update --init`.

Note that BCPyOgreRenderer also requires python-ogre.
See the [BCPyOgreRenderer page](https://github.com/cboulay/BCPyOgreRenderer) for installation instructions.

## ERPExtension

This extension enables storing of ERPs into a custom database, and then
possibly providing feedback about the amplitude of an ERP feature. This
extension requires my [EERF python](https://github.com/cboulay/EERF) package.
See that page for installation instructions.
