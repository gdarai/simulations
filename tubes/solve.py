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
def stringState(sort = False):
	size = state['size']
	colMap = state['colorsInv']
	printDebug(2, colMap)
	out = []
	for tube in state['tubes']:
		printDebug(3, "tube", tube)
		outOne = ''
		for fill in tube[1]:
			printDebug(3, "fill", fill)
			outOne = outOne + colMap[fill[0]]*fill[1]
		outOne = outOne + EMPTY*tube[0]
		out.append(outOne)
	printDebug(2, out)
	if(sort == True): out.sort()
	outStr = ''.join(out)
	return outStr

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
	state['toCheck'] = [[ROOT, initState]]
	state['known'] = set()
	state['known'].add(initState)
	state['from'] = list(range(0,len(state['tubes'])))
	state['to'] = list(range(0,len(state['tubes'])))
	state['round'] = 0
	state['roots'] = 0
	state['solved'] = 0
	state['rowSize'] = source['rowSize']
	state['colNames'] = source['colors']
	state['solution'] = []
	state['initial'] = source['tubes']

# cinit the state object from dump
def initStateFromDump(dump):
	state['bulk'] = dump['bulk']
	state['size'] = dump['size']
	state['colors'] = dump['colors']
	state['colorsInv'] = dict()
	for key in dump['colorsInv']:
		state['colorsInv'][int(key)] = dump['colorsInv'][key]
	state['tubes'] = dump['tubes']
	state['toCheck'] = dump['toCheck']
	state['known'] = set(dump['known'])
	state['from'] = dump['from']
	state['to'] = dump['to']
	state['round'] = dump['round']
	state['roots'] = dump['roots']
	state['solved'] = dump['solved']
	state['rowSize'] = dump['rowSize']
	state['colNames'] = dump['colNames']
	state['initial'] = dump['initial']

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
	if(out[1] == state['size']): return False
	tube[1] = tube[1][0:-1]
	tube[0] = tube[0] + out[1]
	return out

# tweak the state by adding a content
def tweakStateAdd(toAdd, idx):
	tube = state['tubes'][idx]
	if(tube[0] < toAdd[1]): return False
	oldT0 = tube[0]
	tube[0] = tube[0] - toAdd[1]
	if(len(tube[1]) == 0):
		tube[1] = [toAdd]
		return True
	lastFill = tube[1][-1]
	if(lastFill[0] == toAdd[0]):
		lastFill[1] = lastFill[1] + toAdd[1]
		return True
	tube[0] = oldT0
	return False

# get solution path
def getPath(prev, i, j):
	return prev+STEP+str(i)+SEPARATOR+str(j)

# add new state to check
def addToCheck(prev, i, j):
	stateMark = stringState(True)
	if(stateMark in state['known']): return
	stateStr = stringState()

	path = getPath(prev, i, j)
	state['toCheck'].append([path, stateStr])
	state['known'].add(stateMark)

########
# Dump
def storeDump():
	state['known'] = list(state['known'])
	state['round'] = state['round'] + 1
	f = open(DUMP, "w")
	f.write(json.dumps(state, indent=4, sort_keys=True))
	f.close()

def storeSolution(solution):
	store = dict()
	store['size'] = state['size']
	store['rowSize'] = state['rowSize']
	store['colNames'] = state['colNames']
	store['colors'] = state['colors']
	store['initial'] = state['initial']
	store['final'] = solution[1]
	store['steps'] = solution[0].split(STEP)[1:]
	store['separator'] = SEPARATOR
	f = open(SOLUTION, "w")
	f.write(json.dumps(store, indent=4, sort_keys=True))
	f.close()

########
# Settings file
haveDump = os.path.isfile(DUMP)
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]
	haveDump = False
print('\n-----------------\n-- SOLVE TUBES --\n-----------------\n')
if(haveDump):
	print('\nReading DUMP file --> '+DUMP)
	dump = json.load(open(DUMP))
	printDebug(1, DUMP)
	initStateFromDump(dump)
else:
	print('\nReading INPUT file --> '+SETTING)
	source = json.load(open(SETTING))
	printDebug(1, source)
	initState(source)

printDebug(1, "Initial State", state)
round = 0;
while round < state['bulk']:
	round += 1
	checking = state['toCheck'].pop()
	printf('PROGRESS %.1f', (round/state['bulk'])*100)
	print(' %')
	printDebug(1, 'checking', checking)
	setArrState(checking[1])
	printDebug(1, state)
	if(checking[0].count(STEP) == 1):
		state['solved'] += 1

	randomChangeMap()

	for i in state['from']:
		iOrig = copy.deepcopy(state['tubes'][i])
		toAdd = tweakStateRemove(i)
		if(toAdd == False): continue
		for j in state['to']:
			if(i == j): continue
			jOrig = copy.deepcopy(state['tubes'][j])
			if(tweakStateAdd(toAdd, j) == False): continue
			if(checkState() == True):
				solution = [getPath(checking[0], i, j), stringState()]
				printDebug(0, 'WINNER', solution[1]+' '+solution[0])
				printf('BULK ITTERATION %d (by %d)\n', state['round']+1, state['bulk'])
				printf('SOLVED in %d STEPS\n', checking[0].count(STEP))
				storeSolution(solution)
				quit()
			addToCheck(checking[0], i, j)
			state['tubes'][j] = jOrig
		state['tubes'][i] = iOrig

	if(checking[0].count(STEP) == 0):
		state['roots'] = len(state['toCheck'])
		state['solved'] = 0

printDebug(0, 'BULK FINISHED', state['bulk'])
printf('BULK ITTERATION %d\n', state['round']+1)
printf('SOLVED %d of %d\n', state['solved'], state['roots'])
printDebug(0, 'KNOWN', len(state['known']))
printDebug(0, 'TO CHECK', len(state['toCheck']))
storeDump()
