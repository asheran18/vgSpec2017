#*************************************************************
#
# SPEC 2017 Bottleneck Analysis (Valgrind and SPEC2017)
#
# Intended to manage valgrind simulations of the SPEC2017 bencmarks.
#
# NOTE: If we did not have as much control over these parameters
# as we do, much more error handling would be needed to ensure
# safe operation. For our purposes, however, this would be trivial
# since the application this is intended for is highly controled.
#
# If this program were desired to be made into a universal tool
# for process management at large, these error handling protocols
# should be implemented.
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
from collections import deque


#########################################
#           UTILITY FUNCTIONS           #
#########################################
# Finds the most recently run directory in a given path
# Expects standard spec2017 run directory format: "run_base_ref<type>_<configname>.<4digitnumber>"
def findMostRecentExeDir(pathToParentDir):
    children = os.listdir(pathToParentDir)
    currentGuessDir = children[0]
    currentGuessNum = int(currentGuessDir[-4:])
    for child in children:
        # By convention, the directory will start with "run" and end in a 4 digit ID
        if (child[0:3] == "run"):
            runDirNum = child[-4:]
            if (int(runDirNum) > currentGuessNum):
                currentGuessNum = int(runDirNum)
                currentGuessDir = child
    return currentGuessDir

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
# Spec 2017 Subdirectories
spec2017BenchmarksDir = spec2017Dir + "benchspec/CPU/"
spec2017RunDir = "run/" # NOTE: relative path - but its the same for every bmk
#spec2017ExeDir = spec2017RunDir + "run_base_refrate_mytest-m64.0000/" # NOTE: relative path - but its the same for every bmk

#########################################
#          ENVIRONMENT SETUP            #
#########################################
# Clean the benchmark folder
cleanDirCmd =  "rm -r " + vgBenchDir + "*"
cleanDir = subprocess.Popen(cleanDirCmd, shell = True)
cleanDir.communicate()
# Clean the logs folder
cleanDirCmd =  "rm -r " + vgLogsDir + "*"
cleanDir = subprocess.Popen(cleanDirCmd, shell = True)
cleanDir.communicate()
# Locate all benchmark directories in spec2017BenchmarksDir -------- TODO: GCC nonexistent but folder made anyways
for root, dir, file in os.walk(spec2017BenchmarksDir):
    for dirs in dir:
        # Check if this is a bmk directory - it will start with 3 numbers
        if (dirs[0].isdigit() and dirs[1].isdigit() and dirs[2].isdigit()):
            # Hardcoded avoidance of gcc - remove this check if no known issues with any benchmarks
            if (dirs != "602.gcc_s" and dirs != "502.gcc_r"):
                # Make a local folder for this
                makeBmkDirCmd =  "mkdir -m 777 " + vgBenchDir + dirs
                makeBmkDir = subprocess.Popen(makeBmkDirCmd, shell = True)
                makeBmkDir.communicate()
                # Copy the run directory to the local benchmark folder
                copyRunDirCmd = "cp -r " + spec2017BenchmarksDir + dirs + "/" + spec2017RunDir + " " + vgBenchDir + dirs + "/"
                copyRunDir = subprocess.Popen(copyRunDirCmd, shell = True)
                copyRunDir.communicate()

#########################################
#          INITIALIZE RESULTS           #
#########################################
# Create Parent Directory to house simulation results in ../results/ folder - name is <day_month_sim>
vgSpecThisResultsDir = str(datetime.datetime.now().month) + "_" + str(datetime.datetime.now().day) + "_vgRun"
# If this isnt the first sim today
copy = 1
appender = ""
checker = vgSpecThisResultsDir
for root, dir, file in os.walk(vgResultDir):
    for dirs in dir:
        if dirs == checker:
            appender = "_" + str(copy)
            copy = copy + 1
            checker = vgSpecThisResultsDir + appender
# Make directory
if appender != "":
    vgSpecThisResultsDir = vgResultDir + vgSpecThisResultsDir + appender + "/"
else:
    vgSpecThisResultsDir = vgResultDir + vgSpecThisResultsDir + "/"
makeResDirCmd =  "mkdir -m 777 " + vgSpecThisResultsDir
makeResDir = subprocess.Popen(makeResDirCmd, shell = True)
makeResDir.communicate()

#########################################
#         START VGSPEC2017 RUN          #
#########################################
# Record starting time
startTime = time.time()
# Init logfile
logFile = open(vgLogFile, 'wr')
logFile.write("\n*************** <> STARTING VGSPEC2017 RUN <> ***************\n\nBENCHMARK SCHEDULING BEGIN\n")
logFile.close()
# Start valgrind on every benchmark
benchmarkList = os.listdir(vgBenchDir)
benchmarkLogList = []
for benchmark in benchmarkList:
        logFile = open(vgLogFile, 'a')
        # Create the meta log for this benchmark and remember the path
        logFile.write("Creating log file for benchmark " + benchmark + "...\n")
        thisBenchmarkLog = vgLogsDir + benchmark + "_log.txt"
        bmkLog = open(thisBenchmarkLog, 'wr')
        bmkLog.write("Scheduled...\n")
        bmkLog.close()
        benchmarkLogList.append(thisBenchmarkLog)
        # Get the executable path for this benchmark
        # First need to get the actaul executable directory of the form "run_base_refrate_mytest-m64.0000/"
        # Obviously the name could change from config file to config file, but "run_base" should stay the same
        thisRunDir = vgBenchDir + benchmark + "/" + spec2017RunDir
        mostRecentExeDir = findMostRecentExeDir(thisRunDir)
        thisBenchmarkExeDir = vgBenchDir + benchmark + "/" + spec2017RunDir + mostRecentExeDir
        # Get the results file name
        thisBenchmarkResFile = vgSpecThisResultsDir + benchmark + ".txt"
        # Start the monitor on this benchmark - args are (1) this benchmark exe path (2) this log file to write to (3) the results directory
        MonitorCmd = "python " + vgMonitorSubprocScript + " " + thisBenchmarkExeDir + " " + thisBenchmarkLog + " " + thisBenchmarkResFile
        logFile.write("Starting benchmark " + benchmark + "\n")
        Monitor = subprocess.Popen(MonitorCmd, shell = True)
	    Monitor.communicate()
logFile.write("BENCHMARK SCHEDULING END\n\n")
logFile.close()


#########################################
#         MANAGE THE PROCESSES          #
#########################################
# Poll the log files for completion signals until run is complete
completedBenchmarks = []
while True:
    for log in benchmarkLogList:
        # print completedBenchmarks
        checkedLog = open(log, 'r')
        bmkStatus = checkedLog.readline()
        checkedLog.close()
        bmkStatus = bmkStatus.rstrip()
        # By convention, the firts line of the meta log will read "Benchmark Done"
        if (bmkStatus == "Done" and log not in completedBenchmarks):
            completedBenchmarks.append(log)
            # Update the overall run completion percentage
            logFile = open(vgLogFile, 'a')
            percentComplete = (float(len(completedBenchmarks)) / float(len(benchmarkLogList))) * 100.00
            percentCompleteStr = str(percentComplete)
            timeOfCompleteStr = str((time.time() - startTime)/3600)
            notifyCompleteStr = "Benchmark logged in " + log + " has completed with a runtime of " + timeOfCompleteStr[:5] + " hours\n"
            complPcntStr = percentCompleteStr[:5] + "% of jobs completed at " + timeOfCompleteStr + " elapsed hours\n"
            updateStr = notifyCompleteStr + complPcntStr
            logFile.write(updateStr)
            logFile.close()
        # Check if all benchmarks have completed and been processed
        if (len(completedBenchmarks) == len(benchmarkLogList)):
            totalRunTime = str((time.time() - startTime)/3600)
            runCompleteStr = "All benchmarks complete. Total run time was " + totalRunTime + " elapsed hours\n"
            endRunStr = "\n\n*************** <> ENDING VGSPEC2017 RUN <> ***************\n"
            finalStr = runCompleteStr + endRunStr
            logFile = open(vgLogFile, 'a')
            logFile.write(finalStr)
            logFile.close()
            # If the run is done, quit
            quit()
    # Should give some time before checking again
    time.sleep(3)
