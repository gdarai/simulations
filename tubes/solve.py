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
EMPTY = ' '
EMPTY_NUM = 0
debug = 0
state = dict();

########
# Functions
def printf(format, *args):
    sys.stdout.write(format % args)

def printDebug(lvl, desc, data=None):
	if(debug >= lvl):
		if(data != None): print(desc+' '+str(data))
		else: print(desc)

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
		printDebug(3, "tube", tube)
		for fill in tube[1]:
			printDebug(3, "fill", fill)
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
	state['bulk'] = source['bulk']
	state['size'] = source['size']
	if(state['size'] == -1):
		state['size'] = calcSize(source['tubes'])

	state['colors'] = getColors(source['colors'])
	state['colorsInv'] = {v: k for k, v in state['colors'].items()}
	state['tubes'] = [None] * len(source['tubes'])
	initState = stringStateFromInit(source['tubes'])
	state['toCheck'] = [['', initState]]
	state['known'] = set()
	state['known'].add(initState)
	state['from'] = list(range(0,len(state['tubes'])))
	state['to'] = list(range(0,len(state['tubes'])))

# check the state if solved
def checkState():
	for tube in state['tubes']:
		if(tube[0] == state['size']): continue
		if(len(tube[1]) == 1): continue
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
		tube[1] = [toAdd]
		return True
	lastFill = tube[1][-1]
	if(lastFill[0] == toAdd[0]):
		lastFill[1] = lastFill[1] + toAdd[1]
		return True
	tube[1].append(toAdd)
	return True

# get solution path
def getPath(prev, i, j):
	return prev+'-'+str(i)+','+str(j)

# add new state to check
def addToCheck(prev, i, j):
	stateStr = stringState()
	if(stateStr in state['known']): return

	path = getPath(prev, i, j)
	state['toCheck'].append([path, stateStr])
	state['known'].add(stateStr)

########
# Dump
def storeDump():
	state['known'] = list(state['known'])
	f = open(DUMP, "w")
	f.write(json.dumps(state))
	f.close()

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
printDebug(1, "Initial State", state)
round = 0;
while round < state['bulk']:
	round += 1
	checking = state['toCheck'].pop(0)
	printf('PROGRESS %.1f', (round/state['bulk'])*100)
	print(' %')
	printDebug(1, 'checking', checking)
	setArrState(checking[1])
	printDebug(1, state)
	randomChangeMap()

	for i in state['from']:
		iOrig = copy.deepcopy(state['tubes'][i])
		toAdd = tweakStateRemove(i)
		if(toAdd == False): continue
		for j in state['to']:
			if(i == j): continue
			jOrig = copy.deepcopy(state['tubes'][j])
			if(tweakStateAdd(toAdd, j) == False): continue
			if(checkState() == True): #WIN
				printDebug(0, 'WINNER', stringState()+getPath(checking[0], i, j))
				quit()
			addToCheck(checking[0], i, j)
			state['tubes'][j] = jOrig
		state['tubes'][i] = iOrig
printDebug(0, 'BULK FINISHED')
storeDump()
