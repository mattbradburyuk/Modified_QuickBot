import numpy as np
import pypru as pp
import threading
import time
import sys


RUN_FLAG = True


class Qb_read_test():
	""" test of encoder reader prior to integration into QuickBot class"""


	# === Class Properties ===
    	# Parameters
    	
	sampleTime = 20.0/1000.0
	currentTime = 0.0;

	bufferLoc = 0
	prevBufferLoc = 0

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
		self.startTime = time.time()
		self.currentTime = self.startTime
				
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
		print 'readEncoderValues'
		
		buffer = pp.get_pru_data()

		print 'len buffer:' + str(len(buffer))
		
		#update bufferLoc
		self.prevBufferLoc =  self.bufferLoc
		self.bufferLoc = buffer[0]

		if self.bufferLoc > self.prevBufferLoc:
			print 'forwards from: ' + str(self.prevBufferLoc) +' to: ' + str(self.bufferLoc)
			newEntries = buffer[self.prevBufferLoc: self.bufferLoc]
		else:
			print 'backwards from: ' + str(self.prevBufferLoc) +' back to: ' + str(self.bufferLoc)
			newEntries = np.concatenate(( buffer[self.prevBufferLoc:4096] , buffer[4:self.bufferLoc] ) , axis=1)

		print newEntries
