from setuptools import setup, find_packages

setup(
	name='Design3-Driver',
	version='0.0.1',
	packages=find_packages(),
	install_requires=[
		'pyserial',
		'B1530Lib @ https://github.com/arenaudineau/B1530Lib/archive/refs/heads/main.zip',
		'controle_manip @ https://github.com/tvbv/controle_manip/archive/refs/heads/pip-ready.zip'
	]
)
