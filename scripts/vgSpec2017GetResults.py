#*************************************************************
#
# SPEC 2017 Bottleneck Analysis (Valgrind and SPEC2017)
#
# Intended to organize a vgSpec 2017 run's results and prepare them
# for analysis.
#
# Args to this script
#   1) The name of the dirctory of the run's results (i.e. "3_21_vgRun")
#
# NOTE: This Software is provided AS IS.
# If we did not have as much control over these parameters
# as we do, much more error handling would be needed to ensure
# safe operation. For our purposes, however, this would be trivial
# since the application this is intended for is highly controled.
#
#
# MuRI 2019
# Cole Boulanger & Alec Sheran
#
#*************************************************************

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

#########################################
#           UTILITY FUNCTIONS           #
#########################################
# Formats the results folder into raw valgrind outputs and annotated ones
# ARGS: the root results directory, the raw results directory to make,
# the annotated results directory to make, and a temporary copy of the annotated results
# RETURNS: nothing
def prepResultsFolder(root, raw, annotated, tmp):
    # Make the dirs
    makeDirCmd = "mkdir -m 777 " + raw
    makeDir = subprocess.Popen(makeDirCmd, shell = True)
    makeDir.communicate()
    makeDirCmd = "mkdir -m 777 " + annotated
    makeDir = subprocess.Popen(makeDirCmd, shell = True)
    makeDir.communicate()
    makeDirCmd = "mkdir -m 777 " + tmp
    makeDir = subprocess.Popen(makeDirCmd, shell = True)
    makeDir.communicate()
    # Copy the raw results
    copyResCmd = "cp " + root + "*.*.txt " + raw
    copyRes = subprocess.Popen(copyResCmd, shell = True)
    copyRes.communicate()
    # Delete the old copies
    delResCmd = "rm " + root + "*.*.txt "
    delRes = subprocess.Popen(delResCmd, shell = True)
    delRes.communicate()

# Loops through all benchmarcks in the directory and sorts them by the event
# ARGS: the resuls directory being worked with, a string of the event to sort by
# RETURNS: a list of the benchmarks sorted by the event: "benchmark.name <tab> #"
def sortBenchmarksBy(resDir, eventToSortBy):
    # Prep the return list
    sortedBenchmarks = []
    fmtedSortedBenchmarks = []
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
    eventIndex = switchOnEvent.get(eventToSortBy, "NA")
    # Loop through every file for sorting
    files = os.listdir(resDir)
    pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
    for file in files:
        if fnmatch.fnmatch(file, pattern):
            # Get all of the lines in the file
            data = open(resDir + file).readlines()
            for line in range(len(data)):
                data[line] = data[line].split()
                # Look for the program totals line
                if ("PROGRAM" in data[line] and "TOTALS" in data[line]):
                    value = int(data[line][eventIndex].replace(',' , ''))
                    sortedBenchmarks.append((file, value))
    # Sort the list by most number of events
    sortedBenchmarks.sort(key=lambda x:x[1], reverse=True)
    for bmk in sortedBenchmarks:
        # Excuse the syntax, this is just for good looking printing
        num = "{:,}".format(bmk[1])
        tmpStr = "%-30s %s" % (bmk[0], num)
        fmtedSortedBenchmarks.append(tmpStr)
    return fmtedSortedBenchmarks


# Interfaces with the user to understand how the data should be processed for
# further analysis
# ARGS: the working directory of the results being analyzed
# RETURNS: a 2 element list: where the first element is a list of results files
# the user would like to analyze further and the second element is the event
# they care about
def getUserSortParameters(resDir):
    sortAgain = True
    while(sortAgain):
        print ( """
        The name of the event to sort the benchmarks by (Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw Bc Bcm Bi Bim)
        \t Ir = # of executed instructions
        \t I1mr = L1 cache read misses
        \t ILmr = LL cache read misses
        \t Dr = # of memory reads
        \t D1mr = D1 cache read misses
        \t DLmr = LL cache data read misses
        \t Dw = # of memory writes
        \t D1mw = D1 cache write misses
        \t DLmw = LL cache data write misses
        \t Bc = # of cond. branch executions
        \t Bcm = cond. branch mispreds
        \t Bi = indirect branches executed
        \t Bim = indirect branch mispreds
        """)
        sortEvent = raw_input("What would you like to sort the results by? ")
        sortedBenchByEventList = sortBenchmarksBy(resDir,sortEvent)
        for x in range(len(sortedBenchByEventList)):
            print(sortedBenchByEventList[x])
        sortAgainCheck = raw_input("Sort by different event? [y,n] ")
        if (sortAgainCheck == 'y'):
            continue
        elif (sortAgainCheck == 'n'):
            sortAgain = False
        else:
            continue
    BenchNumToProcess = input("How many of the top sorted benchmarks would you like to mark for further processing? ")
    ProcessBenchList = []
    for x in range(BenchNumToProcess):
        ProcessBenchList.append(sortedBenchByEventList[x])
    return [ProcessBenchList, sortEvent]

#########################################
#      DEFINE ABSOLUTE DIRECTORIES      #
#########################################
# Absolute path to the workspace
baseOperatingDir = "/mnt/c/Users/Alec/Desktop/"#"/local/alec/cole_workspace/"
#Base directories for vgSpec2017(ours) and spec2017(spec's)
spec2017Dir = baseOperatingDir + "spec/"
vgSpecDir = baseOperatingDir + "vgSpec2017/"
#vgSpec2017 Subdirectories
vgScriptsDir = vgSpecDir + "scripts/"
vgLogsDir = vgSpecDir + "logs/"
vgLogFile = vgLogsDir + "logfile.txt"
vgBenchDir = vgSpecDir + "benchmarks/"
vgResultDir = vgSpecDir + "results/"
vgMonitorSubprocScript = vgScriptsDir + "vgSpec2017Monitor.py"
# BUILT LATER: "vgSpecThisResultsDir" is the reference for this simulation's results
# BUILT LATER: "vgSpecThisResultsRaw" is the reference for this simulation's raw results after annotation
# BUILT LATER: "vgSpecThisResultsAnn" is the reference for this simulation's annotated results after annotation
# Spec 2017 Subdirectories
spec2017BenchmarksDir = spec2017Dir + "benchspec/CPU/"
spec2017RunDir = "run/" # NOTE: relative path - but its the same for every bmk
#spec2017ExeDir = spec2017RunDir + "run_base_refrate_mytest-m64.0000/" # NOTE: relative path - but its the same for every bmk

#########################################
#            HANDLE CLA                 #
#########################################
if (len(sys.argv) != 2):
    print ("USAGE\t:\n(1) The name of the directory of the run's results (i.e. \"3_21_vgRun\")",
                   "\t(2) The name of the event to sort the benchmarks by (Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw Bc Bcm Bi Bim)",
                   "\t Ir = # of executed instructions, I1mr = L1 cache read misses, ILmr = LL cache read misses ",
                   "\t Dr = # of memory reads, D1mr = D1 cache read misses, DLmr = LL cache data read misses ",
                   "\t Dw = # of memory writes, D1mw = D1 cache write misses, DLmw = LL cache data write misses ",
                   "\t Bc = # of cond. branch executions, Bcm = cond. branch mispreds ",
                   "\t Bi = indirect branches executed, Bim = indirect branch mispreds "
                   )
    quit()
else:
    vgSpecThisResultsDir = vgResultDir + sys.argv[1] + "/"
    vgSpecThisResultsRaw = vgSpecThisResultsDir + "raw/"
    vgSpecThisResultsAnn = vgSpecThisResultsDir + "annotated/"
    vgSpecThisResultsTmp = vgSpecThisResultsDir + "tmp/"
    # Make the raw and annoted directories as well as the temporary
    prepResultsFolder(vgSpecThisResultsDir, vgSpecThisResultsRaw, vgSpecThisResultsAnn, vgSpecThisResultsTmp)

#########################################
#        ANNOTATION OF RESULTS          #
#########################################
# Walk through all of the results files and annotate
files = os.listdir(vgSpecThisResultsRaw)
pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
for file in files:
    if fnmatch.fnmatch(file, pattern):
        # NOTE: This annotate is not going to work locally because we do not have the source locally, so we cannot test it locally
        annotateCmd = "cg_annotate --auto=yes " + vgSpecThisResultsRaw + file + " > " + vgSpecThisResultsAnn + file
        annotateRes = subprocess.Popen(annotateCmd, shell = True)
        annotateRes.communicate()
        # Copy to the tmp directory for further formatting
        copyResCmd = "cp " + vgSpecThisResultsAnn + file + " " + vgSpecThisResultsTmp
        copyRes = subprocess.Popen(copyResCmd, shell = True)
        copyRes.communicate()

#########################################
#          SORTING OF RESULTS           #
#########################################
# Walk through all of the results files and annotate
files = os.listdir(vgSpecThisResultsTmp)
pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
data = [] # Holds the entire text dump of the annotated results
for file in files:
    if fnmatch.fnmatch(file, pattern):
        data = open(vgSpecThisResultsTmp + file).readlines()
        # Prepend a line number to each line
        i = 0
        for line in range(len(data)):
            data[line] = str(i) + "\t" + data[line]
            i += 1
        # Write the formatted data back to the file
        with open(vgSpecThisResultsTmp + file, 'w') as updatedData:
            for item in data:
                updatedData.write(item)
# Let's ask the user what they want to do
analysisList = []
analysisList = getUserSortParameters(vgSpecThisResultsTmp)
