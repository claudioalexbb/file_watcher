import time
import requests
import json
import glob
import os
from datetime import datetime

# set the update/upload interval
UPDATE_INTERVAL = 10 # default: every 10s

firstErrorTime = ""
errorCount = 0
execTime = datetime.now().strftime("%Y%M%d%H%M%S")

### function to send post message in discord
def post_message(msg, url):
    global firstErrorTime
    global errorCount
    global execTime
    data = ""
    if type(msg) is str:
        data = json.dumps({"content": msg}, separators=(',', ':'))
    else:
        data = json.dumps(msg, separators=(',', ':')) 
    headers = {'Content-Type': 'application/json'}
    while True:
        r = requests.post(url, headers=headers, data=data)
        if r.status_code >200 and r.status_code < 205:
            return # message was sent with success, exit loop
        if "retry_after" in r.json():
            time.sleep(float(r.json()["retry_after"]))
        else:
            # if error count reach's 5 with 5 seconds we should stop the script as something is very very wrong
            # and discord may ban the IP for spamming
            if errorCount > 4:
                exit("We had 5 errors in less than 5 seconds! check file_watcher.log for details.")
            currentTime = datetime.now()
            if errorCount == 0:
                firstErrorTime = currentTime
            if firstErrorTime != "" and (currentTime - firstErrorTime).seconds > 5:
                firstErrorTime = "" # reset the error counter if first error was more than 5 seconds ago
                errorCount = 0
            else:
                errorCount = errorCount + 1
            with open(f"file_watcher_{execTime}.log", "a") as f:
                f.write(f"Error sending message ({msg}) to {url}:\r")
                f.write(r.text + "\r")

### function to find the correct file to read
def findMatchingFile(path,filename):
    if path[-1:] == "/":
        path = path[:-1]
    list_of_files = glob.glob(f'{path}/{filename}')
    if len(list_of_files) < 1:
        return None 
    return max(list_of_files, key=os.path.getctime)

### read file contents
def file_read(file, linecount = -1):
    try:
        with open(file,'r') as f:
            if linecount == -1: # initial read
                linecount = 0
                while True:
                    line = f.readline()
                    if not line:
                        break
                    linecount += 1
                print(f"file {file} had {linecount} 'old' lines that are not processed.")
                return (linecount, [])
            else:
                with open(file,'r') as f:
                    newcount = 0
                    line = ""
                    lines = []
                    while newcount < linecount:
                        line = f.readline()
                        newcount += 1
                    lines = f.readlines()
                return (newcount, lines)
    except Exception as e:
        print(e)
        exit(f'file {file} was not found!')

### apply keyword filters
def filterNewLines(line,includes,excludes):
    # first excludes
    for key in excludes:
        if key.lower() in line.lower():
            return None
    # now includes
    if len(includes) == 0: #no include filter, meaning, include all
        return line
    for key in includes:
        if key.lower() in line.lower():
            return line
    # not excluded by exclusions and not included by inclusions...return None
    return None
        

### START POINT
config = ""
try:
    with open("file_watcher_config.json","r") as f:
        config = json.load(f)
except Exception as e:
    print(f"Could not read configuration file (file_watcher_config.json) do to error below")
    exit(e)

if len(config) <1:
    exit("Configuration (file_watcher_config.json) is empty!")

# read the initial line count for each file and add current line to the config var
index = 0
for entry in config:
    fileWithPath = None
    waitTime = 0
    while fileWithPath == None and waitTime < 600:
        fileWithPath = findMatchingFile(entry["filePath"],entry["baseFilename"])
        print(f'file for filter "{entry["baseFilename"]}" not found. waiting more {600-waitTime}s...')
        time.sleep(5) # the server is probably not running yet, we will wait...
        waitTime = waitTime + 5
    if fileWithPath != None:
        linecount, lines = file_read(fileWithPath)
        config[index]["currentFile"] = fileWithPath
        config[index]["currentLine"] = linecount
    else:
        config[index]["currentFile"] = None
        config[index]["currentLine"] = 0

    index = index + 1

print("\nwatching all files for new lines...\n")
print("CTRL+C to stop program or close window")
## now cycle continuously each file searching for new lines
while True:
    index = 0
    for entry in config:
        linecount = entry["currentLine"]
        newLines = []
        fileWithPath = entry["currentFile"]
        if entry["canHaveMultipleFiles"]:
            fileWithPath = findMatchingFile(entry["filePath"],entry["baseFilename"])
        if fileWithPath != None:
            if entry["currentFile"] != fileWithPath: # a new file was generated! need to start reading new file
                config[index]["currentFile"] = fileWithPath
                config[index]["currentLine"] = 0
                linecount = 0
            (linecount, newLines) = file_read(fileWithPath, linecount)
            if len(newLines)> 0: # there are new lines in the files
                #update line pointer
                config[index]["currentLine"] = linecount + len(newLines)
                linesToPost = ""
                for line in newLines:
                    #post new lines to discord
                    if len(entry["keywords"]["include"]) == 0 and len(entry["keywords"]["exclude"]) == 0:
                        if linesToPost == "":
                            linesToPost = line
                        else:
                            if len(linesToPost) + len(line) > 1999:
                                post_message(linesToPost, entry["channel_webhook"])
                                linesToPost = ""
                            linesToPost = linesToPost + line
                    else:
                        line = filterNewLines(line,entry["keywords"]["include"],entry["keywords"]["exclude"])
                        if line != None:
                            if linesToPost == "":
                                linesToPost = line
                            else:
                                if len(linesToPost) + len(line) > 1999:
                                    post_message(linesToPost, entry["channel_webhook"])
                                    linesToPost = ""
                                linesToPost = linesToPost + line
                if linesToPost != "":
                    post_message(linesToPost, entry["channel_webhook"])
        index = index + 1
    time.sleep(UPDATE_INTERVAL)