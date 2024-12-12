<div style="margin-bottom: 20px; text-align: center">
<a href="https://spectrum-instrumentation.com">
    <img src="https://spectrum-instrumentation.com/img/logo-complete.png"  width=400 />
</a>
</div>

# spcm-dds-control
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Graphical User Interface (GUI) for controlling Direct-Digital-Synthesis (DDS) functionality of the Arbitrary Waveform Generators (AWG) and DDS cards of Spectrum Instrumentation.

# Supported devices

See the [SUPPORTED_DEVICES.md](https://github.com/SpectrumInstrumentation/spcm-dds-control/blob/master/SUPPORTED_DEVICES.md) file for a list of supported devices.

# Requirements
[![Static Badge](https://img.shields.io/badge/spcm-1.4.5+-blue)](https://github.com/SpectrumInstrumentation/spcm)
[![Static Badge](https://img.shields.io/badge/PyQt-5.15+-green)](https://www.riverbankcomputing.com/software/pyqt/)


`spcm-dds-control` requires the Spectrum Instrumentation [driver](https://spectrum-instrumentation.com/support/downloads.php) which is available for Windows and Linux. 
Please have a look in the manual of your product for more information about installing the driver on the different plattforms.

# Installation and dependencies

## Download and install Python
Start by installing [Python 3.9 or higher](https://www.python.org/downloads/).

## Create a virtual environment
In the main folder, the folder in which this README recides, create a virtual environment:

Under Linux or GitBash (Windows):
```bash
$ python -m venv .venv
```

activate the virtual environment and install all the required packages:
```bash
$ source .venv/Scripts/activate
$ pip install -r requirements.txt
```

you're all setup to run the program!

# Running the program

In the virtual environement, execute the following command to start the GUI program:

```bash
$ python main.py
```

You should see the GUI window appear.

# Demo devices
To test the Spectrum Instrumentation API with user code without hardware, the Control Center gives the user the option to create [demo devices](https://spectrum-instrumentation.com/support/knowledgebase/software/How_to_set_up_a_demo_card.php). These demo devices can be used in the same manner as real devices. Simply change the device identifier string to the string as shown in the Control Center.

# Documentation
Please see the hardware user manual of your specific card for more information about the available functionality.