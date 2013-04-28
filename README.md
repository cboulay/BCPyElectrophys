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
These files are for use with [BCPy2000](http://bci2000.org/downloads/BCPy2000/BCPy2000.html).
BCPy2000 can be installed in an isolated environment (see its FullMonty install) or in conjunction
with an existing Python installation. Since I require packages in addition to those required
by BCPy2000, and since I use Python for other things
([see EERF](https://github.com/cboulay/EERF)), I prefer to use a full Python installation.

### Install Python
BCPy2000 currently has some [dependencies](http://www.bci2000.org/phpbb/viewtopic.php?f=1&t=1330) that require Python <= 2.6.

[Download Python 2.6](http://www.python.org/download/releases/2.6.6/).
Run the installer.
Add the Python directory (usually `C:\Python26`) to your [PATH environment variable](http://www.computerhope.com/issues/ch000549.htm).

### Install BCPy2000 dependencies
(If the version number is listed, then you must use that specific version)

1. Download and install [setuptools](http://pypi.python.org/pypi/setuptools)
2. Download and install [pyreadline 1.5](http://pypi.python.org/packages/any/p/pyreadline/pyreadline-1.5-win32-setup.exe)
3. Download and install [IPython 0.10.2](http://archive.ipython.org/release/0.10.2/ipython-0.10.2.win32-setup.exe)
4. From [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/) download and install the latest
    pywin32, numpy, scipy, matplotlib, PIL, pyaudio, and pyopengl
    (be sure to get the files ending in win32-py2.6.exe)
5. Download and install [pygame 1.9.1](http://www.pygame.org/download.shtml)
6. Download and install [VisionEgg](http://www.lfd.uci.edu/~gohlke/pythonlibs/#visionegg)

### Install BCI2000 and BCPy2000

#### The Easy Way

1. BCI2000 itself should be installed from the [pre-compiled binaries](http://www.bci2000.org/wiki/index.php/BCI2000_Binaries).
For the remainder of this section let us consider the directory where BCI2000 was extracted as $BCI2000PATH.
2. Unfortunately, BCPy2000 is not included in the BCI2000 distributions. Download the BCPy2000 foundation files (i.e. the BCI2000 modules that will execute the Python code) from the
[BCPy2000-demo](http://bci2000.org/downloads/BCPy2000/Download.html) (see Option B).
3. From the extracted archive's `demo` directory, copy the `batch`, `parms`, and `python` directories to $BCI2000PATH.
4. From the extracted archive's `demo\prog` directory, copy `PythonApplication.exe`, `PythonSignalProcessing.exe`, and `PythonSource.exe` into `$BCI2000PATH\prog`.
5. The prepackaged BCPy2000 downloads have rather old framework files so we will have to install those from the source code repository.
There are several ways to do this, but the easiest way to maintain your BCPy2000 framework files is to use SVN to manage the files within
the Python directory (usually `C:\Python26\Lib\site-packages`). Change to that directory, and ask Tortoise-SVN to
checkout `http://www.bci2000.org/svn/trunk/src/contrib/BCPy2000/framework/BCPy2000`.

#### The Hard Way

If you are a developer and you expect to change the BCI2000 source code, or you need the latest fixes to BCI2000/BCPy2000,
then you should get access to the source code and compile it yourself.

Follow the instructions
[here](http://www.bci2000.org/wiki/index.php/Programming_Reference:BCI2000_Source_Code).
In brief (on Windows):

1. Download and install [TortoiseSVN](http://tortoisesvn.net)
2. Download and install [MS Visual Studio 2008 Express](http://www.microsoft.com/en-us/download/details.aspx?id=6506)(vcsetup.exe)
3. Download and install [CMake](http://www.cmake.org/cmake/resources/software.html)
4. Create an [account](http://www.bci2000.org/wiki/index.php/Creating_a_User_Account) on bci2000.org
5. Download the source code (`SVN checkout http://www.bci2000.org/svn/trunk BCI2000 --username <username> --password <password>`). This is around 160 MBytes. We will call the location of the created directory `$BCI2000PATH`.
6. Change to the `$BCI2000PATH/build/` directory and run `Make VS2008 Project Files.bat`
7. During the make process, be sure to make contributions and BCPy2000
8. Open the BCI2000.sln file in VS2008
9. At the top, change the Debug to Release*, from the Build menu select "Build Solution". Wait ~10 minutes.
10. Run `$BCI2000PATH/src/contrib/BCPy2000/InstallFramework.bat`

* The BCPy2000 modules and the version of Python you use must both compiled for the same architecture,
i.e. 32-bit or 64-bit. Most neurophysiology devices only have 32-bit drivers and thus will only
work with the 32-bit source modules. Also, BCPy2000 currently requires certain packages that do not
have 64-bit binary installers. While you COULD compile the Python packages yourself, I recommend you do not.
Thus, compile all BCI2000 modules for 32-bit.

### Stop and Test

At this point you should test that BCPy2000 is working.
Run `$BCI2000PATH/src/contrib/BCPy2000/Merge.bat`
Then run `$BCI2000PATH/batch/PythonDemo1_Triangle.bat`

### Installing BCPyElectrophys dependencies
The extensions in this repo have additional dependencies depending on which extensions you intend to use.
These include [EERF](https://github.com/cboulay/EERF),
 my [caio package](https://github.com/cboulay/caio-python),
 my [magstim package](https://github.com/cboulay/magstim-python),
 and these may or may not have their own dependencies. See their respective pages for installation instructions.

### Downloading and installing BCPyElectrophys
You can either use git or download the tagged version.

Git:

Change to BCI2000's parent directory. `git clone git://github.com/cboulay/BCPyElectrophys.git`

Tag:

Click on Tags near the top right of this page. Download the source code in an archive.
Extract the contents of the archive (i.e., its root folder) into BCI2000's parent folder.
You should have \parent\BCI2000 and \parent\BCPyElectrophys-vx.x

If you are using the OgreRenderer, don't forget to `git submodule update --init`.

Test it by changing to the BCPyElectrophys folder and running `test.bat`.
Nothing is enabled by default, but you should be able to see the debug information showing task progression.

# Description

## TemplateApplication

This BCPy2000 application does not do much except define the phases of each trial
and call on the extensions.
The phases are: intertrial, baseline, gocue, task, response, stopcue
The duration of the phases can either be set by parameters
or they might be determined by events occuring in the extensions.

## GatingExtension

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

This extension enables continuous feedback of some signal. Feedback may be auditory,
visual (a bar, a cursor, the color of a circle), passive movement operated by a custom device we have,
or neuromuscular stimulation controlled by a custom device we have. Both the passive movement
and NMES devices require another Python package that I have. I have not published this
package because I am uncertain if it reveals any intellectual property. If you are
interested in this package then please contact me directly.

## ERPExtension

This extension enables storing of ERPs into a custom database, and then
possibly providing feedback about the amplitude of an ERP feature. This
extension requires my [EERF python](https://github.com/cboulay/EERF) repo.