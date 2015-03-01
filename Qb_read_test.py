# to do:
# add pwm direction to change velocity sign and direction of ticks increment
# look at whether trigger for updated is timed correctly
# add second encoder
# add properties list


import numpy as np
import pypru as pp 	# start_up_pru(), stop_pru(), get_pru_data()
import threading
import time
import sys
import timeit

RUN_FLAG = True
MAP_SIZE = 4096

class Qb_read_test():
	""" test of encoder reader prior to integration into QuickBot class"""


	# === Class Properties ===
    	# Parameters
    	
	# timing 
	sampleTime = 20.0/1000.0	#sample time of the update function
	pruCurrentTime = 0.0	# time of current last sample per pru
	pruPrevTime = 0.0 	# time of previous last sample per pru
	pruTotalTime = 0.0	# total time since pru started per pru
	sysStartTime = 0.0	# system time when pru started
	sysTotalTime = 0.0	# total time since pru started per system
	
	#buffer
	bufferLoc = 4	 # initialise at start of sample data in buffer
	prevBufferLoc = 0

	#ticks
	prevLastTick = [0,0];
	runningAverage = [0.0,0.0];
	tickVel = [0,0]

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
			 
#			newEntries_0 = buffer[0,self.prevBufferLoc: self.bufferLoc]
#			newEntries_1 = buffer[1,self.prevBufferLoc: self.bufferLoc]
		else:
			print 'backwards from: ' + str(self.prevBufferLoc) +' back to: ' + str(self.bufferLoc)
			lenNE = MAP_SIZE - self.prevBufferLoc + self.bufferLoc - 4  	
			newEntries = np.zeros((2,lenNE))		
			newEntries[0] = np.concatenate(( buffer[0,self.prevBufferLoc:MAP_SIZE] , buffer[0,4:self.bufferLoc] ) , axis=1)
			newEntries[1] = np.concatenate(( buffer[1,self.prevBufferLoc:MAP_SIZE] , buffer[1,4:self.bufferLoc] ) , axis=1)

#			newEntries_0 = np.concatenate(( buffer[0,self.prevBufferLoc:4096] , buffer[0,4:self.bufferLoc] ) , axis=1)
#			newEntries_1 = np.concatenate(( buffer[1,self.prevBufferLoc:4096] , buffer[1,4:self.bufferLoc] ) , axis=1)
			
		
		# update times

		# pru predicted:
		self.pruPrevTime = self.pruCurrentTime
#		self.pruCurrentTime = self.pruPrevTime + len(newEntries_0)*0.0001
		self.pruCurrentTime = self.pruPrevTime + lenNE * 0.0001

		self.pruTotalTime = self.pruCurrentTime - self.sysStartTime
		
		# system actual
		self.sysCurrentTime = time.time()
		self.sysTotalTime = self.sysCurrentTime - self.sysStartTime	

		# pru diferences
		sysToPru  = self.sysTotalTime  - self.pruTotalTime

#		print '******* Timings *******'
#		
#		print 'pruTotalTime: ' + str(self.pruTotalTime)
#		print 'sysTotalTime: ' + str(self.sysTotalTime)
#		print 'sys to pru: ' + str(sysToPru)

		# 0: calculate number of ticks 1->0 qnd 0->1 in newEntries
		ticks = np.diff(newEntries[0])
		ticks = abs(ticks)
		ticks = sum(ticks)
		if self.prevLastTick[0] != newEntries[0][0]: # catch ticks that go accross sets of samples
			ticks = ticks + 1

		self.prevLastTick[0] = newEntries[0][lenNE-1]
		
		#calculate time elapsed for this set of samples		
		timeElapsed = self.pruCurrentTime - self.pruPrevTime
		self.tickVel[0] = ticks / timeElapsed

		#create running average of tick vels over 5 readings
		self.runningAverage[0] = (self.runningAverage[0]*4 + self.tickVel[0])/5
		print 'tickVel[0]: {:0.1f}'.format(self.tickVel[0]) + ' runningAverage[0]: {:0.1f}'.format(self.runningAverage[0])




                # 1: calculate number of ticks 1->0 qnd 0->1 in newEntries
                ticks = np.diff(newEntries[1])
                ticks = abs(ticks)
                ticks = sum(ticks)
                if self.prevLastTick[1] != newEntries[1][0]: # catch ticks that go accross sets of samples
                        ticks = ticks + 1

                self.prevLastTick[1] = newEntries[1][lenNE-1]

                #calculate time elapsed for this set of samples         
                timeElapsed = self.pruCurrentTime - self.pruPrevTime
                self.tickVel[1] = ticks / timeElapsed

                #create running average of tick vels over 5 readings
                self.runningAverage[1] = (self.runningAverage[1]*4 + self.tickVel[1])/5
                print 'tickVel[1]: {:0.1f}'.format(self.tickVel[1]) + ' runningAverage[1]: {:0.1f}'.format(self.runningAverage[1])
