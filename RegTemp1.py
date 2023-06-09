import csv
import subprocess
import time
from w1thermsensor import W1ThermSensor,Sensor
from timeloop import Timeloop
from datetime import timedelta
#from pynput.keyboard import Key, Listener
from pynput import keyboard 

#-------------------------------------------------------------------------------
# Initialize globalish stuff

tl = Timeloop()
sensor = W1ThermSensor()    # handle to an individual sensor
sensors = W1ThermSensor.get_available_sensors([Sensor.DS18B20]) # list of all sensors attached
lastReadings = []           # last readings taken from all sensors
same = 0                    # keep track of # same temp readings

driveEnable = False         # If True enable drive copy during test
driveRunning = 0            # global to indicate if drive is running
stop = 15                   # global # times for d64 copy then stop



#-------------------------------------------------------------------------------
# Function definitions

# Create a CSV file to hold our readings, and write out header
def makeCSV(fName):
    csv_file = open(fName + ".csv", 'w')
    csv_writer = csv.writer(csv_file)
    
    # Dump sensor serial numbers first
    header = []
    for sensor in sensors:
        header.append(sensor.id)

    print(header)
    csv_writer.writerow(header)

    # Create a header for out CSV log file with sensor ser# and start time
    header = ["Internal","External","Running","Time","Date"]
    print(header)
    csv_writer.writerow(header)

    return csv_writer


@tl.job(interval=timedelta(seconds=2))
def readTemp_10s():

    global lastReadings
    global same
    global csv_writer
    readings = []       # List of current readings for each sensor
    index = 0
    diff = False

    # If this reading is different from the last set diff = True
    for sensor in sensors:
        temp = sensor.get_temperature()
        if (temp != lastReadings[index]):
            diff = True
        readings.append(temp)
        index += 1

    readings.append(driveRunning)
    readings.append(time.strftime('%H:%M:%S', time.localtime()))
    readings.append(time.strftime('%a, %d %b %Y', time.localtime()))

    # If this reading different from last and we skipped writing 2 or more
    # reeadings then first write out last reading, then write out current
    # reading. This provides the data point just before reading changed.
    if diff:
        if same > 1:
            print(lastReadings)
            csv_writer.writerow(lastReadings)
        print(readings)
        csv_writer.writerow(readings)
        same = 0
    else:
        # Just showing for debugging output in term window
        same += 1
        print(str(readings) + ' Same:' + str(same))

    lastReadings = readings #save last set of sensor data output


# OpenCMB process
@tl.job(interval=timedelta(seconds=240))
def start1541_240s():
    
    global driveEnable
    global driveRunning
    global stop
    
    #result = subprocess.run(["cbmctrl detect"], shell=True, capture_output=True, text=True)
    #print(result.stdout)
    #print("OpenCBM process")

    if driveEnable:
        print("Starting D64 copy:" + (time.strftime('%H:%M:%S', time.localtime())))
        result = subprocess.run(["d64copy Jumpman.d64 8"], shell=True, capture_output=True, text=True)
        print(result.stdout)
        print("Copy done: " + (time.strftime('%H:%M:%S', time.localtime())))

    driveRunning ^= 1
    stop -= 1
    print("stop = " + str(stop))

# Function definitions
#------------------------------------------------------------------------------- 
    

#------------------------------------------------------------------------------- 
# MAIN

csv_writer = makeCSV("Test")            # Name of CSV file created
driveEnable = False                     # Enable D64 copying during test

# Seed the lastReadings list with zeros
for sensor in sensors:                  # Make sure our list starts with defaults
    lastReadings.append(0)

tl.start()

# End when ESC key pressed or collection time out
while 1:
    with keyboard.Events() as events:
        event = events.get(60.0)

        if event is not None:
            if event.key == keyboard.Key.esc:
                tl.stop()
                break

        if stop <= 0:
            tl.stop()
            break


print("end")

# MAIN
#------------------------------------------------------------------------------- 
