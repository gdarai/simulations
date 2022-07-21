import sys
import re
import os
import json
import random
import math
import copy
import cv2
import numpy as np
import csv

SETTING = 'setting.json'
EMPTY = ' '
########
# Functions

# calc 1 tube size
def calcSize(tubes):
	out = -1
	for tube in tubes:
		out = max(out, len(tube))
	return out

# get the colors map
def getColors(colors):
	keys = list(colors.keys())
	keys.sort()
	colMap = dict();
	colMap['size'] = len(keys) + 1;
	colMap[EMPTY] = 0
	for idx, key in enumerate(keys):
		colMap[key] = idx + 1
	return colMap;

# init the state string
def stringState(tubes, size):
	state = ''
	for tube in tubes:
		state = state + tube
		if(len(tube) < size):
			state = state + EMPTY*(size - len(tube))
	return state

# init the state string
def setNumState(stringState, state):
	state['tubes'] = []
	x = state['size']
	strTubes =[stringState[y-x:y] for y in range(x, len(stringState)+x,x)]
	colMap = state['colors']
	multip = colMap['size']
	for idx, tube in enumerate(strTubes):
		val = 0
		for ch in tube:
			val = ((val) * multip ) + colMap[ch]
		print(val)
#		state['tubes'][idx] = val

# check the state if solved

########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]

print('\n-----------------\n-- SOLVE TUBES --\n-----------------\n')
print('\nReading input file --> '+SETTING)

source = json.load(open(SETTING))

print(source)

# Init
state = dict();
state['size'] = source['size']
if(state['size'] == -1):
	state['size'] = calcSize(source['tubes'])

state['colors'] = getColors(source['colors'])
setNumState(stringState(source['tubes'], state['size']), state)

print(state)
