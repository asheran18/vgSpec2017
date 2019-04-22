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

# Constants


###################################################################################################################
# Args
resultToAnalyze = "/mnt/c/Users/Alec/Desktop/vgSpec2017/scripts/500.perlbench_r_annotated.txt"
indivOutputDir = "/mnt/c/Users/Alec/Desktop/vgSpec2017/scripts/"
summaryOutputFile = "/mnt/c/Users/Alec/Desktop/vgSpec2017/scripts/summary.txt"
eventToAnalyze = "D1mr"
percentToAnalyze = 0.80
regionToAnalyze = 30
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

# Prove that we can create one file for one instruction
for j in range(10):
    i = hotList[j][0] - regionToAnalyze
    code = []
    while (i <= (hotList[j][0] + regionToAnalyze)):
        if (len(rawData[i].split(None, 14)) > 14):
            # A little confusing, but just grabs the line number, the data point, and the code for that line while preserving tabs
            buff = [str(rawData[i].split(None, 14)[0]), str(rawData[i].split(None, 14)[eventIndex]), str(rawData[i].split(None, 13)[-1].split(' ',1)[1]).rstrip()]
            code.append('{0:<20} {1:<20} {2}'.format(*buff))
        i += 1
    # Writing to the ouput file for this hotspot
    indivOutputFile = indivOutputDir + "top" + str(j+1) + ".txt"
    with open(indivOutputFile, 'a') as out:
        # Prepare the header to the output file
        percOfTotal = str(float(hotList[j][1])/float(totalEvents)*100.0)
        header = "--------------------------------------------------------------------------------------------------\n"
        header = header + "--- Hot Instruction Number " + str(j+1) + " has " + str(hotList[j][1]) + " events associated with it (" + percOfTotal[0:5] + " % of total events) ---\n"
        header = header + "--------------------------------------------------------------------------------------------------\n"
        out.write(header)
        header = ['Line Number', eventToAnalyze, 'Instruction']
        out.write('{0:<20} {1:<20} {2}'.format(*header))
        out.write('\n')
        header = ['------', '------', '------']
        out.write('{0:<20} {1:<20} {2}'.format(*header))
        out.write('\n')
        # Write all of the lines to the file
        for line in code:
            out.write(line)
            out.write('\n')



# # Go through the hotspot list and get the region of code each one lies within
# with open(outputFile, 'w') as out:
#     out.write("LINE FORMAT:\n")
#     out.write("Line\tIr\tI1mr\tILmr\tDr\tD1mr\tDLmr\tDw\tD1mw\tDLmw\tBc\tBcm\tBi\tBim\tInstruction\n")
# for index,instruction in enumerate(hotList):
#     lineNum = instruction[0]
#     percOfTotal = str(float(instruction[1])/float(totalEvents)*100.0)
#     code = "\n--- Hot Instruction Number " + str(index + 1) + " has " + str(instruction[1]) + " events associated with it (" + percOfTotal[0:5] + " % of total events) ---\n"
#     i = lineNum - regionToAnalyze
#     while (i <= (lineNum + regionToAnalyze)):
#         code = code + rawData[i]
#         i += 1
#     with open(outputFile, 'a') as out:
#         out.write(code)



# Heirarchy:
# for every benchmark, have a folder: bmkfolder
# in bmkfolder we have BP folder and memory folder
# for example, in memory folder we have one file for each of the top ten instructions wrt to LL data misses -> that contains code with the line number, D1m, and DLLm (n TBD)
# we should also have a summary file that displays data for each of the top 10 instructions only -> in excel -> also what percent of total does this make up?
