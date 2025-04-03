#from SEES import Sensors
from datetime import datetime
from SENSORS import Sensors
import time
import csv
import os

if __name__ == "__main__":
	sensors = Sensors()

	fields:list = ["Time", "Soil Moisture", "Temperature", "Nh3", "Humidity", "Pressure", "Light", "Oxidizing", "Reducing"] 
	data_collection_inteval:float = 0.1 # time in secconds

	cache = []
	file_name = "Data.csv"

	if not os.path.isfile(file_name):
		with open(file_name, "w+") as f:
			write = csv.writer(f)
			write.writerow(fields)
			write.writerow([])
	
	
	start = time.time()
	while True:
		try:
			data = []
			
			start_time:float = time.monotonic()
			data.append(datetime.now().strftime('%d-%H:%M:%S.%f'))
			data.append(sensors.soil_moisture())
			data.append(sensors.temp())
			data.append(sensors.nh3())
			data.append(sensors.humidity())			
			data.append(sensors.pressure())
			data.append(sensors.light())
			data.append(sensors.oxidising())
			data.append(sensors.reducing())
			
			cache.append(data)

			if len(cache) == 15:
				with open("Data.csv", "a") as f:
					write = csv.writer(f)
					write.writerows(cache)
				cache = []

			try:
				time_to_sleep = data_collection_inteval - ((time.monotonic() - start_time) % 60.0) # 1 seccond compensated sleep time
				elapsed_time = time.time() - start
				
				time.sleep(time_to_sleep)

			except KeyboardInterrupt:
				exit()
			
		except KeyboardInterrupt:
			exit()
	
