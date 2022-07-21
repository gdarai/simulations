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

########
# Settings file
if(len(sys.argv) > 1):
	SETTING = sys.argv[1]

print('\n-----------\n')
print('\nReading input file --> '+SETTING)
