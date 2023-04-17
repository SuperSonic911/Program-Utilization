import os
import getpass
import psutil
import datetime
import time
import math
import socket
import csv
import pandas as pd

# for debugging purposes, clears command line every time program runs
os.system('cls' if os.name == 'nt' else 'clear')

# Gets User Name of PC
user_name = getpass.getuser()
# Gets Computer Name
computer_name = socket.gethostname()


# import list of programs from a text file called monitored_programs.txt
try:
    with open("monitored_programs.txt") as f:
        # contains names of programs i.e. Taskmgr.exe
        monitored_programs = []
        # contains version i.e. System32
        versions = []
        while True:
            line = f.readline()
            if not line:
                break
            # store as program.exe, for example Spotify.exe or Taskmgr.exe
            monitored_programs.append(line.strip().replace('"', '').split("\\")[-1])
            # containig folder of program is the version, for example System32
            versions.append(line.split("\\")[-2])
except FileNotFoundError:
    print("Please make sure monitored_programs.txt exists in the same file path as the script")
    input("Press any key to exit")

# if txt file is mounted successfully, go to monitoring function
try:
    if monitored_programs[0]:
        print("Monitoring...")
except IndexError:
    print("Please make sure monitored_programs.txt contains valid file paths, each on a seperate line")
    input("Press any key to exit")

def monitor(monitored_programs, versions):
    for i in range(len(monitored_programs)):
        try:
            # Get a list of all running processes 
            processes = psutil.process_iter() 

            # Iterate through each process and get its name, start time and total CPU time
            for proc in processes:
                # available name of process
                name = proc.name()
                # if process is running, get it's information
                if name == monitored_programs[i]:  
                    # when did the process start, starting point of utilization time  
                    start_time = proc.create_time()
                    # format as date and time
                    start_time_formatted = datetime.datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
                    # get the time on this pc since epoch, ending point for utilization time till this insant
                    time_now = time.time() 
                    # round and subtract difference between 2 time points
                    utilization_time = math.trunc(time_now - start_time)
                    # formatted in HH:MM:SS
                    utilization_time_formated = datetime.timedelta(seconds=utilization_time)
                    
                    # creating the dataframe, that will be added to csv
                    dict = {
                    "User_Name": [user_name],
                    "Computer_Name": [computer_name],
                    "Version": [versions[i]],
                    "Program_Name": [monitored_programs[i]],
                    "Date_Used": [start_time_formatted],
                    "Utilization_Time": [utilization_time_formated],
                    "Initializations_of_program": [1]
                    }

                    df = pd.DataFrame(dict)	

            # name of created csv = name of program
            file_name_csv = monitored_programs[i].strip(".exe") + ".csv"
            path_csv = "./Log of CSVs/" + file_name_csv

            # if file exists, append to it
            if os.path.isfile(path_csv):
                # compare previous results to current results
                stored_info_df = pd.read_csv(path_csv)
                previous_session_start_time = stored_info_df.iloc[-1, 4]
                # if previous = new, that means we are still in the same session, so keep updating utilization time live
                if previous_session_start_time == start_time_formatted:
                    # modify current session time since last
                    stored_info_df.iloc[-1, 5] = utilization_time_formated
                    # store information in same place
                    stored_info_df.to_csv(path_csv, index=False)

                # if last entry is different from the previous, that means file has been launced again, append new row (new session)
                else:
                    # add 1 to number of initializations
                    no_of_initializations = stored_info_df.iloc[-1, 6]
                    no_of_initializations += 1
                    # modify it in original csv cell
                    df.iloc[0, 6] = no_of_initializations
                    # add new session of usage, if program is launched again
                    df.to_csv(path_csv, mode="a", index=False, header=False)
            
            # file doesn't exist, create it and initiliaze it with a row of information
            else:
                try:
                    os.makedirs("./Log of CSVs/")
                except FileExistsError:
                    pass
                df.to_csv(path_csv, index=False)
                print(f'{file_name_csv} successfully created for monitoring')
        except (PermissionError, NameError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

# combine all seperate programs into a central CSV
def combine_csv():
    # assign directory of logged csvs
    directory = "./Log of CSVs"
    # create an empty combined.csv in the same directory as script, to append to it, all CSVs in log of CSVs
    with open("combined.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        # write the header row
        writer.writerow(["User_Name",
                        "Computer_Name",
                        "Version",
                        "Program_Name",
                        "Date_Used",
                        "Utilization_Time",
                        "Initializations_of_program"])
    # iterate over files in log of CSVs
    for filename in os.listdir(directory):
        path_csv = os.path.join(directory, filename)
        # checking if it is a file
        if os.path.isfile(path_csv):
            df = pd.read_csv(path_csv)
            #df.sum(axis="Utilization_Time")  
            # append rows to combined.csv
            df.to_csv("combined.csv", mode="a", index=False, header=False)

while (True):
    time.sleep(3)
    monitor(monitored_programs, versions)
    time.sleep(1)
    combine_csv()
    