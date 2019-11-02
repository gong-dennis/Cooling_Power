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
    def __init__(self, serialPort = '/dev/cu.usbmodem14201', serialBaud = 9600, plotLength = 1000, dataNumBytes = 2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = bytearray(dataNumBytes)

        self.data = []
        for i in range(2):
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))

        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.previousTimer = 0
        self.first = 0
        self.firstT = 0
        self.prevT = 0

        self.csvData = []
        self.csvDataT = []
        self.csvDataTime = []

        self.trial = 0
        self.current = 0
        self.pressure = 0
       
        self.water = float(input("Input starting water mass (g): ")) 
        self.pressure = input("Input start pressure (psi): ")
            
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
            self.csvDataT.append(999999)
            self.csvDataTime.append(999999)
            self.first = currentTimer
            self.trial = 1

        if (self.trial == 1):
            
            self.previousTimer = currentTimer
            self.current = round(currentTimer - self.first, 2)
            timeText.set_text('Timer (s) = ' + str(self.current)) # Sets the timer on the screen
            if (self.current <= 0.2):
                self.firstT = temp

            temp = round((self.prevT + temp)/2, 2)
            self.prevT = round(temp, 2)

            if ((self.current / -1) != 0): # Make sure to keep consistent units
                value = ((temp - self.firstT) * self.water * 4.179)/(self.current * -1) # Calculates the value
                value = round(value, 2)

        self.data[0].append(value)    # we get the latest data point and append it to our array
        self.data[1].append(temp)

        lines[0].set_data(range(self.plotMaxLength), self.data[0])
        lineValueText[0].set_text('[' + lineLabel[0] + '] = ' + str(value))

        lines[1].set_data(range(self.plotMaxLength), self.data[1])
        lineValueText[1].set_text('[' + lineLabel[1] + '] = ' + str(temp))

        self.csvData.append(value)
        self.csvDataT.append(temp)
        self.csvDataTime.append(self.current)
 
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
            df = pd.DataFrame(self.csvData, columns = ['Cooling Power'])
            df['Time'] = self.csvDataTime
            df['Temperature'] = self.csvDataT
            df['Average Cooling Power'] = df['Cooling Power'].rolling(5).mean()
            df['Average Temperature'] = df['Temperature'].rolling(5).mean() 

            today = date.today()
            today_date = today.strftime("%b-%d-%Y")
            trial_num = input("Enter trial identifier: ")
            df.to_csv(today_date + '_Calorimetry_' + trial_num + '_' + self.pressure + 'psi.csv')
 
 
def main():
    # portName = 'COM5'     # for windows users
    portName = '/dev/cu.usbmodem14201'
    baudRate = 9600
    maxPlotLength = 2000
    dataNumBytes = 4        # number of bytes of 1 data point
    numPlots = 2 
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
    ax.set_xlabel("Time (1/10s)")
    ax.set_ylabel("Cooling Power (W)")
 
    lineLabel = ['Cooling Power (W)', 'Temperature (C)']
    style = ['r-', 'c-']
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []

    for i in range(numPlots):
        lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.50, 0.90-i*0.05, '', transform=ax.transAxes))

    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
 
    plt.legend(loc="upper left")
    plt.show()
 
    s.close()
 
 
if __name__ == '__main__':
    main()
