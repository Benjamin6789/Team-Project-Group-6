from enviroplus import gas
from bme280 import BME280
from smbus2 import SMBus

from pms5003 import PMS5003, ReadTimeoutError

import time

try:
	from ltr559 import LTR559
	ltr559 = LTR559()
except ImportError:
	import ltr559


class Sensors:
	def __init__(self):
		gas.enable_adc()
		gas.set_adc_gain(4.096)

		# init tempriture / pressure / humidity sensor
		bus = SMBus(1)
		self.bme280 = BME280(i2c_dev=bus)
		
		# get_lux() function returns 0 the fist 2 or more times when called
		lux:float = ltr559.get_lux()
		while lux == 0:
			lux = ltr559.get_lux()


	def nh3(self) -> float:
		nh3:float = gas.read_nh3()		
		nh3 = round(nh3, 2)
		return nh3
		
	def reducing(self) -> float:
		reducing:float = gas.read_reducing() 
		reducing = round(reducing, 2)
		return reducing
		
	def oxidising(self) -> float:
		oxidising:float = gas.read_oxidising()
		oxidising = round(oxidising, 2)
		return oxidising
		
	def light(self) -> float:
		lux = ltr559.get_lux()
		lux = round(lux, 2)
		return lux

	def temp(self) -> float:
		raw_temp:float = self.bme280.get_temperature()
		raw_temp = round(raw_temp, 2)
		return raw_temp
		
	def pressure(self) -> float:
		pressure:float = self.bme280.get_pressure()
		pressure = round(pressure, 2)
		return pressure
		
	def humidity(self) -> float:
		humidity:float = self.bme280.get_humidity()
		humidity = round(humidity, 2)
		return humidity
		
	def soil_moisture(self) -> float:
		soil = gas.read_adc()
		return soil
		

