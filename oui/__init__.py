from typing import List

from oui import mcd, B1530Lib
from oui.mcd import State


###############################
# WGFMU Configuration Constants
# Empty

# Utils export from mcd
print_ports = mcd.MCDriver.print_ports
print_visa_dev = B1530Lib.print_devices

##########################
# class NewChipDriver
class NewChipDriver:
	"""
		New Chip Driver (TODO: the name)

		...
		Attributes
		----------
		_mcd: mcd.MCDriver
			The low-level driver used for the µc

		_b1530: B1530Lib.B1530
			The driver used to control the B1530
	"""

	def __init__(self, uc_pid = mcd.MCDriver.DEFAULT_PID, visa_addr = B1530Lib.B1530.DEFAULT_ADDR):
		"""
		Creates the driver.

		Details:
			It will search for the µc using the PID value 'DEFAULT_PID' or the one provided in argument.
			Takes the first found if many have the same PID.
			RAISE Exception if not found.

		Arguments:
			pid: optional, the pid to search for.
		"""
		self._mcd = mcd.MCDriver(uc_pid)

		try:
			self._b1530 = B1530Lib.B1530(addr=visa_addr)
		except Exception as e:
			self._mcd.ser.close()
			raise e
		
		self.reset_state()

	def reset_state(self):
		"""
		Resets the state of the driver, to run after exception catching for example.
		"""
		self._mcd.flush_input()
		self._mcd.ack_mode(mcd.ACK_ALL)
		self._mcd.set_cs(mcd.CS.CARAC_EN, State.SET) # Enable CARAC MODE

	##### µC-RELATED METHODS #####
	# EMPTY

	##### B1530-RELATED METHODS #####
	def configure_wgfmu(self, config):
		"""
		Configures the WGFMUs with the configuration provided
		
		Parameters:
			config: The configuration to apply:
				* Empty
				
		Details:
			b1530.chans
		"""
		if self._last_wgfu_config == config:
			return
		
		self._last_wgfu_config = config

		#self._b1530.reset_configuration()
		chan = self._b1530.chan

		# TODO: make this a list/dict?
		self._b1530.reset_configuration()
		self._b1530.configure()

	##### HIGH-LEVEL MEMRISTOR MANIPULATION METHODS #####
	# Empty
		


