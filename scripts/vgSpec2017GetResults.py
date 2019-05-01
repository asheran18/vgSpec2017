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
def prepResultsFolder(root, raw, annotated, formatted):
    # Make the dirs
    sys.stdout.write("Preparing results folder...")
    makeDirCmd = "mkdir -m 777 " + raw
    makeDir = subprocess.Popen(makeDirCmd, shell = True)
    makeDir.communicate()
    makeDirCmd = "mkdir -m 777 " + annotated
    makeDir = subprocess.Popen(makeDirCmd, shell = True)
    makeDir.communicate()
    makeDirCmd = "mkdir -m 777 " + formatted
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
    # Making the final formatted results directories
    for root,dirs,files in os.walk(raw):
        for filename in files:
            newFile = formatted + "/" + filename[:-4] + "/"
            makeDirCmd = "mkdir -m 777 " + newFile
            makeDir = subprocess.Popen(makeDirCmd, shell = True)
            makeDir.communicate()
            makeDirCmd = "mkdir -m 777 " + newFile + "branch/"
            makeDir = subprocess.Popen(makeDirCmd, shell = True)
            makeDir.communicate()
            makeDirCmd = "mkdir -m 777 " + newFile + "cache/"
            makeDir = subprocess.Popen(makeDirCmd, shell = True)
            makeDir.communicate()
    sys.stdout.write("done\n")

# The main payload of this script. Finds the hotspots for the given event in the given
# benchmark and grabs the region of code each one lies within. It then generates a file
# for each hotspot and its region, as well as a summary file for all hotspots of the benchmark
# ARGS: the benchmark name, the annotated result file, directory of formatted results,
# the summary output file, the event to analyze (string), the percentage to analyze (decimal < 1),
# the number of lines above and below the hot spot to grab
# RETURNS: nothing
def analyzeHotspots(bmkName, resultToAnalyze, indivOutputDir, summaryOutputFile, eventToAnalyze, percentToAnalyze, regionToAnalyze):
    sys.stdout.write("Beginning hotspot search on " + bmkName + "...")
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
                    # Just to parse a number with commas as a proper integer
                    value = splitData[eventIndex].replace(',' , '') if splitData[eventIndex] != '.' else '0'
                    if (value.isdigit()):
                        totalEvents += int(value)
                        eventData.append((int(splitData[0]), int(value)))
    # Sort the list by most number of events
    eventData.sort(key=lambda x:x[1], reverse=True)
    sys.stdout.write("search complete\n")
    # Determine the top <percentToAnalyze> percent of the hot instructions
    hotList = []
    threshold = percentToAnalyze * float(totalEvents)
    accumulator = 0
    iterator = 0
    while (accumulator < threshold):
        hotList.append(eventData[iterator])
        accumulator += eventData[iterator][1]
        iterator += 1

    # Before doing the processing, prepare the final summary file
    sys.stdout.write("Generating output files for " + bmkName + "...")
    with open(summaryOutputFile, 'w') as out:
        header = "-------------------------------------------------------------------------------------------------\n"
        header = header + "------------------------ SUMMARY OF TOP INSTRUCTIONS FOR " + bmkName + " ------------------------\n"
        header = header + "-------------------------------------------------------------------------------------------------\n\n"
        out.write(header)
        header = ['Line Number', eventToAnalyze, 'Percent of Total','Instruction']
        out.write('{0:^20} {1:^20} {2:^20} {3}'.format(*header))
        out.write('\n')
        header = ['-----------', '------', '----------------', '-----------']
        out.write('{0:^20} {1:^20} {2:^20} {3}'.format(*header))
        out.write('\n')

    # For now we'll only do the analysis on the top 10 (if there are at least 10)
    topInstructions = 10
    if len(hotList) < 10:
        topInstructions = len(hotList)
    percAccum = 0
    eventAccum = 0
    for j in range(topInstructions):
        i = hotList[j][0] - regionToAnalyze
        k = hotList[j][0]
        code = []
        source = ""
        # First get the source file the hot instruction is from by walking up
        while (k > 0):
            if ("Auto-annotated source" in rawData[k]):
                source = rawData[k]
                break
            k -= 1
        # We grab the region of code around the hot instruction
        while (i <= (hotList[j][0] + regionToAnalyze)):
            if (len(rawData[i].split(None, 14)) > 14):
                # A little confusing, but just grabs the line number, the data point, and the code for that line while preserving tabs
                buff = [str(rawData[i].split(None, 14)[0]), str(rawData[i].split(None, 14)[eventIndex]), str(rawData[i].split(None, 13)[-1].split(' ',1)[1]).rstrip()]
                code.append('{0:<20} {1:<20} {2}'.format(*buff))
            i += 1
        # Writing to the ouput file for this hotspot
        # TODO: Add file name to indivOutputFile by searching up until file is found
        indivOutputFile = indivOutputDir + "top" + str(j+1) + ".txt"
        with open(indivOutputFile, 'a') as out:
            # Prepare the header to the output file
            percOfTotal = str(float(hotList[j][1])/float(totalEvents)*100.0)
            header = "--------------------------------------------------------------------------------------------------\n"
            header = header + "--- Hot Instruction Number " + str(j+1) + " has " + str(hotList[j][1]) + " events associated with it (" + percOfTotal[0:5] + " % of total events) ---\n"
            header = header + "--------------------------------------------------------------------------------------------------\n"
            header = header + source + "\n"
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
        # Iteratively update the final summary file
        with open(summaryOutputFile, 'a') as out:
            value = rawData[hotList[j][0]].split(None, 14)[eventIndex]
            value = value.replace(',' , '') if value != '.' else '0'
            percent = float(value)/float(totalEvents) * 100.0
            percAccum += percent
            eventAccum += int(value)
            percentstr = str(percent)[0:5] + " %"
            # Similar buffer to before, only including the percentage
            buff = [str(rawData[hotList[j][0]].split(None, 14)[0]), str(rawData[hotList[j][0]].split(None, 14)[eventIndex]), percentstr, str(rawData[hotList[j][0]].split(None, 14)[-1].rstrip())]
            out.write('{0:^20} {1:^20} {2:^20} {3}'.format(*buff))
            out.write('\n')

    # Finish the summary file
    with open(summaryOutputFile, 'a') as out:
        footer = "-------------------------------------------------------------------------------------------------\n"
        out.write(footer)
        footer = ['TOTALS', str(eventAccum), str(percAccum)[0:5] + ' %',' ']
        out.write('{0:^20} {1:^20} {2:^20} {3}'.format(*footer))
        out.write('\n')
    sys.stdout.write("done\n")

#########################################
#      DEFINE ABSOLUTE DIRECTORIES      #
#########################################
# Absolute path to the workspace
baseOperatingDir = "/local/alec/cole_workspace/"
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
sys.stdout.write("Parsing directory arg...")
if (len(sys.argv) != 2):
    USAGE = ("\nUSAGE\t:\n" +
            "\t\"python vgSpec2017GetResults.py <1>\"\n" +
            "\t<1> = The name of the directory of the run's results (i.e. \"3_21_vgRun\")")
    print USAGE
    quit()
else:
    vgSpecThisResultsDir = vgResultDir + sys.argv[1] + "/"
    vgSpecThisResultsRaw = vgSpecThisResultsDir + "raw/"
    vgSpecThisResultsAnn = vgSpecThisResultsDir + "annotated/"
    vgSpecThisResultsFmt = vgSpecThisResultsDir + "formatted/"
    # Make the raw and annoted directories as well as the temporary
    sys.stdout.write("done\n")
    prepResultsFolder(vgSpecThisResultsDir, vgSpecThisResultsRaw, vgSpecThisResultsAnn, vgSpecThisResultsFmt)

#########################################
#        ANNOTATION OF RESULTS          #
#########################################
# Walk through all of the results files and annotate
files = os.listdir(vgSpecThisResultsRaw)
pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
sys.stdout.write("Annotating all results...")
for file in files:
    if fnmatch.fnmatch(file, pattern):
        # NOTE: This annotate is not going to work locally because we do not have the source locally, so we cannot test it locally
        annotateCmd = "cg_annotate --auto=yes " + vgSpecThisResultsRaw + file + " > " + vgSpecThisResultsAnn + file
        annotateRes = subprocess.Popen(annotateCmd, shell = True)
        annotateRes.communicate()
sys.stdout.write("done\n")

#########################################
#          SORTING OF RESULTS           #
#########################################
# Walk through all of the results files and annotate
files = os.listdir(vgSpecThisResultsAnn)
pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
data = [] # Holds the entire text dump of the annotated results
sys.stdout.write("Reformatting annotated results...")
for file in files:
    if fnmatch.fnmatch(file, pattern):
        data = open(vgSpecThisResultsAnn + file).readlines()
        # Prepend a line number to each line
        i = 0
        for line in range(len(data)):
            data[line] = str(i) + "\t" + data[line]
            i += 1
        # Write the formatted data back to the file
        with open(vgSpecThisResultsAnn + file, 'w') as updatedData:
            for item in data:
                updatedData.write(item)
sys.stdout.write("done\n")

# Analyze the hotspots for every benchmark
files = os.listdir(vgSpecThisResultsAnn)
pattern = "*.*.txt" # All result files must be of the form ###.bmk_name.txt
for file in files:
    # Only do analysis if there is an annotated copy
    if fnmatch.fnmatch(file, pattern):
        # Prepare the function call
        bmkName = file[0:-4]
        resultToAnalyze = vgSpecThisResultsAnn + file
        indivOutputDir = vgSpecThisResultsFmt + bmkName +"/cache/"
        summaryOutputFile = indivOutputDir + "summary.txt"
        eventToAnalyze = "DLmr"
        percentToAnalyze = .90
        regionToAnalyze = 30
        # Do the analysis on DLmr
        analyzeHotspots(bmkName, resultToAnalyze, indivOutputDir, summaryOutputFile, eventToAnalyze, percentToAnalyze, regionToAnalyze)
        # Do the analysis on Bcm
        indivOutputDir = vgSpecThisResultsFmt + bmkName + "/branch/"
        summaryOutputFile = indivOutputDir + "summary.txt"
        eventToAnalyze = "Bcm"
        analyzeHotspots(bmkName, resultToAnalyze, indivOutputDir, summaryOutputFile, eventToAnalyze, percentToAnalyze, regionToAnalyze)
sys.stdout.write("Job has completed. Please see the results folder for this run.\n")

#########################################
#           UNUSED FUNCTIONS            #
#########################################

# The following functions are currently unsued in this framework.
# However, they have been verified to be working and may be useful in
# the future.
#
# We decided to do the analysis with respect to DLmr and Bcm only, so
# there is no need to really interface with the user. In the event user
# input is desired at some point, these should help get the job done.
#
# We have left them in for this reason.

# *** THIS FUNCTION IS UNUSED ***
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

# *** THIS FUNCTION IS UNUSED ***
# Interfaces with the user to understand how the data should be processed for
# further analysis
# ARGS: the working directory of the results being analyzed
# RETURNS: the event the user cares about and wants to do analysis with respect to
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
        sortAgainCheck = raw_input("Sort by different event? [y/n] ")
        if (sortAgainCheck == 'y'):
            continue
        elif (sortAgainCheck == 'n'):
            sortConfirm = raw_input("Confirm that you would like to process hotspots of events: "+ sortEvent + " [y/n] ")
            if(sortConfirm == 'y'):
                sortAgain = False
            else:
                continue
        else:
            continue
    return sortEvent
