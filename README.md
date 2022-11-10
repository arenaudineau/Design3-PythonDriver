# Design3-PythonDriver
Python drivers to control Design 3, developped @ C2N 

## Installation
1. Download and install the NI-VISA drivers, see [the official doc](https://pyvisa.readthedocs.io/en/latest/faq/getting_nivisa.html#faq-getting-nivisa). (⚠️ 32 bits version required)
2. `B1530driver.py` and `B1530ErrorModule.py` are licensed and cannot be shared on GitHub, they are therefore missing on this repo.  
You must add their path to the environment variable PYTHONPATH. See the end of this README for instructions.  


### Development installation
Download this repo at this [link](https://github.com/arenaudineau/Design3-PythonDriver/archive/refs/heads/main.zip), or clone it locally using `git` : `git clone https://github.com/arenaudineau/Design3-PythonDriver`.

Then, install the requirements using `pip install -r requirements.txt`.

Then, see the Getting Started section below.

### Global installation
Run the command `pip install https://github.com/arenaudineau/Design3-PythonDriver/archive/refs/heads/main.zip`

You can now use `d3` as a regular library, by using `import d3` in any directory on the computer.

### Adding path to PYTHONPATH
`Win + R` -> Write "SystemPropertiesAdvanced", Enter => Environment Variables... => User Variables for XXX ;  
If `PYTHONPATH` exists, edit it and append the path to B1530driver files ;  
Otherwise, create it.

## Getting Started
See notebook [here](d3.ipynb).
