#from enviroplus import gas
#from bme280 import BME280
#from smbus2 import SMBus

#from pms5003 import PMS5003, ReadTimeoutError

import random
import time
"""
try:
	from ltr559 import LTR559
	ltr559 = LTR559()
except ImportError:
	import ltr559
"""

class Sensors:
	def __init__(self):
		pass
	def nh3(self) -> float:
		return round(random.uniform(0, 100), 2)
	def reducing(self) -> float:
		return round(random.uniform(0, 100), 2)
	def oxidising(self) -> float:
		return round(random.uniform(0, 100), 2)		
	def light(self) -> float:
		return round(random.uniform(0, 100), 2)
	def temp(self) -> float:
		return round(random.uniform(0, 100), 2)		
	def pressure(self) -> float:
		return round(random.uniform(0, 100), 2)		
	def humidity(self) -> float:
		return round(random.uniform(0, 100), 2)		
	def soil_moisture(self) -> float:
		return round(random.uniform(0, 100), 2)	
		

