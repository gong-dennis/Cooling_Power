#!/usr/bin/env python
 
from threading import Thread
from datetime import date
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import pandas as pd

 
 
class serialPlot:
    def __init__(self, serialPort = '/dev/cu.usbmodem14401', serialBaud = 9600, plotLength = 1000, dataNumBytes = 2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = bytearray(dataNumBytes)
        self.data = collections.deque([0] * plotLength, maxlen=plotLength)
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.csvData = []
        self.first = 0
        self.trial = 0
        self.current = 0
        
        self.water = float(input("Input water mass (g): "))
        
        self.start_temp = float(input("Input initial water temperature (C): "))
            
        print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
 
    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            self.first = time.perf_counter()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)
 
    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        temp,  = struct.unpack('f', self.rawData)    # use 'h' for a 2 byte integer 
        temp = round(temp, 2)
        currentTimer = round(time.perf_counter(), 2)
        value = 0
        if (temp == -99):
            self.csvData.append(999999)
            self.first = currentTimer
            self.trial = 1
        if (self.trial == 1):
            self.plotTimer = int((currentTimer - self.previousTimer))     # the first reading will be erroneous (1/10 second)
            self.previousTimer = currentTimer
            self.current = round(currentTimer - self.first, 2)
            timeText.set_text('Timer = ' + str(self.current) + '1/10s')
            if (((currentTimer - self.first) / -1) != 0): # Make sure to keep consistent units
                value = ((temp - self.start_temp) * self.water * 4.179)/((currentTimer - self.first) / -1) # in seconds
                value = round(value, 2)
        self.data.append(value)    # we get the latest data point and append it to our array
        lines.set_data(range(self.plotMaxLength), self.data)
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value))
        self.csvData.append(self.data[-1])
 
    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            self.serialConnection.readinto(self.rawData)
            self.isReceiving = True
            #print(self.rawData)
 
    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')

        save = input("Save data (Y/N)? ")
        if (save == "Y"):
            df = pd.DataFrame(self.csvData)
            today = date.today()
            today_date = today.strftime("%b-%d-%Y")
            trial_num = input("Enter trial identifier: ")
            df.to_csv(today_date + '_Calorimetry_' + trial_num + '.csv')
 
 
def main():
    # portName = 'COM5'     # for windows users
    portName = '/dev/cu.usbmodem14401'
    baudRate = 9600
    maxPlotLength = 2000
    dataNumBytes = 4        # number of bytes of 1 data point
 
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)   # initializes all required variables
    s.readSerialStart()                                               # starts background thread
 
    # plotting starts below
    pltInterval = 100   # Period at which the plot animation updates
    xmin = 0
    xmax = 2000
    ymin = -(1)
    ymax = 150
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Cooling Power over Time')
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Cooling Power (W)")
 
    lineLabel = 'Cooling Power (W)'
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = ax.plot([], [], label=lineLabel)[0]
    lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
 
    plt.legend(loc="upper left")
    plt.show()
 
    s.close()
 
 
if __name__ == '__main__':
    main()
