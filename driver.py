from SENSORS import Sensors
import time

sensors = Sensors()

secconds_counter:int = 0
while True:
	try:
		start_time:float = time.monotonic()
		secconds_counter += 1
		
		print("soil moisture", sensors.soil_moisture() , "%") # out of 100% 
		print("temp", sensors.temp())		  	# 22.63
		print("nh3", sensors.nh3())				# 204.38
		
		
		if secconds_counter % 5 == 0: # executes evrey 5 seconds
			print("humidity", sensors.humidity()) 	# 79.19
			print("pressure", sensors.pressure()) 	# 677.44
		
		if secconds_counter % 10 == 0: # executes evrey 10 seconds
			print("light", sensors.light())		  	# 15.4
			print("oxidising", sensors.oxidising()) # 19030.45
			print("reducing", sensors.reducing())	# 1249.07
			
			secconds_counter:int = 0
			
		print()
		
		try:
			time_to_sleep = 1.0 - ((time.monotonic() - start_time) % 60.0) # 1 seccond compensated sleep time
			time.sleep(time_to_sleep)
			
		except KeyboardInterrupt:
			exit()
		
	except KeyboardInterrupt:
		exit()
	
