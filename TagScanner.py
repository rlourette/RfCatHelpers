#!/usr/bin/env python

import sys
import time
from rflib import *
from struct import *
import argparse
import bitstring
import re
import operator
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import datetime as dt
import select
import tty
import termios
import messages


chr = 0
keyLen = 0
baudRate = 200000
frequency = 433272000

def ConfigureD(d):
	d.setMdmModulation(MOD_FORMAT_GFSK)
	d.setFreq(frequency)
	# d.makePktFLEN()
	d.setMdmSyncWord(0x670b)
	d.setMdmDRate(baudRate)
	d.setMdmNumPreamble(MFMCFG1_NUM_PREAMBLE_6) # 48
	d.setPktPQT(7)
	d.setMdmSyncMode(SYNCM_16_of_16) # 16/16
	d.setEnablePktDataWhitening(enable=True)
	d.setMdmChanBW(300000)
	d.setEnablePktCRC()
	d.makePktVLEN()

print("")
print("######################################################")
print("#                TAG Scanning with RFCat             #")
print("#                                                    #")
print("#                  @Richard Lourette                 #")
print("#                                                    #")
print("######################################################")
print("")
parser = argparse.ArgumentParser(
	description='Simple program to scan for PWM OOK codes',
	# version="RFCat PWM Scanner 0.01 - by Andrew MacPherson (www.andrewmohawk.com) / @AndrewMohawk "
)
parser.add_argument('-f', action="store", default=frequency, dest="Freq",help='Frequency to start scan at, defaults to 433000000',type=int)
parser.add_argument('-vv', action="store_true", dest="verbose", default=False,help='Verbose output')
# parser.add_argument('-p', action="store", dest="paddingZeros", default=15,help='Amount of repeated zeros to search for when looking for patterns',type=int)
#parser.add_argument('-g',action="store_true",dest="showGraph", default=False,help='Show graph of data')
parser.add_argument('-ms', action="store", dest="minimumStrength", default=-80,help='Minimum strength, defaults to -80',type=int)
results = parser.parse_args()

currFreq = results.Freq
frequency = currFreq
sys.stdout.write("Configuring RFCat...\n")
d = RfCat()
ConfigureD(d)
allstrings = {}
lens = dict() 

'''
if (results.showGraph == True):
	x = range(0,38)
	y = range(0,38)
	line, = plt.plot(x,y,"-")
	plt.ion()
	plt.show()
	plt.draw()
	x = range(0,38)
	line.set_xdata(x)
'''

usecolors = False

def spinning_cursor():
	while True:
		for cursor in '|/-\\':
			yield cursor

spinner = spinning_cursor()
BOLD = '\033[1;37;40m'
ENDC = '\033[0m'
RED = '\033[1;31;40m'
BLUE = '\033[1;34;40m'
GREEN = '\033[1;32;40m'
YELLOW = '\033[1;33;40m'
WHITE = '\033[1;37;40m'
LIGHTBLUE = '\033[1;36;40m'

if usecolors:
	print("Scanning for Tags... Press " + BOLD + WHITE + "<enter>" + ENDC + " to stop and " + BOLD + WHITE + " any key" + ENDC + " to continue\n")
else:
	print("Scanning for Tags... Press <enter> to stop and any key to continue\n")



def isData():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

if usecolors:
	old_settings = termios.tcgetattr(sys.stdin)
	tty.setcbreak(sys.stdin.fileno())


def showStatus():
	sys.stdout.write('\r' + BOLD +  ENDC + "[ " + BOLD + YELLOW)
	sys.stdout.write(next(spinner))
	strength= -d.getRSSI()[0]
	# strength= 0 - ord(str(d.getRSSI()))
	sigFound = "0"
	if(currFreq in allstrings):
		sigFound = str(len(allstrings[currFreq]))
	sys.stdout.write(ENDC + ' ] Freq: [ ' + LIGHTBLUE + str(currFreq) + ENDC + ' ] Strength [ ' + YELLOW + str(strength) + ENDC + ' ] Signals Found: [ ' + GREEN + sigFound + ENDC + " ]" )
	if(lockedFreq == True):
		sys.stdout.write(ENDC + RED + " [!FREQ LOCKED!]" + ENDC)
	#else:
	#	sys.stdout.write(" " * 30)
	#sys.stdout.write(" " * 10)
	#yes, i know, icky!
	sys.stdout.flush()
	#sys.stdout.write("\n- Press Any Key to End Scan -");

n1=dt.datetime.now()



while True:
	try:
		if isData():
			x= ord(sys.stdin.read(1))
			if (x == 3 or x == 10):
				break
			elif(x == 32):
				print("unlocking")
		y, t = d.RFrecv(timeout=1, blocksize=255)
		# sampleString=y.hex()
		# lets find all the zero's
		# showStatus();
		# print("Received:  %s" % y.hex())
		try:
			offset, message = messages.MessageFactory.CreateMessage(0,y)
			print(f"{message} msgcrc({message.msgcrc:04X}) crc16({message.crc16:04X})")
		except messages.IllegalMessage as ex:
			print(ex, y)
		# zeroPadding = [match[0] for match in re.findall(r'((0)\2{25,})', sampleString)]
		# for z in zeroPadding:
		# 	currLen = len(z)
		# 	if currLen in lens.keys():
		# 		lens[currLen] = lens[currLen] + 1
		# 	else:
		# 		lens[currLen] = 1
		# sorted_lens = sorted(lens.items(), key=operator.itemgetter(1), reverse=True)
		# lens = dict()
		# if(sorted_lens and sorted_lens[0][0] > 0 and sorted_lens[0][0] < 400):
		# 	zeroPaddingString = "0" * sorted_lens[0][0]
		# 	#print "zeros used in padding: " , zeroPaddingString
		#
		# 	possibleStrings = sampleString.split(zeroPaddingString)
		# 	possibleStrings = [s.strip("0") for s in possibleStrings]
		# 	#print possibleStrings
		# 	for s in possibleStrings:
		# 		if(currFreq in allstrings):
		# 			allstrings[currFreq].append(s)
		# 		else:
		# 			allstrings[currFreq] = [s]
		# 		if((len(allstrings[currFreq]) > results.lockNum) and lockOnSignal == True):
		# 			lockedFreq = True
	except KeyboardInterrupt:
		break
	except ChipconUsbTimeoutException:
		pass

if usecolors:	
	termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
	# hacky, but i wanna get rid of the line:
	print("\r" + (" " * 150))

print("Scanning stopped:")
# sortedKeys = sorted(allstrings, key=lambda k: len(allstrings[k]), reverse=True)


# key_packed = bitstring.BitArray(bin=finalKey).tobytes()
sys.stdout.write("\nDone.\n")
d.setModeIDLE()
