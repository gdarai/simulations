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
EMPTY_NUM = 0
debug = 1
state = dict();

########
# Functions

def printDebug(lvl, data):
	if(debug >= lvl): print(data)

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

# get current state string
def stringState():
	size = state['size']
	colMap = state['colorsInv']
	out = ''
	for tube in state['tubes']:
		for fill in tube[1]:
			out = out + colMap[fill[0]]*fill[1]
		out = out + EMPTY*tube[0]
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
	if(state['size'] == -1):
		state['size'] = calcSize(source['tubes'])

	state['colors'] = getColors(source['colors'])
	state['colorsInv'] = {v: k for k, v in state['colors'].items()}
	state['tubes'] = [None] * len(source['tubes'])
	initState = stringStateFromInit(source['tubes'])
	state['toCheck'] = [[initState, '']]
	state['known'] = set()
	state['known'].add(initState)
	state['from'] = list(range(0,len(state['tubes'])))
	state['to'] = list(range(0,len(state['tubes'])))

# check the state if solved
def checkState():
	for tube in state['tubes']:
		if(len(tube) == 1): continue
		if((len(tube) == 2) & (tube[1][0] == EMPTY_NUM)): continue
		return False
	return True

# make map of possible changes
def randomChangeMap():
	random.shuffle(state['from'])
	random.shuffle(state['to'])

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
		tube[1] = toAdd
		return True
	lastFill = tube[1][-1]
	if(lastFill[0] == toAdd[0]):
		lastFill[1] = lastFill[1] + toAdd[1]
		return True
	tube[1].append(toAdd)
	return True

########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]

print('\n-----------------\n-- SOLVE TUBES --\n-----------------\n')
print('\nReading input file --> '+SETTING)

source = json.load(open(SETTING))
printDebug(1, source)

# Init
initState(source)
printDebug(1, state)
checking = state['toCheck'].pop(0)
setArrState(checking[0])
printDebug(1, state)
printDebug(2, 'Check: '+str(checkState()))
randomChangeMap()

for i in state['from']:
	iOrig = copy.deepcopy(state['tubes'][i])
	toAdd = tweakStateRemove(i)
	if(toAdd == False): continue
	for j in state['to']:
		if(i == j): continue
		jOrig = copy.deepcopy(state['tubes'][j])
		if(tweakStateAdd(toAdd, j) == False): continue
		if(checkState()): #WIN
			print('Winner')
			quit()
		print('NotWinner')
		stringState()
		#ADD to toCheck
		state['tubes'][j] = jOrig
	state['tubes'][i] = iOrig


quit()
