# to do:
# add carry forward of previous sample value

import numpy as np
import pypru as pp
import threading
import time
import sys
import timeit

RUN_FLAG = True


class Qb_read_test():
	""" test of encoder reader prior to integration into QuickBot class"""


	# === Class Properties ===
    	# Parameters
    	
	sampleTime = 20.0/1000.0
	currentTime = 0.0
	prevTime = 0.0
	startTime = 0


	bufferLoc = 0
	prevBufferLoc = 4	# initialise at start of sample data in buffer


	prevLastTick = 0;

	runningAverage = 0;

	# State Encoder
    	encTime = [0.0, 0.0]  # Last time encoders were read
    	encPos = [0.0, 0.0]  # Last encoder tick position
    	encVel = [0.0, 0.0]  # Last encoder tick velocity

    	# === Class Methods ===
    	# Constructor
    	def __init__(self):

		print 'initalising Qb_read_test class'


	def run(self):
		global RUN_FLAG

		pp.start_up_pru()

		adj = 0.014; 
		self.sysStartTime = time.time() + adj
		self.pruCurrentTime = self.sysStartTime


		# double check timingn with timeit
#		self.timeitStartTime = timeit.default_timer() + adj
#		self.ct2 = self.timeitStartTime
	
		while RUN_FLAG is True:
			self.update()
			time.sleep(self.sampleTime)

	def stop(self):
		global RUN_FLAG
		print 'stopping'
		RUN_FLAG = False


	def update(self):
		self.readEncoderValues()

	def readEncoderValues(self):
#		print 'readEncoderValues'
		
		buffer = pp.get_pru_data()

#		print 'len buffer:' + str(len(buffer))
		
		#update bufferLoc
		self.prevBufferLoc =  self.bufferLoc
		self.bufferLoc = buffer[0]

		# get new entries in buffer
		if self.bufferLoc > self.prevBufferLoc:
#			print 'forwards from: ' + str(self.prevBufferLoc) +' to: ' + str(self.bufferLoc)
			newEntries = buffer[self.prevBufferLoc: self.bufferLoc]
		else:
#			print 'backwards from: ' + str(self.prevBufferLoc) +' back to: ' + str(self.bufferLoc)
			newEntries = np.concatenate(( buffer[self.prevBufferLoc:4096] , buffer[4:self.bufferLoc] ) , axis=1)
			
		
		# update times

		# pru predicted:
		self.pruPrevTime = self.pruCurrentTime
		self.pruCurrentTime = self.pruPrevTime + len(newEntries)*0.0001
		self.pruTotalTime = self.pruCurrentTime - self.sysStartTime
		
		# system actual
		self.sysCurrentTime = time.time()
		self.sysTotalTime = self.sysCurrentTime - self.sysStartTime	

		# timeit actual
#		self.timeitCurrentTime = timeit.default_timer()
#		self.timeitTotalTime = self.timeitCurrentTime - self.timeitStartTime

		# pru diferences
		sysToPru  = self.sysTotalTime  - self.pruTotalTime
#		timeitToPru = self.timeitTotalTime - self.pruTotalTime

#
#		print '******* Timings *******'
#		
#		print 'pruTotalTime: ' + str(self.pruTotalTime)
#		print 'sysTotalTime: ' + str(self.sysTotalTime)
#		print 'timeitTotalTime: ' + str(self.timeitTotalTime)
#		print 'sys to pru: ' + str(sysToPru)
#		print 'timeit to pru: ' + str(timeitToPru) 
#

		ticks = np.diff(newEntries)
		ticks = abs(ticks)
		ticks = sum(ticks)

		
		if self.prevLastTick != newEntries[0]:
			ticks = ticks + 1
			print 'tick at start'

		self.prevLastTick = newEntries[len(newEntries)-1]
		
#		print 'ticks: ' + str(ticks) 
		
		timeElapsed = self.pruCurrentTime - self.pruPrevTime

		tickVel = ticks / timeElapsed

		#create running average of tick vels over 5 readings

		self.runningAverage = (self.runningAverage*4 + tickVel)/5
		print 'tickVel: {:0.1f}'.format(tickVel) + ' runningAverage: {:0.1f}'.format(self.runningAverage)
