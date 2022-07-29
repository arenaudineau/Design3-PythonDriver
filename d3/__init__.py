from d3 import mcd
from d3.mcd import State #, add other usefull import here
import B1530Lib
import lab.keith2230GDriver as kdriver

import numpy as np

import functools as ft
from typing import List
from time import sleep

###############################
# WGFMU Configuration Constants
WGFMU_CONFIG_SENSE = 0

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

		_kdriver: kdriver.Keith2230G
			The driver used to control the 2230G

		_last_wgfu_config: int
			Stores the last operation performed, not to reconfigure everything if it is the same (see 'WGFMU Configuration Constants')
	"""

	K2230G_DEFAULT_ADDR = "GPIB::6::INSTR"

	def __init__(self, uc_pid = mcd.MCDriver.DEFAULT_PID, b1530_addr = B1530Lib.B1530.DEFAULT_ADDR, k2230g_addr = K2230G_DEFAULT_ADDR):
		"""
		Creates the driver.

		Details:
			* It will search for the µc using the PID value 'DEFAULT_PID' or the one provided in argument.
			Takes the first found if several have the same PID.
			* It will search for the B1530 using the visa address 'B1530.DEFAULT_ADDR' or the one provided in argument.
			* It will search for the K2230G using the visa address 'K2230G_DEFAULT_ADDR' or the one provided in argument.
			RAISE Exception if not found.

		Arguments:
			pid: optional, the pid to search for.
			b1530_addr: optionnal, the visa addr to search for the B1530. If None, do not use the B1530
			k2230g_addr: optionnal, the visa addr to search for the Keithley 2230G. If None, do not use K2230G
		"""
		self._mcd     = None
		self._b1530   = None
		self._kdriver = None

		if uc_pid is not None:
			try:
				self._mcd = mcd.MCDriver(uc_pid)
			except Exception as e:
				del self
				raise e

		if b1530_addr is not None:
			try:
				self._b1530 = B1530Lib.B1530(addr=b1530_addr)
			except Exception as e:
				del self
				raise e

		if k2230g_addr is not None:
			try:
				self._kdriver = kdriver.Keith2230G(adress=k2230g_addr, silence_initial_measurements=True)
			except Exception as e:
				del self
				raise e
		
		self.k2230g_chans = {
			'VDD':  'CH1',
			'VDDC': 'CH2',
			'VDDR': 'CH3',
		}
		
		self.reset_state()

	def __del__(self):
		if self._kdriver is not None:
			self._kdriver = None
			print("Closed Keith2230G")

		if self._b1530 is not None:
			self._b1530.__del__() # Because somehow del self._b1530 doesnt work
			self._b1530 = None
			print("Closed B1530")
		
		if self._mcd is not None:
			self._mcd.__del__() # Because somehow del self._b1530 doesnt work
			self._mcd = None
			print("Closed MCDriver")

	def reset_state(self):
		"""
		Resets the state of the driver, to run after exception catching for example.
		"""
		self._mcd.flush_input() # Flush any remaning inputs stuck in the buffer
		self._mcd.ack_mode(mcd.ACK_ALL) # Enable ACK for every procedure commands

		# Enable all three channels of the DC Power Supply
		if self._kdriver is not None:
			self._kdriver.set_channel_output(self.k2230g_chans['VDD'],  1)
			self._kdriver.set_channel_output(self.k2230g_chans['VDDC'], 1)
			self._kdriver.set_channel_output(self.k2230g_chans['VDDR'], 1)

			self.set_voltages({'VDD': 0.0, 'VDDR': 0.0, 'VDDC': 0.0})
		
		self._last_wgfu_config = -1 # Initially, no WGFMU Configuration
		self.discharge_time = None
		self.precharge_time = None
		self.interval       = 20e-6
		self.clk_len        = 15e-6 # Quite long length and interval to let the µc react to the clk pulse

	##### µC-RELATED METHODS #####
	# EMPTY

	##### B1530-RELATED METHODS #####
	def configure_wgfmu_default(self, measure = False):
		"""
		Configures the WGFMUs by default

		Parameters:
			measure: bool : Measure the signals generated
		"""
		# Reconfigure only if the configuration has changed
		if self._last_wgfu_config == (self.precharge_time, self.discharge_time, self.interval, self.clk_len):
			return
		self._last_wgfu_config = (self.precharge_time, self.discharge_time, self.interval, self.clk_len)

		if self.discharge_time is None or self.precharge_time is None:
			raise ValueError("discharge_time or precharge_time not set")

		chan = self._b1530.chan

		bit_in = chan[1]
		cwl    = chan[2]
		csl    = chan[3]
		clk    = chan[4]

		bit_in.name = 'bit_in'
		cwl.name    = 'cwl'
		csl.name    = 'csl'
		clk.name    = 'clk'

		bit_in.wave = B1530Lib.Pulse(
			voltage  = 3.3,
			interval = 1e-7,
			edges    = 1e-8,
			length   = 1.4 * (self.precharge_time + self.discharge_time) # !! 1.2
		)

		cwl.wave = bit_in.wave.centered_on(
			voltage  = 3.3,
			length   = self.precharge_time + self.discharge_time,
			wait_end = 0,
		)

		csl.wave = cwl.wave.copy(
			voltage  = 3.3,
			length   = self.precharge_time,
			wait_end = self.discharge_time,
		)

		clk.wave = B1530Lib.Pulse(
			voltage    = 3.3,
			edges      = 1e-8,
			length     = self.clk_len,
			wait_begin = cwl.wave.get_total_duration(),# - cwl.wave.trail,
			wait_end   = 0,
		)
		
		# Repeat once again control signals, but this time with bit_in at GND 
		interval = max(0, self.interval - cwl.wave.wait_begin)
		cwl.wave.append_wait_end(new_total_duration = clk.wave.get_total_duration() + interval)
		csl.wave.append_wait_end(new_total_duration = clk.wave.get_total_duration() + interval)
		clk.wave.append_wait_end(new_total_duration = clk.wave.get_total_duration() + interval)

		# See https://github.com/arenaudineau/B1530Lib/wiki
		#bit_in = B1530Lib.Waveform(
		#	[
		#		[0],
		#		[],
		#		[],
		#		[],
		#	]
		#)

		cwl.wave.repeat(1)
		csl.wave.repeat(1)
		clk.wave.repeat(1)
		
		bit_in.wave.append_wait_end(new_total_duration = clk.wave.get_total_duration())

		for c in chan.values():
			c.wave \
				.repeat(8 - 1) \
				.prepend_wait_begin(wait_time = 0.05) # Let the µc init

		if measure:
			for c in self._b1530.chan.values():
				c.measure_self(
					average_time=0.1e-7,
					sample_interval=0.1e-7,
					ignore_edges=False,
					ignore_settling=False,
				)

		bit_in.wave.force_fastiv = True
		cwl.wave.force_fastiv    = True
		csl.wave.force_fastiv    = True
		clk.wave.force_fastiv    = True
		self._b1530.configure()

	##### Keith2230G-RELATED METHODS #####
	def set_voltages(self, voltages, tolerance=0.05, wait_time=0.3):
		"""
		Sets the voltages provided and waits for the values to be settled.

		Parameters:
			voltages: Dict specifying the channel name as a key and the wanted voltage as a value
			tolerance: float : The tolerated voltage difference
			wait_time: float : Wait time between each actual voltage queries 
		"""
		for chan_name, voltage in voltages.items():
			chan = self.k2230g_chans[chan_name]
			self._kdriver.set_channel_voltage(chan, voltage)

		def voltage_settled():
			settled = True
			for chan_name, voltage in voltages.items():
				chan = self.k2230g_chans[chan_name]
				actual_voltage = float(self._kdriver.get_channel_voltage(chan))
				settled &= (abs(actual_voltage - voltage) < tolerance)

			return settled

		while not voltage_settled():
			sleep(wait_time)
		sleep(2*wait_time) # Let the voltage stabilize

	##### HIGH-LEVEL ARRAY MANIPULATION METHODS #####
	@staticmethod
	def ternary_to_repr(t: int):
		return {
			 1: 0b10, # HRS-LRS
			 0: 0b00, # HRS-HRS
			-1: 0b01, # LRS-HRS
		}[t]

	@staticmethod
	def flatten_array(arr: List[List[int]], m = lambda x: x) -> List[int]:
		"""
		Returns a 1D flatten array from a 2D one, with optionally a function to map.

		Parameters:
			arr: List[List[int]] : The 2D array to flatten
			m: func : The function to map to individual values [identity by default]
		"""
		return \
			list(ft.reduce(
					lambda reduced_rows, rows:
						reduced_rows + list(map(m, rows)),
					arr,
					[],
			))
	
	def set(self, values: List[List[int]], VDDR = 3, VDDC = 3.5):
		"""
		Sets the selected memristors

		Parameters:
			values: List[List[int]]
			Details:
				2D array of binary values '0bXY'
					If X = '1', SET R, otherwise do not change R state
					If Y = '1', SET Rb, otherwise do not change Rb state
					If XY = '00', do not change the cell state
				
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7],  # row 1
					...,
				[col0, col1, ..., col7]]  # row 7

			VDDR: float, 3 by default
			VDDC: float, 3.5 by default
		"""
		if self._kdriver is not None:
			self.set_voltages({'VDDR': VDDR, 'VDDC': VDDC})
		self._mcd.set(*self.flatten_array(values))

	def reset(self, values: List[List[int]], VDDR = 5, VDDC = 4.5):
		"""
		Resets the selected memristors

		Parameters:
			values: List[List[int]]
			Details:
				2D array of binary values '0bXY'
					If X = '1', RESET R, otherwise do not change R state
					If Y = '1', RESET Rb, otherwise do not change Rb state
					If XY = '00', do not change the cell state
				
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7],  # row 1
					...,
				[col0, col1, ..., col7]]  # row 7

			VDDR: float, 5 by default
			VDDC: float, 4.5 by default
		"""
		if self._kdriver is not None:
			self.set_voltages({'VDDR': VDDR, 'VDDC': VDDC})
		self._mcd.reset(*self.flatten_array(values))

	def form(self, values: List[List[int]], VDD = 1.2, VDDR = 3, VDDC = 3):
		"""
		Forms the selected memristors

		Parameters:
			values: List[List[int]]
			Details:
				2D array of binary values '0bXY'
					If X = '1', FORM R, otherwise do not change R state
					If Y = '1', FORM Rb, otherwise do not change Rb state
					If XY = '00', do not change the cell state
				
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7],  # row 1
					...,
				[col0, col1, ..., col7]]  # row 7

			VDDR: float, 3 by default
			VDDC: float, 3 by default
		"""
		self.set_voltages({'VDD': VDD, 'VDDR': VDDR, 'VDDC': VDDC})
		self._mcd.set(*self.flatten_array(values)) # FORM has the same control signals as SET

	def fill(self, values, otp=False):
		"""
		Fills in the array
		
		Parameters:
			values: List[List[int]]
			Details:
				2D array of '1', '-1' or '0'
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7],  # row 1
					...,
				[col0, col1, ..., col7]]  # row 7

			otp: bool : Fill in OTP mode or not [False by default]
			Details:
				If otp = False, sets or resets all the memristors
				If otp = True, forms only the memristors to set, leaves untouched to ones to reset
		"""
		if len(values) != 8 and len(values[0]) != 8:
			raise ValueError("Expected 8x8 array")

		set_values, reset_values = [], []
		for row in values:
			set_value_col   = []
			reset_value_col = []
			for v in row:
				v = {
					 1: 0b01, #  1 = HRS-LRS = RST-SET
					-1: 0b10, # -1 = LRS-HRS = SET-RST
					 0: 0b00, #  0 = HRS-HRS = RST-RST
				}[v]

				set_val   = v ^ 0b00
				reset_val = v ^ 0b11

				set_value_col.append(set_val)
				reset_value_col.append(reset_val)

			set_values.append(set_value_col)
			reset_values.append(reset_value_col)

		if otp: # If we are in OTP mode, we form the memristors to SET and leave to other unformed
			self.form(set_values)
		else: # Otherwise, we set to memristors to SET and RESET to others
			self.set(set_values)
			self.reset(reset_values)

	def sense(self, measure_pulses=False, sense_uc=False, VDD=1.2, VDDR=2.5, VDDC=1.2):
		"""
		Reads out the array

		Parameters:
			measure_pulses: bool : Make a B1530 measurement of the pulses applied [False by default]
			sense_uc: bool : Sense using the microcontroller only [False by default]

		Returns:
			values: List[List[int]]
			Details:
				2D array of integers '0b00', '0b10' or '0b01' (or '0b11' but that shouldn't happen)
				[[col0, col1, ..., col7], # row 0
				[col0, col1, ..., col7],  # row 1
					...,
				[col0, col1, ..., col7]]  # row 7
		"""
		if self._kdriver is not None:
			self.set_voltages({'VDD': VDD, 'VDDR': VDDR, 'VDDC': VDDC})
		
		if self._b1530 is not None and not sense_uc:
			self.configure_wgfmu_default(measure_pulses)
			self._b1530.exec(wait_until_completed = False) # Does not wait for completion because we want to run µc sense at the same time
			
			values = self._mcd.sense() # Get array of bytes

		else:
			values = self._mcd.sense_uc() # Get array of bytes
		
		values = np.array([b for b in values], dtype=int) # Convert array of bytes into array of integers
		values = values.reshape(8, 8)                     # Shape 1D array of size 64 to 8x8 2D array
		
		return values