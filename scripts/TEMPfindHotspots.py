import string
import datetime
import time
import subprocess
import os
import sys
from collections import deque
import re
import csv
import fnmatch



###################################################################################################################
# Args
resultToAnalyze = "/mnt/c/Users/Alec/Desktop/vgSpec2017/scripts/500.perlbench_r_annotated.txt"
eventToAnalyze = "D1mr"
percentToAnalyze = 0.90
regionToAnalyze = 10
###################################################################################################################


# Switch on the event to find the column which is cared about
switchOnEvent = {
        'Ir'    : 1,
        'I1mr'  : 2,
        'ILmr'  : 3,
        'Dr'    : 4,
        'D1mr'  : 5,
        'DLmr'  : 6,
        'Dw'    : 7,
        'D1mw'  : 8,
        'DLmw'  : 9,
        'Bc'    : 10,
        'Bcm'   : 11,
        'Bi'    : 12,
        'Bim'   : 13
}
eventIndex = switchOnEvent.get(eventToAnalyze, "NA")

# Get all of the lines in the file
eventData = []
sortedEventData = []
splitData = []
rawData = open(resultToAnalyze).readlines()
dataStart = False
totalEvents = 0
for line in range(len(rawData)):
    # Wait until the first source annotated shows up
    if (not dataStart and "Auto-annotated source" in rawData[line]):
        dataStart = True
    # Process until the final summary is seen
    elif (dataStart and "percentage of events annotated" in rawData[line]):
        dataStart= False
    # Otherwise process the line
    elif (dataStart):
        # Split the line by tabs
        splitData = rawData[line].split()
        # Make sure this line has at least an expected number of columns
        if (len(splitData) > eventIndex):
            # Ignore comment lines - they start with a dash
            if (("-" not in splitData[1])):
                value = splitData[eventIndex].replace(',' , '') if splitData[eventIndex] != '.' else '0'
                if (value.isdigit()):
                    totalEvents += int(value)
                    eventData.append((int(splitData[0]), int(value)))
# Sort the list by most number of events
eventData.sort(key=lambda x:x[1], reverse=True)



# Determine the top <percentToAnalyze> percent of the hot instructions
hotList = []
threshold = percentToAnalyze * float(totalEvents)
accumulator = 0
iterator = 0
while (accumulator < threshold):
    hotList.append(eventData[iterator])
    accumulator += eventData[iterator][1]
    iterator += 1

# Go through the hotspot list and get the region of code it lies within
for instruction in hotList:
    lineNum = instruction[0]
    code = ""
    i = lineNum - regionToAnalyze
    while (i <= (lineNum + regionToAnalyze)):
        code = code + rawData[i]
        i += 1
    print code
    break
