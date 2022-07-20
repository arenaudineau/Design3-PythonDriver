# Design3-PythonDriver
Python drivers to control Design 3, developped @ C2N 

## Installation
This library requires:  
* ⚠️ 32 bits version of Python
* `pyserial` version 3.5 or any other compatible version
* `pyvisa` version 1.12.0 or any other compatible version
* `pandas` version 1.4.2 or any other compatible version
* The associated NI-VISA drivers, see [the official doc](https://pyvisa.readthedocs.io/en/latest/faq/getting_nivisa.html#faq-getting-nivisa). (⚠️ 32 bits version required)

### Global installation
1. Download and install the NI-VISA drivers
2. `B1530driver.py` and `B1530ErrorModule.py` are licensed and cannot be shared on GitHub, they are therefore missing on this repo.  
You must add their path to the environment variable PYTHONPATH. See the end of this README for instructions.  
3. Run the command `pip install https://github.com/arenaudineau/Design3-PythonDriver/archive/refs/heads/main.zip`

You can now use `d3` as a regular library, by using `import d3` in any directory on the computer.

### Extending the driver
You need to create a fork of this repo, `git clone` your fork onto your local computer and run `pip install -e .` in the root of the downloaded folder.  
You can know use `d3` in any directory of the computer and any changes in the sources will be taken into account. 

### Adding path to PYTHONPATH
`Win + R` -> Write "SystemPropertiesAdvanced", Enter => Environment Variables... => User Variables for XXX ;  
If `PYTHONPATH` exists, edit it and append the path to B1530driver files ;  
Otherwise, create it.

# Getting Started
See notebook [here](https://gist.github.com/arenaudineau/42e6704368cb00af8836932d38dd419e).
