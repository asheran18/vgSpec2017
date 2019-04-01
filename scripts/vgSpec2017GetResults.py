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
import pandas as pd
import fnmatch

#########################################
#           UTILITY FUNCTIONS           #
#########################################
# Formats the results folder into raw valgrind outputs and annotated ones
# Expects 4 args: the root results directory, the raw results directory to make,
# the annotated results directory to make, and a temporary copy of the annotated results
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
    print ("USAGE\t:\n(1) The name of the dirctory of the run's results (i.e. \"3_21_vgRun\")")
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
        #
        # Do some more processing
        #
        # Write the formatted data back to the file
        with open(vgSpecThisResultsTmp + file, 'w') as updatedData:
            for item in data:
                updatedData.write(item)
