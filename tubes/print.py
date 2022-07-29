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
DUMP = 'dump.json'
SOLUTION = 'solved.json'
EMPTY = ' '
ROOT = 'X'
STEP = '-'
SEPARATOR = ', '
EMPTY_NUM = 0
debug = 0
state = dict();
BULK = 10

########
# Functions
def printf(format, *args):
	sys.stdout.write(format % args)

def printDebug(lvl, desc, data=None):
	if(debug >= lvl):
		if(data != None): print(desc+' '+str(data))
		else: print(desc)

# get the colors map
def getColors(colors):
	keys = list(colors.keys())
	keys.sort()
	colMap = dict();
	colMap['size'] = len(keys) + 1;
	colMap[EMPTY] = EMPTY_NUM
	for idx, key in enumerate(keys):
		colMap[key] = idx + 1

	return colMap;

# init the state string
def stringStateFromInit(tubes):
	size = state['size']
	out = ''
	for tube in tubes:
		out = out + tube
		if(len(tube) < len(out)):
			out = out + EMPTY*(size - len(tube))
	printDebug(2, out)
	return out

def setArrStateLambda(liq):
	return [state['colors'][liq[0]],len(liq)]

# init the state string
def setArrState(stringState):
	x = state['size']
	strTubes =[stringState[y-x:y] for y in range(x, len(stringState)+x,x)]
	for idx, tube in enumerate(strTubes):
		tubeSplit = [m.group(0) for m in re.finditer(r"(.)\1*", tube)]
		tubeSplitMap = list(map(setArrStateLambda, tubeSplit));
		tubeFree = x
		if(len(tubeSplitMap) > 0):
			if(tubeSplitMap[-1][0] == 0):
				tubeFree = tubeSplitMap[-1][1]
				tubeSplitMap = tubeSplitMap[0:-1]
			else:
				tubeFree = 0
		state['tubes'][idx] = [tubeFree,tubeSplitMap]
		printDebug(3, state)

# cinit the state object
def initState(source):
	state['size'] = source['size']
	state['colors'] = source['colors']
	state['colorsInv'] = {v: k for k, v in state['colors'].items()}
	state['tubes'] = [None] * len(source['initial'])
	setArrState(stringStateFromInit(source['initial']))
	state['steps'] = source['steps']
	state['separator'] = source['separator']
	state['rowSize'] = source['rowSize']
	state['colNames'] = source['colNames']

# tweak the state by removing a content
def tweakStateRemove(idx):
	tube = state['tubes'][idx]
	if(tube[0] == state['size']): return False
	out = tube[1][-1]
	tube[1] = tube[1][0:-1]
	tube[0] = tube[0] + out[1]
	return out

# tweak the state by adding a content
def tweakStateAdd(toAdd, idx):
	tube = state['tubes'][idx]
	if(tube[0] < toAdd[1]): return False
	tube[0] = tube[0] - toAdd[1]
	if(len(tube[1]) == 0):
		tube[1] = [toAdd]
		return True
	lastFill = tube[1][-1]
	if(lastFill[0] == toAdd[0]):
		lastFill[1] = lastFill[1] + toAdd[1]
		return True
	tube[1].append(toAdd)
	return True

########
# Read Tubes

def getTube(idStr):
	idNum = int(idStr)
	idLetter = chr( ord('A') + (idNum // state['rowSize']) )
	idNum = (idNum % state['rowSize']) + 1
	return idLetter + str(idNum)

def getColor(idx):
	printDebug(2, 'COLOR', [idx, state['tubes']])
	printDebug(2, 'COLOR', [idx, state['tubes'][idx]])
	tube = state['tubes'][idx][1]
	colId = tube[-1][0]
	colCh = state['colorsInv'][colId]
	return state['colNames'][colCh]

########
# Settings file
print('\n-----------------\n-- SOLVE TUBES --\n-- PRINT       --\n-----------------\n')
print('\nReading SOLUTION file --> '+SOLUTION)

source = json.load(open(SOLUTION))
initState(source)
max = len(state['steps']) // BULK + 1
idx = 0;
bulk = 0;
for step in state['steps']:
	idx += 1
	if(idx % BULK == 1):
		bulk += 1
		print('==== BULK '+str(bulk)+' / '+str(max))
	nums = step.split(state['separator'])
	printDebug(1, 'NUMS', nums)
	printDebug(2, 'TUBES', [state['tubes'][int(nums[0])], state['tubes'][int(nums[1])]])
	tube1 = getTube(nums[0])
	tube2 = getTube(nums[1])
	color = getColor(int(nums[0]));
	print('  '+tube1+' to '+tube2+' - '+color)

	toAdd = tweakStateRemove(int(nums[0]))
	tweakStateAdd(toAdd, int(nums[1]))
	printDebug(1, 'STATE', state['tubes'])
