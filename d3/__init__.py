from typing import List

from d3 import mcd, B1530Lib
from d3.mcd import State #, add other usefull import here

import functools as ft

###############################
# WGFMU Configuration Constants
# Empty

# Utils export from mcd
print_ports = mcd.MCDriver.print_ports
print_visa_dev = B1530Lib.print_devices

######################
# class Design3Driver
######################
class Design3Driver:
	"""
		Design3 Driver

		...
		Attributes
		----------
		_mcd: mcd.MCDriver
			The low-level driver used for the µc

		_b1530: B1530Lib.B1530
			The driver used to control the B1530

		_last_wgfu_config: int
			Stores the last operation performed, not to reconfigure everything if it is the same (see 'WGFMU Configuration Constants')
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
		self._mcd.flush_input() # Flush any remaning inputs stuck in the buffer
		self._mcd.ack_mode(mcd.ACK_ALL) # Enable ACK for every procedure commands
		self._last_wgfu_config = -1 # Initially, no WGFMU Configuration

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
		chan = self._b1530.chan

		# self._b1530.reset_configuration() # If required (e.g. when different channels wave/meas is used for different configurations)

		##### HERE #####

		################

		self._b1530.configure()

	##### HIGH-LEVEL ARRAY MANIPULATION METHODS #####
	@staticmethod
	def ternary_to_repr(t: int):
		return {
			 1: 0b10,
			 0: 0b00,
			-1: 0b01,
		}[t]

	@staticmethod
	def binary_to_repr(b: int):
		return {
			 1: 0b1,
			-1: 0b0,
			 0: 0b0, # == mcd.State.RESET
		}[b]

	def fill(self, values):
		"""
		Fills in the array
		
		Parameters:
			values: List[List[int]]
			Details:
				2D array of '1', '-1' or '0'
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7], # row 1
					...,
				[col0, col1, ..., col7]] # row 7
		"""
		values = list(ft.reduce(
				lambda reduced_rows, rows: reduced_rows + list(map(self.ternary_to_repr, rows)),
				values,
				[],
		))
		self._mcd.fill(values)
		


