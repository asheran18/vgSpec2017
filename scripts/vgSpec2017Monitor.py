#*************************************************************
#
# SPEC 2017 Bottleneck Analysis (Valgrind and SPEC2017)
#
# Intended to manage individual valgrind simulations of the
# SPEC2017 bencmarks. Writes the current status of the benchmark
# to the referenced met log file.
#
# Args to this script
#   1) The full path of the dirctory of the benchmark executable
#   2) The full path of the meta log file for signaling the status of this benchmark
#   3) The full path of the file to store the results for this benchmark
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

import os
import datetime
import time
import subprocess
import sys
import random


# Args to this script
#   1) The full path of the dirctory of the benchmark executable
#   2) The full path of the meta log file for signaling the status of this benchmark
#   3) The full path of the file to store the results for this benchmark
# Process CLA
if (len(sys.argv) != 4):
    print ("USAGE\t:\n(1) The absolute path to the benchmark executable folder\n"+
                     "(2) The absolute path to the benchmark meta log file\n"+
                     "(3) The absolute path of the file to store the results for this benchmark")
    quit()
else:
    benchmarkExeDir = sys.argv[1]
    benchmarkLogFile = sys.argv[2]
    benchmarkResFile = sys.argv[3]

# Set up necessary absolute paths (taken from vgSpec2017Manager.py)
# Absolute path to the workspace
baseOperatingDir = "/local/alec/cole_workspace/"
vgSpecDir = baseOperatingDir + "vgSpec2017/"
#vgSpec2017 Subdirectories
vgScriptsDir = vgSpecDir + "scripts/"
vgLogsDir = vgSpecDir + "logs/"
vgLogFile = vgLogsDir + "logfile.txt"
vgBenchDir = vgSpecDir + "benchmarks/"
vgResultDir = vgSpecDir + "results/"
vgExeCmdFile = "speccmds.cmd" # Expected in the benchmarkExeDir directory passed in


# Initialize the meta log file
metaLogFile = open(benchmarkLogFile, "wr")
metaLogStartStr = "Running...\n" + "Executing benchmark in folder: " + benchmarkExeDir + "\n"
metaLogFile.write(metaLogStartStr)
metaLogFile.close()

# # DEBUG - vgSpec2017Manager verification
# emulateTime = random.randint(1,20)
# time.sleep(emulateTime)
# resFile = open(benchmarkResFile, "wr")
# os.chdir(benchmarkExeDir)
# cwd = "Operated out of directory: " + os.getcwd()
# resFile.write(cwd)
# resFile.write("I slept for " + str(emulateTime) + " seconds\n")
# resFile.close()
# metaLogFile = open(benchmarkLogFile, "wr")
# metaLogFile.write("Done\n")
# metaLogFile.close()
# quit()

# Change directories and prepare the run by getting the executable command
os.chdir(benchmarkExeDir)
with open(vgExeCmdFile) as f:
    commands = f.readlines()
exeCommand = ""
copyDone = False;
for cmd in commands:
    if ((cmd[0:2] == "-o" or cmd[0:2] == "-i") and not copyDone):
        # Once the -o or -i flag is seen, get the command from the line (and just the command)
        i = 0
        exeCommand = ""
        copyStart = False;
        for i in range(len(cmd)):
            if(cmd[i:i+3] == "../"):
                copyStart = True;
                exeCommand = exeCommand + cmd[i]
            elif(cmd[i:i+2] == " >"):
                copyDone = True
                break;
            elif(copyStart):
                exeCommand = exeCommand + cmd[i]

# # DEBUG - Command generation verification
# resFile = open(benchmarkResFile, "wr")
# resFile.write(exeCommand)
# resFile.close()
# metaLogFile = open(benchmarkLogFile, "wr")
# metaLogFile.write("Done\n")
# metaLogFile.close()
# quit()

# Start valgrind on the benchmark
with open(benchmarkLogFile, 'w') as output:
    valgrindCmd = "valgrind --tool=cachegrind --branch-sim=yes --LL=2097152,16,64 --cachegrind-out-file=" + benchmarkResFile + " " + exeCommand
    StartSimCmd = valgrindCmd + " &"
    StartSim = subprocess.Popen(StartSimCmd, stdout=output, stderr=subprocess.STDOUT, shell=True)
    StartSim.communicate()

# Constantly check output file for keyword "LL miss rate:" which asserts whether the trace is done or not.
DoneFlag = False
while(1):
    txtfile = open(benchmarkLogFile, 'r')
    lines = txtfile.readlines()
    txtfile.close()
    for line in lines:
        if line.find("LL miss rate:") != -1:
            DoneFlag = True
            break
    if DoneFlag != True:
        time.sleep(3)
    else:
        break

# Let the manager know that I have finished
metaLogFile = open(benchmarkLogFile, "r+b")
metaLogFile.seek(0,0)
metaLogFile.write("Done     \n") # Added the extra spaces to make it look nice - no functional impact
metaLogFile.close()
sys.exit()
