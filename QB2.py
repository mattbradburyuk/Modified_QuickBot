#!/usr/bin/python
"""
@modified QuickBot class to include using pru to read wheel encoders 

author: Matthew bradbury 

based on original QuickBot.py class from: 
@author Rowland O'Flaherty (rowlandoflaherty.com)
@date 02/07/2014
@version: 1.0
@copyright: Copyright (C) 2014, Georgia Tech Research Corporation
see the LICENSE file included with this software (see LINENSE file)
"""

#  to do

# 1) modify physics of encoders


from __future__ import division
import sys
import time
import re
import socket
import threading
import numpy as np

import pypru as pp  # start_up_pru(), stop_pru(), get_pru_data()

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.ADC as ADC

# Constants
LEFT = 0
RIGHT = 1
MIN = 0
MAX = 1

MAP_SIZE = 4096

DEBUG = False

ADCTIME = 0.001


ADC_LOCK = threading.Lock()

## Run variables
RUN_FLAG = True
RUN_FLAG_LOCK = threading.Lock()


class QuickBot():
    """The QuickBot Class"""

    # === Class Properties ===
    # Parameters
    sampleTime = 20.0 / 1000.0

    # timing 
    sampleTime = 20.0/1000.0        #sample time of the update function
    pruCurrentTime = 0.0    # time of current last sample per pru
    pruPrevTime = 0.0       # time of previous last sample per pru
    pruTotalTime = 0.0      # total time since pru started per pru
    sysStartTime = 0.0      # system time when pru started
    sysTotalTime = 0.0      # total time since pru started per system

    # encoder buffer
    bufferLoc = 4    # initialise at start of sample data in buffer
    prevBufferLoc = 0

    #ticks
    prevLastTick = [0,0];
    runningAverage = [0.0,0.0];
    tickVel = [0,0]


    # Pins
    ledPin = 'USR1'

    # Motor Pins -- (LEFT, RIGHT)
    dir1Pin = ('P8_14', 'P8_12')
    dir2Pin = ('P8_16', 'P8_10')
    pwmPin = ('P9_16', 'P9_14')

    # ADC Pins
    irPin = ('P9_38', 'P9_40', 'P9_36', 'P9_35', 'P9_33')
    

    # Encoder counting parameter and variables
    ticksPerTurn = 4  # Number of ticks on encoder disc
    minPWMThreshold = [45, 45]  # Threshold on the minimum value to turn wheel



    # Constraints
    pwmLimits = [-100, 100]  # [min, max]

    # State PWM -- (LEFT, RIGHT)
    pwm = [0, 0]

    # State IR
    irVal = [0.0, 0.0, 0.0, 0.0, 0.0]
    ithIR = 0

    # State Encoder
    encTime = [0.0, 0.0]  # Last time encoders were read
    encPos = [0.0, 0.0]  # Last encoder tick position
    encVel = [0.0, 0.0]  # Last encoder tick velocity


    # Variables
    ledFlag = True
    cmdBuffer = ''

    # UDP
    baseIP = '192.168.7.1'
    robotIP = '192.168.7.2'
    port = 5005
    robotSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    robotSocket.setblocking(False)

    # === Class Methods ===
    # Constructor
    def __init__(self, baseIP, robotIP):

        # Initialize GPIO pins
        GPIO.setup(self.dir1Pin[LEFT], GPIO.OUT)
        GPIO.setup(self.dir2Pin[LEFT], GPIO.OUT)
        GPIO.setup(self.dir1Pin[RIGHT], GPIO.OUT)
        GPIO.setup(self.dir2Pin[RIGHT], GPIO.OUT)

        GPIO.setup(self.ledPin, GPIO.OUT)

        # Initialize PWM pins: PWM.start(channel, duty, freq=2000, polarity=0)
        PWM.start(self.pwmPin[LEFT], 0)
        PWM.start(self.pwmPin[RIGHT], 0)

        # Set motor speed to 0
        self.setPWM([0, 0])

        # Initialize ADC
        ADC.setup()


        # Set IP addresses
        self.baseIP = baseIP
        self.robotIP = robotIP
        self.robotSocket.bind((self.robotIP, self.port))

        

    # Getters and Setters
    def setPWM(self, pwm):
        # [leftSpeed, rightSpeed]: 0 is off, caps at min and max values

        self.pwm[LEFT] = min(
            max(pwm[LEFT], self.pwmLimits[MIN]), self.pwmLimits[MAX])
        self.pwm[RIGHT] = min(
            max(pwm[RIGHT], self.pwmLimits[MIN]), self.pwmLimits[MAX])

        # Left motor
        if self.pwm[LEFT] > 0:
            GPIO.output(self.dir1Pin[LEFT], GPIO.LOW)
            GPIO.output(self.dir2Pin[LEFT], GPIO.HIGH)
            PWM.set_duty_cycle(self.pwmPin[LEFT], abs(self.pwm[LEFT]))
        elif self.pwm[LEFT] < 0:
            GPIO.output(self.dir1Pin[LEFT], GPIO.HIGH)
            GPIO.output(self.dir2Pin[LEFT], GPIO.LOW)
            PWM.set_duty_cycle(self.pwmPin[LEFT], abs(self.pwm[LEFT]))
        else:
            GPIO.output(self.dir1Pin[LEFT], GPIO.LOW)
            GPIO.output(self.dir2Pin[LEFT], GPIO.LOW)
            PWM.set_duty_cycle(self.pwmPin[LEFT], 0)

        # Right motor
        if self.pwm[RIGHT] > 0:
            GPIO.output(self.dir1Pin[RIGHT], GPIO.LOW)
            GPIO.output(self.dir2Pin[RIGHT], GPIO.HIGH)
            PWM.set_duty_cycle(self.pwmPin[RIGHT], abs(self.pwm[RIGHT]))
        elif self.pwm[RIGHT] < 0:
            GPIO.output(self.dir1Pin[RIGHT], GPIO.HIGH)
            GPIO.output(self.dir2Pin[RIGHT], GPIO.LOW)
            PWM.set_duty_cycle(self.pwmPin[RIGHT], abs(self.pwm[RIGHT]))
        else:
            GPIO.output(self.dir1Pin[RIGHT], GPIO.LOW)
            GPIO.output(self.dir2Pin[RIGHT], GPIO.LOW)
            PWM.set_duty_cycle(self.pwmPin[RIGHT], 0)

    # Methods
    def run(self):
        global RUN_FLAG

        # start up pru taking encoder readings
        pp.start_up_pru()

        adj = 0.014;
        self.sysStartTime = time.time() + adj
        self.pruCurrentTime = self.sysStartTime

        
        try:
            while RUN_FLAG is True:
                self.update()

                # Flash BBB LED
                if self.ledFlag is True:
                    self.ledFlag = False
                    GPIO.output(self.ledPin, GPIO.HIGH)
                else:
                    self.ledFlag = True
                    GPIO.output(self.ledPin, GPIO.LOW)
                time.sleep(self.sampleTime)
        except:
            RUN_FLAG_LOCK.acquire()
            RUN_FLAG = False
            RUN_FLAG_LOCK.release()
            raise

        self.cleanup()
        return

    def cleanup(self):
        sys.stdout.write("Shutting down...")
        self.setPWM([0, 0])
        self.robotSocket.close()
        GPIO.cleanup()
        PWM.cleanup()
        if DEBUG:
            # tictocPrint()
            self.writeBuffersToFile()
        sys.stdout.write("Done\n")

    def update(self):
        self.readIRValues()
        self.readEncoderValues() 
        self.parseCmdBuffer()

    def parseCmdBuffer(self):
        global RUN_FLAG
        try:
            line = self.robotSocket.recv(1024)
        except socket.error as msg:
            return

        self.cmdBuffer += line

        bufferPattern = r'\$[^\$\*]*?\*'  # String contained within $ and * symbols with no $ or * symbols in it
        bufferRegex = re.compile(bufferPattern)
        bufferResult = bufferRegex.search(self.cmdBuffer)

        if bufferResult:
            msg = bufferResult.group()
            print msg
            self.cmdBuffer = ''

            msgPattern = r'\$(?P<CMD>[A-Z]{3,})(?P<SET>=?)(?P<QUERY>\??)(?(2)(?P<ARGS>.*)).*\*'
            msgRegex = re.compile(msgPattern)
            msgResult = msgRegex.search(msg)

            if msgResult.group('CMD') == 'CHECK':
                self.robotSocket.sendto('Hello from QuickBot\n',(self.baseIP, self.port))

            elif msgResult.group('CMD') == 'PWM':
                if msgResult.group('QUERY'):
                    self.robotSocket.sendto(str(self.pwm) + '\n',(self.baseIP, self.port))

                elif msgResult.group('SET') and msgResult.group('ARGS'):
                    args = msgResult.group('ARGS')
                    pwmArgPattern = r'(?P<LEFT>[-]?\d+),(?P<RIGHT>[-]?\d+)'
                    pwmRegex = re.compile(pwmArgPattern)
                    pwmResult = pwmRegex.match(args)
                    if pwmResult:
                        pwm = [int(pwmRegex.match(args).group('LEFT')),
                            int(pwmRegex.match(args).group('RIGHT'))]
                        self.setPWM(pwm)

            elif msgResult.group('CMD') == 'IRVAL':
                if msgResult.group('QUERY'):
                    reply = '[' + ', '.join(map(str, self.irVal)) + ']'
                    print 'Sending: ' + reply
                    self.robotSocket.sendto(reply + '\n', (self.baseIP, self.port))

            elif msgResult.group('CMD') == 'ENVAL':
                if msgResult.group('QUERY'):
                    reply = '[' + ', '.join(map(str, self.encPos)) + ']'
                    print 'Sending: ' + reply
                    self.robotSocket.sendto(reply + '\n', (self.baseIP, self.port))

            elif msgResult.group('CMD') == 'ENVEL':
                if msgResult.group('QUERY'):
                    reply = '[' + ', '.join(map(str, self.encVel)) + ']'
                    print 'Sending: ' + reply
                    self.robotSocket.sendto(reply + '\n', (self.baseIP, self.port))

            elif msgResult.group('CMD') == 'RESET':
                self.encPos[LEFT] = 0.0
                self.encPos[RIGHT] = 0.0
                print 'Encoder values reset to [' + ', '.join(map(str, self.encVel)) + ']'

            elif msgResult.group('CMD') == 'UPDATE':
                if msgResult.group('SET') and msgResult.group('ARGS'):
                    args = msgResult.group('ARGS')
                    pwmArgPattern = r'(?P<LEFT>[-]?\d+),(?P<RIGHT>[-]?\d+)'
                    pwmRegex = re.compile(pwmArgPattern)
                    pwmResult = pwmRegex.match(args)
                    if pwmResult:
                        pwm = [int(pwmRegex.match(args).group('LEFT')),
                            int(pwmRegex.match(args).group('RIGHT'))]
                        self.setPWM(pwm)

                    reply = '[' + ', '.join(map(str, self.encPos)) + ', ' \
                        + ', '.join(map(str, self.encVel)) + ']'
                    print 'Sending: ' + reply
                    self.robotSocket.sendto(reply + '\n', (self.baseIP, self.port))

            elif msgResult.group('CMD') == 'END':
                RUN_FLAG_LOCK.acquire()
                RUN_FLAG = False
                RUN_FLAG_LOCK.release()

    def readIRValues(self):
        prevVal = self.irVal[self.ithIR]
        ADC_LOCK.acquire()
        self.irVal[self.ithIR] = ADC.read_raw(self.irPin[self.ithIR])
        time.sleep(ADCTIME)
        ADC_LOCK.release()

        if self.irVal[self.ithIR] >= 1100:
                self.irVal[self.ithIR] = prevVal

        self.ithIR = ((self.ithIR+1) % 5)


    def readEncoderValues(self):
        print 'readEncodervalues called'
        
        buffer = pp.get_pru_data()

        #update bufferLoc
        self.prevBufferLoc =  self.bufferLoc
        self.bufferLoc = buffer[0,0]

        # get new entries in buffer
        if self.bufferLoc > self.prevBufferLoc:
            print 'forwards from: ' + str(self.prevBufferLoc) +' to: ' + str(self.bufferLoc)
            lenNE = self.bufferLoc - self.prevBufferLoc
            newEntries = np.zeros((2,lenNE))
            newEntries[0] = buffer[0,self.prevBufferLoc: self.bufferLoc]
            newEntries[1] = buffer[1,self.prevBufferLoc: self.bufferLoc]

        else:
            print 'backwards from: ' + str(self.prevBufferLoc) +' back to: ' + str(self.bufferLoc)
            lenNE = MAP_SIZE - self.prevBufferLoc + self.bufferLoc - 4
            newEntries = np.zeros((2,lenNE))
            newEntries[0] = np.concatenate(( buffer[0,self.prevBufferLoc:MAP_SIZE] , buffer[0,4:self.bufferLoc] ) , axis=1)
            newEntries[1] = np.concatenate(( buffer[1,self.prevBufferLoc:MAP_SIZE] , buffer[1,4:self.bufferLoc] ) , axis=1)

	
        # update times

        # pru predicted:
        self.pruPrevTime = self.pruCurrentTime
#       self.pruCurrentTime = self.pruPrevTime + len(newEntries_0)*0.0001
        self.pruCurrentTime = self.pruPrevTime + lenNE * 0.0001

        self.pruTotalTime = self.pruCurrentTime - self.sysStartTime

        # system actual
        self.sysCurrentTime = time.time()
        self.sysTotalTime = self.sysCurrentTime - self.sysStartTime

        # pru diferences
        sysToPru  = self.sysTotalTime  - self.pruTotalTime

#       print '******* Timings *******'
#       
#       print 'pruTotalTime: ' + str(self.pruTotalTime)
#       print 'sysTotalTime: ' + str(self.sysTotalTime)
#       print 'sys to pru: ' + str(sysToPru)


        # calculate number of ticks 1->0 and 0->1 in newEntries

        for side in range(0,2):

            # calculate number of ticks in this sample
            ticks = np.diff(newEntries[side])
            ticks = abs(ticks)
            ticks = sum(ticks)
            if self.prevLastTick[side] != newEntries[side][0]: # catch ticks that go accross sets of samples
                ticks = ticks + 1

            self.prevLastTick[side] = newEntries[side][lenNE-1]

            #calculate time elapsed for this set of samples         
            timeElapsed = self.pruCurrentTime - self.pruPrevTime
            self.tickVel[side] = ticks / timeElapsed

            #create running average of tick vels over 5 readings 
            self.runningAverage[side] = (self.runningAverage[side]*4 + self.tickVel[side])/5

            # set State Encoder
            self.encTime[side]  = 0.0                       # not required in modified QB program
            self.encPos[side] = self.encPos[side] + (ticks * np.sign(self.pwm[side]))   # new  encoder tick position
            self.encVel[side] = self.runningAverage[side] * np.sign(self.pwm[side]) # new encoder tick velocity

            print 'encPos[{:d}]: {:0.1f}'.format(side,self.encPos[side]) + ' encVel[{:d}]: {:0.1f}'.format(side,self.encVel[side])





