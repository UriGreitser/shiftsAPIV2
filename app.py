from flask import Flask, request, jsonify, Response,send_file
import csv
import io
import json
from classes import Shift,Worker
import random
import csv
import pandas as pd
import functools
import os
import time

app = Flask(__name__)
stored_name = None
global_config = None
global_prefrences = None

prefrences_file = 'pref.csv'
config_file = 'config.csv'



shift_config = None
def csv_to_json_test(file_path):
    json_data = {}
    full_json = {}
    test_json = {}
    
    with open(file_path, mode="r", newline="") as csvfile:
        csvreader = list(csv.reader(csvfile))  # Read all rows into a list
        
        # Skip the first line
        rows = csvreader[1:]
        
        # Process the first 3 rows with 7 elements each
        for row_idx, row in enumerate(rows[:5], start=1):
            row_data = row[1:]  # Skip the first item in each row

            if row_idx == 1:
                add_to_json_key = 1
                for i in range(0,7):
                    if int(row_data[i])!=2:
                        test_json[f'{add_to_json_key}'] = int(row_data[i])
                    add_to_json_key+=3
            if row_idx == 2:
                add_to_json_key=2
                for i in range(0,7):
                    if int(row_data[i])!=2:
                        test_json[f'{add_to_json_key}'] =  int(row_data[i])
                    add_to_json_key+=3
            if row_idx == 3:
                add_to_json_key=3
                for i in range(0,7):
                    if int(row_data[i])!=2:
                        test_json[f'{add_to_json_key}'] =  int(row_data[i])
                    add_to_json_key+=3
            if row_idx == 4:
                if int(row_data[0])!=2:
                    test_json["22"] =  int(row_data[0])
            if row_idx == 5:
                if int(row_data[0])!=2:
                    test_json["23"] =  int(row_data[0])

                    
                # for i in range(1,8):  # Process the first 3 lines with 7 elements after skipping the first one
                #     cell_value = row_data[i-1]
                #     if cell_value != "2":
                #         json_data[f"{(row_idx - 1) * 7 + i}"] = int(cell_value)  # Numbering from 1 to 21
            # elif row_idx <= 5:  # Process the next 2 lines with 1 element each
            #     cell_value = row_data[0]  # After skipping the first item, take the only element
            #     line_number = 21 + (row_idx - 3)  # Line 22 for the 4th row, line 23 for the 5th row
            #     if cell_value != "2":
            #         json_data[f"{line_number}"] = int(cell_value)  # Add to JSON with number 22 or 23

        # Now process the "Hardcoded Shifts" line (6th line)
        hardcoded_shifts = []
        hardcoded_row = rows[5][1:]  # The 6th line, skipping the first element
        for cell in hardcoded_row:
            if not cell:  # Stop when an empty cell is encountered
                break
            hardcoded_shifts.append(str(cell))  # Add each cell value to the list as a string

        full_json["hard_coded_shifts"] = hardcoded_shifts  # Add the list of shifts to the JSON
        # Adding data to full_json
    full_json["amount_of_workers_to_allocate_by_default"] = 2
    full_json["amount_of_workers_to_allocate_specific_shifts"] = json.dumps(test_json)
    return json.dumps(full_json, indent=4)

# shift_config = {
#     "amount_of_workers_to_allocate_by_default": 2,
#     "hard_coded_shifts": ["Nitay-Monday Morning"],
#     "amount_of_workers_to_allocate_specific_shifts": {
#         "Sunday Night": 1,
#         "Monday Night": 1,
#         "Tuesday Night": 1,
#         "Wednesday Night": 1,
#         "Thursday Night": 1,
#         "Friday Night": 1,
#         "Saturday Night": 1,
#         "Thursday Evening": 1,
#         "Sunday Middle": 1,
#         "Saturday Middle": 1,
#         "Saturday Evening": 1
#     }
# }
# "Monday Morning": 1,

# prefrences_file = 'latest_pref.csv'

API_TOKEN = "videotoken123" 

#mapping between numbers and shifts
def replace_shift_keys(input_json):
    # Define the reverse mapping for each day and shift name to shift number
    reverse_shift_mapping = {
        "Sunday Morning": "1",
        "Sunday Evening": "2",
        "Sunday Night": "3",
        "Monday Morning": "4",
        "Monday Evening": "5",
        "Monday Night": "6",
        "Tuesday Morning": "7",
        "Tuesday Evening": "8",
        "Tuesday Night": "9",
        "Wednesday Morning": "10",
        "Wednesday Evening": "11",
        "Wednesday Night": "12",
        "Thursday Morning": "13",
        "Thursday Evening": "14",
        "Thursday Night": "15",
        "Friday Morning": "16",
        "Friday Evening": "17",
        "Friday Night": "18",
        "Saturday Morning": "19",
        "Saturday Evening": "20",
        "Saturday Night": "21",
        "Saturday Middle": "22",
        "Sunday Middle": "23"
    }
    # Copy the input JSON to avoid modifying the original
    output_json = input_json.copy()
    
    # Get the specific shifts dictionary from the input JSON
    specific_shifts = input_json.get("amount_of_workers_to_allocate_specific_shifts", {})
    
    # Create a new dictionary with the updated keys
    updated_shifts = {}
    for shift_label, workers in specific_shifts.items():
        # Replace the day and shift with the corresponding number
        shift_number = reverse_shift_mapping.get(shift_label, f"Unknown shift {shift_label}")
        updated_shifts[shift_number] = workers
    
    # Replace the old specific shifts with the updated shifts in the output JSON
    output_json["amount_of_workers_to_allocate_specific_shifts"] = updated_shifts
    
    return output_json

# Simple utility function to check the token
def token_required(f):
    @functools.wraps(f)  # This preserves the original function's name and metadata
    def wrap(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token != f"Bearer {API_TOKEN}":
            return jsonify({'error': 'Unauthorized access, invalid token'}), 401
        return f(*args, **kwargs)
    return wrap



def AmountOfShiftsToAllocateAtStart(list_of_shifts) -> int:
    amount = 0
    for shift in list_of_shifts:
        amount += shift.amount_of_workers_to_allocate_no_changes
    return amount

def PrintWorkersAndTheirShifts(list_of_workers):
    #print shifts for every worker
    for worker in list_of_workers:
        print("--------------------------------------------------")
        print(worker.name, ":")
        for shift_of_worker in worker.shifts_assigned:
            print(Shift.PrintShiftIDByDayAndTime(shift_of_worker))

def AddWorkersAndTheirShiftsToStats(list_of_workers, stats):
    # Define the custom sorting order for days of the week
    day_order = {
        "Sunday": 1,
        "Monday": 2,
        "Tuesday": 3,
        "Wednesday": 4,
        "Thursday": 5,
        "Friday": 6,
        "Saturday": 7
    }
    
    # Add shifts for every worker to the stats
    for worker in list_of_workers:
        # Create a list of shifts for the worker
        worker_shifts = []
        for shift_of_worker in worker.shifts_assigned:
            # Add the shift information to the list
            shift_info = Shift.PrintShiftIDByDayAndTime(shift_of_worker)
            worker_shifts.append(shift_info)
        
        # Sort the shifts based on the day of the week (first word)
        worker_shifts.sort(key=lambda shift: day_order.get(shift.split()[0], 0))
        
        # Add the worker and their sorted shifts to the stats dictionary
        stats[worker.name] = worker_shifts

    return stats



#checks if all shifts are assigned to a worker that has not blocked them
def CheckAllShiftsAssigned(shifts):
    for shift in shifts:
        for worker in shift.list_of_workers:
            if shift.shift_id in worker.closed_shifts_no_changes:
                return False
    return True

def ReadFromGoogleSheets(prefrences_file):
    # print("TESTING")
    worker_list = []
    with open(prefrences_file, mode='r',encoding='utf-8') as file:
        reader = csv.reader(file)
        id = 100
        for row in reader:
            name = row[0]
            open_shifts = set()
            start = 1
            try:
                night_shifts_requested = int(float(row[8]))
                days_off_taken = int(float(row[9]))
                shifts_to_allocate = 5 - int(float(days_off_taken))
            except:
                print(row)
                print("FAIL")
            for i in range(1,8):
                pref = row[i]
                if pref == "Open":
                    open_shifts.update((start,start+1,start+2))
                    if i == 1:
                        open_shifts.add(23)
                    elif i == 7:
                        open_shifts.add(22)
                elif pref == "No Morning":
                    open_shifts.update((start+1,start+2))
                    if i == 1:
                        open_shifts.add(23)
                    elif i == 7:
                        open_shifts.add(22)
                elif pref == "No Evening":
                    open_shifts.update((start,start+2))
                elif pref == "No Night":
                    open_shifts.update((start,start+1))
                    if i == 1:
                        open_shifts.add(23)
                    elif i == 7:
                        open_shifts.add(22)
                elif pref == "No Morning and Evening": # only night
                    open_shifts.add(start+2)
                elif pref == "No Morning and Night": #only evening
                    open_shifts.add(start+1)
                    if i == 1:
                        open_shifts.add(23)
                    elif i == 7:
                        open_shifts.add(22)
                elif pref == "No Evening and Night": # only morning
                    open_shifts.add(start)
                elif pref == "Closed":
                    pass
                start += 3
            set_of_closed_shifts = OppositeToSetUntil21(open_shifts)
            worker = Worker(name=name,worker_id=id,num_shifts_left_to_assign=shifts_to_allocate,open_shifts_no_changes=open_shifts,closed_shifts_no_changes=set_of_closed_shifts,night_shifts_requested=night_shifts_requested)
            id += 1
            worker_list.append(worker)
    return worker_list


def CreateShiftsByConfigFile(shift_config,list_of_workers): # this isnt working right for shifts 22 and 23 - if i try to set them to 0 it doesnt.
    # print("TESTING")
    list_of_shifts = []
    config = json.loads(shift_config)
    # shift_config = replace_shift_keys(shift_config)
    #print("Allocating shifts again")
    print(shift_config)
    specific_shifts_dict = json.loads(config["amount_of_workers_to_allocate_specific_shifts"])
    if isinstance(specific_shifts_dict, str):
        specific_shifts_dict = json.loads(specific_shifts_dict)

    specific_workers_list = config["hard_coded_shifts"]
    # print("SPECIFIC SHIFTS DICT: ", specific_shifts_dict)
    # print("HERE?")
    # print(shift_config)``
    for i in range(1,24):
        if str(i) in specific_shifts_dict:
            amount_of_workers_to_allocate_no_changes =specific_shifts_dict[str(i)]
        else:
            amount_of_workers_to_allocate_no_changes = 2
        if i % 3 == 0:
            night_shift_bool = True
        else:
            night_shift_bool= False
        if i == 22 or i == 23:
            night_shift_bool = False
        shift = Shift(night_shift_bool,shift_id = i,amount_of_workers_to_allocate_no_changes=amount_of_workers_to_allocate_no_changes)
        list_of_shifts.append(shift)
        
    if len(specific_workers_list)==0:
        return list_of_shifts,[]


    return list_of_shifts,specific_workers_list


list_of_names1 = ["Nitay", "Uri"]
list_of_names_copy = [ "Nitay", "Niro", "Natan", "Idan", "Israel", "Sasha", "Evgeniy", "Uri"]
list_of_names = ["Nitay", "Niro", "Natan", "Idan", "Israel", "Sasha", "Evgeniy", "Uri"]
#write shifts to file

def GetShiftByID(list_of_shifts,shift_id):
    for shift in list_of_shifts:
        if shift.shift_id == shift_id:
            return shift
    return None

def WriteShiftsToFile(list_of_shifts,filename):
    with open(filename, "w") as file:
        for shift in list_of_shifts:
            x = Shift.ReturnShiftIDByDayAndTime(shift)
            file.write(str(shift.shift_id))
            file.write(str(x))
            file.write(str(shift.list_of_workers_by_name))
            file.write("\n")

def WriteShiftsToCSVFile(list_of_shifts,filename):
    days_of_week = ['Sunday','Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', ]
    shifts_by_time = {'Morning': [], 'Evening': [], 'Night': []}

    for shift in list_of_shifts:
        shift_time = Shift.GetShiftTime(shift)  # Assuming there's a function to get the time of the shift
        shift_day = Shift.GetShiftDay(shift)    # Assuming there's a function to get the day of the shift
        shift_info = f"{shift.list_of_workers_by_name}"
        
        if shift_time == 'Morning':
            shifts_by_time['Morning'].append(shift_info)
        elif shift_time == 'Evening':
            shifts_by_time['Evening'].append(shift_info)
        elif shift_time == 'Night':
            shifts_by_time['Night'].append(shift_info)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row with the days of the week
        writer.writerow(['Shift Type'] + days_of_week)
        
        # Write the morning, evening, and night shifts in their respective rows
        writer.writerow(['Morning'] + shifts_by_time['Morning'])
        writer.writerow(['Evening'] + shifts_by_time['Evening'])
        writer.writerow(['Night'] + shifts_by_time['Night'])
        try:
            writer.writerow(['Sunday middle shift'] + list_of_shifts[22].list_of_workers_by_name) #sunday middle shift id=23
            writer.writerow(['Saturday middle shift'] + list_of_shifts[21].list_of_workers_by_name) # saturday middle shift id = 22
        except:
            # PrintListOfShifts(list_of_shifts)
            print("ERROR - WRITE SHIFTS TO CSV FILE")



#print list of workers
def PrintListOfWorkers(list_of_workers):
    for worker in list_of_workers:
        Worker.PrintWorker(worker)

#print list of shifts
def PrintListOfShifts(list_of_shifts):
    for shift in list_of_shifts:
        Shift.PrintShift(shift)
        
#
def get_shift_by_id(shifts_list, shift_id) -> Shift:
    for shift in shifts_list:
        if shift.shift_id == shift_id:
            return shift
    return None  

def GetWorkerByName(list_of_workers,name):
    for worker in list_of_workers:
        if worker.name == name:
            return worker
    return None
# prints the list of workers by names
def PrintListOfWorkersByNames(list_of_workers):
    for worker in list_of_workers:
        print(worker.name)

# returns true if the shift is a weekend shift and false if not
def IsShiftAWeekendShift(shift) -> bool:
        if shift.shift_id > 15 and shift.shift_id <= 22:
            return True
        return False

# returns a set of shifts that the worker can not do per a specific shift
def ReturnSetOfBannedShiftsPerShift(shift) -> set:
    set_of_banned_shifts = []
    id = shift.shift_id
    if id == 22: 
        set_of_banned_shifts.extend((21,20,19,18))
    elif id == 23:
        set_of_banned_shifts.extend((1,2,3))
    elif id % 3 == 0: # night shift
        set_of_banned_shifts.extend((id-2,id-1,id+1))
    elif id % 3 == 1: # morning shift
        set_of_banned_shifts.extend((id-1,id+1,id+2))
    else: # evening shift
        set_of_banned_shifts.extend((id-1,id+1))
    if id == 1 or id ==2 or id == 3:
        set_of_banned_shifts.append(23)
    if id == 21 or id == 20 or id == 19:
        set_of_banned_shifts.append(22)
    return set_of_banned_shifts

# creates a set of numbers from 1 to 21
def SetUntil21() -> set:
    list_of_numbers = set()
    for i in range(23):
        list_of_numbers.add(i+1)
    return list_of_numbers

# creates a set of numbers from 1 to 21 and removes the numbers that are in the passed argument set
def OppositeToSetUntil21(set_start) -> set:
    set_of_numbers = set()
    for i in range(1,24):
        if i in set_start: #in the passed argument set
            continue
        else:
            set_of_numbers.add(i)
    return set_of_numbers

# generates a set of restrictions that the worker can not do - fake restrictions, removes x shifts from the set of all the shifts
def GenerateFakeRestrictionsMinuxX(x) -> set:
    set_of_restrictions = SetUntil21()
    for i in range(x):
        list_of_restrictions = list(set_of_restrictions)
        random_number = random.choice(list_of_restrictions)
        set_of_restrictions.remove(random_number)
    return set_of_restrictions

# creates a list of workers
def CreateWorkerList(list_of_names) -> list:
    worker_list = []
    for i in range(len(list_of_names)):
        set_of_open_shifts = GenerateFakeRestrictionsMinuxX(9)
        set_of_closed_shifts = OppositeToSetUntil21(set_of_open_shifts)
        worker = Worker(name=list_of_names[i],worker_id=i+100,num_shifts_left_to_assign=5,open_shifts_no_changes=set_of_open_shifts,closed_shifts_no_changes=set_of_closed_shifts,night_shifts_requested=2)
        worker_list.append(worker)
    return worker_list

# creates a list of shifts
def CreateShiftList() -> list:
    shift_list = []
    for i in range(1,22):
        if i % 3 == 0:
            night_shift_bool = True
        else:
            night_shift_bool= False
        shift = Shift(night_shift_bool,shift_id = i,amount_of_workers_to_allocate_no_changes=2)
        shift_list.append(shift)
    for i in range(22,24):
        night_shift_bool = False
        shift = Shift(night_shift_bool,shift_id = i,amount_of_workers_to_allocate_no_changes=1)
        shift_list.append(shift)
    return shift_list

# assigns the worker to the shift
def AssignWorkerToShift(worker,shift,hard_coded=None,protected=None):
    if hard_coded==True:
        shift.hardcoded_worker = worker
    if protected==True:
        shift.protected_shifts.append(worker)
        
    shift.list_of_workers.append(worker)
    shift.number_of_assigned_workers += 1
    shift.workers_left_to_assign -= 1
    shift.list_of_workers_by_name.append(worker.name)
    shift.list_of_workers_by_id.append(worker.worker_id)

    worker.shifts_assigned.append(shift)
    worker.shifts_assigned_by_id.append(shift.shift_id)
    worker.num_shifts_left_to_assign -= 1

    banned_set_from_that_shift= ReturnSetOfBannedShiftsPerShift(shift)
    worker.banned_shifts_added.update(banned_set_from_that_shift) 
    worker.all_restrictions.update(banned_set_from_that_shift)
    if shift.is_night_shift:
        worker.night_shifts_allocated += 1
    if IsShiftAWeekendShift(shift):
        worker.amount_of_weekend_shifts += 1
    

# def RemoveWorkerFromShiftNewVersion(worker,shift):
#     if worker not in shift.list_of_workers:
#         print("Worker is not in the shift!!!!! ERROR")
#         return
#     if worker is shift.hardcoded_worker:
#         print("Worker is hardcoded to the shift, can't remove him!")
#         return
#     shift.list_of_workers.remove(worker)
#     shift.list_of_workers_by_id.remove(worker.worker_id)
#     shift.list_of_workers_by_name.remove(worker.name)
#     shift.number_of_assigned_workers -= 1
#     shift.workers_left_to_assign += 1


#     #worker removes
#     worker.shifts_assigned.remove(shift)
#     worker.shifts_assigned_by_id.remove(shift.shift_id)
#     worker.num_shifts_left_to_assign += 1
#     banned_set_from_that_shift= ReturnSetOfBannedShiftsPerShift(shift)
#     for x in list(banned_set_from_that_shift):
#         try:
#             if x in worker.closed_shifts_no_changes:
#                 worker.added_banned_shifts.remove(x)
#             else:
#                 worker.banned_shifts_added.remove(x)
#                 worker.all_restrictions.remove(x)
#         except:
#             # print("ERROR - remove worker from shift")
#             pass

#     if shift.is_night_shift:
#         worker.night_shifts_allocated -= 1
#     if IsShiftAWeekendShift(shift):
#         worker.amount_of_weekend_shifts -= 1



def AllocateWorkersWhenAmountOfAvailablePeopleEqualsAmountOfNeededPeople(list_of_shifts,list_of_workers):
        for shift in list_of_shifts:
            number_of_people_left_to_assign = shift.amount_of_workers_to_allocate_no_changes - shift.number_of_assigned_workers
            list_of_ppl = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
            if shift.amount_of_workers_to_allocate_no_changes == shift.number_of_assigned_workers:
                continue
            if len(list_of_ppl) == shift.amount_of_workers_to_allocate_no_changes:
                for people in list_of_ppl:
                    if people not in shift.list_of_workers and CanWorkerDoShift(people,shift):
                        AssignWorkerToShift(people,shift)
        return list_of_shifts,list_of_workers

# removes the worker from the shift
def RemoveWorkerFromShift(worker,shift):
    if worker in shift.list_of_workers:
        shift.list_of_workers.remove(worker)
        shift.number_of_assigned_workers -= 1
        shift.workers_left_to_assign += 1
        shift.list_of_workers_by_name.remove(worker.name)
        shift.list_of_workers_by_id.remove(worker.worker_id)

        worker.shifts_assigned.remove(shift)
        worker.shifts_assigned_by_id.remove(shift.shift_id)
        worker.num_shifts_left_to_assign += 1
        banned_set_from_that_shift= ReturnSetOfBannedShiftsPerShift(shift)
        for shift_id_in_banned in banned_set_from_that_shift:
            if shift_id_in_banned in worker.closed_shifts_no_changes:
                continue
            try:  
                worker.banned_shifts_added.remove(shift_id_in_banned)
                worker.all_restrictions.remove(shift_id_in_banned)
            except:
            #   print("ERROR - remove worker from shift")
              pass
        for x in worker.shifts_assigned:
            restrictions_for_existing_shifts = ReturnSetOfBannedShiftsPerShift(x)
            worker.banned_shifts_added.update(restrictions_for_existing_shifts)
            worker.all_restrictions.update(restrictions_for_existing_shifts)
        # worker.banned_shifts_added.difference_update(banned_set_from_that_shift)
        # worker.all_restrictions.difference_update(banned_set_from_that_shift)
        # worker.all_restrictions.update(worker.closed_shifts_no_changes)
        # worker.banned_shifts_added.update(worker.closed_shifts_no_changes)
        if shift.is_night_shift:
            worker.night_shifts_allocated -= 1
        if IsShiftAWeekendShift(shift):
            worker.amount_of_weekend_shifts -= 1
    else:
        print("Worker is not in the shift!!!!! ERROR")

# returns true if the worker can do the shift and false if not
def CanWorkerDoShift(worker,shift):
    if shift.is_night_shift and worker.night_shifts_allocated >= worker.night_shifts_requested_no_changes:
        return False
    if shift.shift_id in worker.shifts_assigned_by_id:
        return False
    if shift.shift_id in worker.all_restrictions:
        return False
    if shift.shift_id == 1 and worker.did_night_shift_saturday:
        return False
    if worker.num_shifts_left_to_assign <= 0:
        return False
    return True


def NumberOfWorkersAssignedToAllShifts(list_of_shifts) -> int:
    sum = 0
    for shift in list_of_shifts:
        sum += shift.number_of_assigned_workers
    return sum

def CanWorkerDoShiftSecondFunctionMinimalEffort(worker,shift):
    if shift.shift_id in worker.shifts_assigned_by_id:
        return False
    if shift.shift_id in worker.all_restrictions:
        return False

#all the people who can do the specific shift
def ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift):
    list_of_people = []
    for worker in list_of_workers:
        if CanWorkerDoShift(worker,shift):
            list_of_people.append(worker)
    return list_of_people

# returns the shift with the least amount of workers and the least amount of demand
def PickShiftWithLeastWorkersAndLeastAmountOfDemand(list_of_shifts,list_of_workers) -> Shift: # returns the shift with the least amount of workers and the least amount of demand
    list_of_shifts_to_pick_from = []
    min_workers = 0
    # find the shifts with the least amount of workers
    for shift in list_of_shifts:
        if shift.workers_left_to_assign == 0:
            continue
        if (shift.workers_left_to_assign > min_workers):
            min_workers = shift.workers_left_to_assign
    for shift in list_of_shifts:
        if shift.workers_left_to_assign == min_workers:
            list_of_shifts_to_pick_from.append(shift)
    if len(list_of_shifts_to_pick_from) == 1:
        return list_of_shifts_to_pick_from[0]
    if len(list_of_shifts_to_pick_from) == 0:
        return None
    shifts_dict = {}
    for shift in list_of_shifts_to_pick_from:
        workers_can_do_shift = 0
        shift_id = shift.shift_id
        for worker in list_of_workers:
            if CanWorkerDoShift(worker,shift):         
                workers_can_do_shift += 1
        shifts_dict[shift_id] = workers_can_do_shift
    min = 10000
    # print(shifts_dict)
    for item in shifts_dict.values():
        if item < min:
            min = item
    # print("MIN: ", min)
    final_list_of_shift_ids = []
    for key in shifts_dict:
        if shifts_dict[key] == min:
            final_list_of_shift_ids.append(key)
    list_finalized_shifts = []
    for shift_id in final_list_of_shift_ids:
        shift = get_shift_by_id(list_of_shifts,shift_id)
        if shift.amount_of_workers_to_allocate_no_changes != shift.number_of_assigned_workers:
            list_finalized_shifts.append(shift)
    
    # for shift in list_finalized_shifts:
    #     Shift.PrintShift(shift)
    random_shift = random.choice(list_finalized_shifts)
    # print("RANDOM SHIFT: ", random_shift.shift_id)
    return random_shift

# returns the nightshift with the least amount of workers and the least amount of demand
def PickShiftWithLeastWorkersAndLeastAmountOfDemandNightShifts(list_of_shifts,list_of_workers) -> Shift: # returns the shift with the least amount of workers and the least amount of demand
    list_of_night_shifts = []
    for shift in list_of_shifts:
        if shift.is_night_shift and shift.amount_of_workers_to_allocate_no_changes != shift.number_of_assigned_workers:
            list_of_night_shifts.append(shift)
    if len(list_of_night_shifts) == 0:
        return None
    if len(list_of_night_shifts) == 1:
        return list_of_night_shifts[0]
    shift = PickShiftWithLeastWorkersAndLeastAmountOfDemand(list_of_night_shifts,list_of_workers)
    return shift

#create a function that goes over all the list of shifts and returns true if all the number of assigned people per shift is 1 and 0 if not
def IsAllShiftsAssignedByOnePersonAtleast(list_of_shifts) -> bool:
    for shift in list_of_shifts:
        if shift.number_of_assigned_workers != 1:
            return False
    return True
# create a function that goes over all the list of workers and returns the amount of remaining shifts to assign
def AmountOfRemainingShiftsToAssign(list_of_workers) -> int:
    amount = 0
    for worker in list_of_workers:
        amount += worker.num_shifts_left_to_assign
    return amount

#create a function that goes over all the list of night shifts and returns true if all the number of assigned people per shift is 1 and 0 if not
def IsAllNightShiftsAssignedByOnePerson(list_of_shifts) -> bool:
    for shift in list_of_shifts:
        if shift.is_night_shift and shift.number_of_assigned_workers < 1:
            return False
    return True

def AreAllNightShiftsAssigned(list_of_shifts):
    for shift in list_of_shifts:
        if shift.is_night_shift and shift.number_of_assigned_workers != shift.amount_of_workers_to_allocate_no_changes:
            return False
    return True

def ReturnAllWorkersWithLeastAmountOfAllocatedShifts(list_of_workers) -> list:
    list_of_workers_with_least_amount_of_shifts = []
    min_shifts = 11111
    for worker in list_of_workers:
        length = int(len(worker.shifts_assigned_by_id))
        if length < min_shifts:
            min_shifts = length
    for worker in list_of_workers:
        length = len(worker.shifts_assigned_by_id)
        if length == min_shifts:
            list_of_workers_with_least_amount_of_shifts.append(worker)
    return list_of_workers_with_least_amount_of_shifts

def PickNightShiftThatIsNotFull(list_of_shifts) -> Shift:
    list_of_night_shifts = []
    for shift in list_of_shifts:
        if shift.is_night_shift and shift.amount_of_workers_to_allocate_no_changes != shift.number_of_assigned_workers:
            list_of_night_shifts.append(shift)
    random_night_shift = random.choice(list_of_night_shifts)
    return random_night_shift

def PickNightShiftWithLeastWorkers(list_of_shifts,list_of_workers) -> Shift:
    list_of_night_shifts = []
    for shift in list_of_shifts:
        if shift.is_night_shift and shift.amount_of_workers_to_allocate_no_changes != shift.number_of_assigned_workers:
            list_of_night_shifts.append(shift)
    if len(list_of_night_shifts) == 0:
        return None
    if len(list_of_night_shifts) == 1:
        return list_of_night_shifts[0]
    shift = PickShiftWithLeastWorkers(list_of_night_shifts,list_of_workers)
    return shift

def ReturnAllShiftsWithZeroWorkers(list_of_shifts) -> list:
    list_of_shifts_with_zero_workers = []
    for shift in list_of_shifts:
        if shift.number_of_assigned_workers == 0:
            list_of_shifts_with_zero_workers.append(shift)
    return list_of_shifts_with_zero_workers

def PickShiftWithLeastWorkers(list_of_shifts,list_of_workers):
    list_of_shifts_to_pick_from = []
    min_workers = 0
    # find the shifts with the least amount of workers
    list_of_shifts_without_nights = []
    for shift in list_of_shifts:
        if shift.is_night_shift:
            continue
        list_of_shifts_without_nights.append(shift)

    for shift in list_of_shifts_without_nights:
        if shift.workers_left_to_assign == 0:
            continue
        if (shift.workers_left_to_assign > min_workers):
            min_workers = shift.workers_left_to_assign
    for shift in list_of_shifts_without_nights:
        if shift.workers_left_to_assign == min_workers:
            list_of_shifts_to_pick_from.append(shift)

    if len(list_of_shifts_to_pick_from) == 1:
        return list_of_shifts_to_pick_from[0]
    if len(list_of_shifts_to_pick_from) == 0:
        return None
    # for shift in list_finalized_shifts:
    #     Shift.PrintShift(shift)
    random_shift = random.choice(list_of_shifts_to_pick_from)
    # print("RANDOM SHIFT: ", random_shift.shift_id)
    return random_shift

def CheckIfThereAreShiftsThatCannotEverBeCompleted(list_of_shifts,list_of_workers):
    number_of_closed_days = {}
    for worker in list_of_workers:
        closed_days = 0
        current_shift = 1
        for x in range(1,8):
            current_shift_1 = current_shift+1
            current_shift_2 = current_shift+2
            if current_shift in worker.closed_shifts_no_changes and current_shift_1 in worker.closed_shifts_no_changes and current_shift_2 in worker.closed_shifts_no_changes:
                closed_days += 1
            current_shift += 3
        number_of_closed_days[worker.name] = closed_days
    return number_of_closed_days

def GoOverTheDictionaryOfProblematicWorkers(list_of_shifts,list_of_workers,dict_of_closed_days: dict):
    #iterate over dict_of_clsoed_days keys and items
    dict_of_everything = {}
    for key,value in dict_of_closed_days.items():
        worker = GetWorkerByName(list_of_workers,key)
        worker_amount_of_shifs = worker.num_shifts_left_to_assign
        if worker_amount_of_shifs + value == 7:
            current_shift = 1
            for x in range(1,8):
                current_shift_1 = current_shift+1
                current_shift_2 = current_shift+2  
                list_of_small_shifts = []
                list_of_all_shifts = [current_shift,current_shift_1,current_shift_2]    
                if current_shift in worker.closed_shifts_no_changes:
                    list_of_small_shifts.append(current_shift)
                if current_shift_1 in worker.closed_shifts_no_changes:
                    list_of_small_shifts.append(current_shift_1)
                if current_shift_2 in worker.closed_shifts_no_changes:
                    list_of_small_shifts.append(current_shift_2)
                if len(list_of_small_shifts) == 2:
                    #check what shift is in list of all shifts but not in list of small shifts
                    for shift in list_of_all_shifts:
                        if shift not in list_of_small_shifts:
                            shift_to_remove = shift
                    if shift_to_remove not in dict_of_everything:
                        dict_of_everything[shift_to_remove] = [key]
                    else:
                        dict_of_everything[shift_to_remove].append(key)
                current_shift += 3
    return dict_of_everything            

def FillAllHaveToShifts(list_of_shifts,list_of_workers,dict_of_everything):
    for key,value in dict_of_everything.items():
        shift = GetShiftByID(list_of_shifts,key)
        for worker_name in value:
            worker = GetWorkerByName(list_of_workers,worker_name)
            if worker not in shift.list_of_workers:
                AssignWorkerToShift(worker,shift,protected=True)
        

def Checks(list_of_shifts,list_of_workers,dict_of_everything):
    error = ''
    for key,value in dict_of_everything.items():
        shift = GetShiftByID(list_of_shifts,key)
        list_of_people = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
        if shift.amount_of_workers_to_allocate_no_changes < len(value):
            error += f'ERROR - shift {Shift.PrintShiftIDByDayAndTime(shift)} needs {shift.amount_of_workers_to_allocate_no_changes} workers, but {value} HAVE to do that shift\n'
            
        #count the amount of people we need in general
    count_shifts_to_allocate = 0
    for shift in list_of_shifts:
        count_shifts_to_allocate += shift.amount_of_workers_to_allocate_no_changes
    count_worker_shifts = 0
    for worker in list_of_workers:
        count_worker_shifts += worker.num_shifts_left_to_assign
    if count_shifts_to_allocate != count_worker_shifts:
       error += f'ERROR - amount of shifts to allocate is not equal to the amount of shifts left to assign,shifts we need: {count_shifts_to_allocate}, shifts all workers can do: {count_worker_shifts}\n'
    for shift in list_of_shifts:
        #count how many people can do that shift
        list_of_people = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
        #check if its smaller than the amount of people we need
        if len(list_of_people) < shift.amount_of_workers_to_allocate_no_changes:
           error += f'ERROR - shift {Shift.PrintShiftIDByDayAndTime(shift)} needs {shift.amount_of_workers_to_allocate_no_changes} workers, but only {len(list_of_people)} can do that shift\n'
    return error
    
    
    
def CreateSchedule_UntilEveryShiftIsCoveredByOneWorker(list_of_shifts,list_of_workers):
    # print("ENTERED FIRST FUNCTION!")
    true_if_finished_correctly = None
    i=0
    assigned_shifts = 0
    error = 0
    while(not IsAllShiftsAssignedByOnePersonAtleast(list_of_shifts)):
            random_int_for_shift = random.randint(0,2)
            list_of_shifts_with_zero_workers = ReturnAllShiftsWithZeroWorkers(list_of_shifts)
            if len(list_of_shifts_with_zero_workers) == 0:
                #print("WE ALLOCATED ALL SHIFTS TO FIRST FUNCTION")
                return True
            if random_int_for_shift == 0 or random_int_for_shift == 1:
                shift = PickShiftWithLeastWorkersAndLeastAmountOfDemand(list_of_shifts_with_zero_workers,list_of_workers)
            else:
                shift = PickShiftWithLeastWorkersAndLeastAmountOfDemandNightShifts(list_of_shifts_with_zero_workers,list_of_workers)
            if shift is None:
                shift = random.choice(ReturnAllShiftsWithZeroWorkers(list_of_shifts_with_zero_workers))
             # add function for list of shift with 0 workers
            list_of_people = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
            if len(list_of_people) == 0:
                # print(f'WERE STUCK IN THE FIRST FUNCTION in shift  {shift.shift_id}')
                # WriteShiftsToCSVFile(list_of_shifts,filename=f'shifts_when_error_first_function_stuck_{shift.shift_id}.csv')
                error += 1
            # print("LEN OF LIST OF PEOPLE: ", len(list_of_people))
            list_of_workers_with_min_shifts = ReturnAllWorkersWithLeastAmountOfAllocatedShifts(list_of_people)
            if len(list_of_workers_with_min_shifts) == 0:
                i +=1
                error+=1
                if error > 5000:
                    true_if_finished_correctly = False
                    # print("reached 1000 errors in the second function!")
                    return true_if_finished_correctly
                continue
            worker = random.choice(list_of_workers_with_min_shifts)
            AssignWorkerToShift(worker,shift)
            # print("ASSIGNED WORKER: ", worker.name, "TO SHIFT: ", shift.shift_id)
            i += 1
            assigned_shifts += 1
    return True
            # print(i)
    # print("ASSIGNED SHIFTS: ", assigned_shifts)
    # print("number of iterations!!: ", i)

def Create_Schedule_TryToAllocateAllRemainingShifts(list_of_shifts,list_of_workers):
    # print("ENTERED SECOND FUNCTION!")
    i=0
    error =0
    assigned_shifts = 0
    # for shift in list_of_shifts:
    #     if (shift.number_of_assigned_workers
    while(AmountOfRemainingShiftsToAssign(list_of_workers) > 0):
            true_if_finished_correctly = None
            shift = None
            random_int_for_shift = random.randint(0,2)
            if random_int_for_shift == 0:
                if not AreAllNightShiftsAssigned(list_of_shifts):
                    shift = PickNightShiftThatIsNotFull(list_of_shifts)
                else:
                    shift = PickShiftWithLeastWorkers(list_of_shifts,list_of_workers)
            else:
                shift = PickShiftWithLeastWorkers(list_of_shifts,list_of_workers)
            if shift is None:
                error+=1
                if error > 1000:
                    true_if_finished_correctly = False
                    print("reached 1000 errors in the second function! - shift is none")
                    return true_if_finished_correctly
                continue
            if shift.number_of_assigned_workers == shift.amount_of_workers_to_allocate_no_changes:
                error+=1
                if error > 1000:
                    true_if_finished_correctly = False
                    # print("reached 1000 errors in the second function! - shift is full")
                    return true_if_finished_correctly
                continue
            list_of_people = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
            # print("PASSED")
            if len(list_of_people) == 0:
                error+=1
                i +=1
                if error > 1:
                    true_if_finished_correctly = False
                    # print("reached 1000 errors in the second function! - no people")
                    return true_if_finished_correctly
                continue
            worker = random.choice(list_of_people)
            # if worker.name == "Uri":
            #     print("DEBUG")
            AssignWorkerToShift(worker,shift)
            # print("amount of shifts left to assign:",AmountOfRemainingShiftsToAssign(list_of_workers))
            # print("ASSIGNED WORKER: ", worker.name, "TO SHIFT: ", shift.shift_id)
            i += 1
            assigned_shifts += 1
            error+=1
            # print(error)
            # print(i)
    print("I HAVE FINISHED HERE")
    WriteShiftsToCSVFile(list_of_shifts,filename="weird_thing.csv")
    print("shifts to assign:",AmountOfRemainingShiftsToAssign(list_of_workers))
    return True
    # print("ASSIGNED SHIFTS: ", assigned_shifts)
    # print("number of iterations!!: ", i)
    
def CreateSchedule_FillingAllProblematicShifts(list_of_shifts,list_of_workers):
    # itrate over the shifts and if a shift requires x amount of workers and there are only x amount of people who can do it, allocate all of them
    for shift in list_of_shifts:
        #check how many workers can do this shift
        list_of_people = ListOfPeopleWhoCanDoSpecificShift(list_of_workers,shift)
        if len(list_of_people) == (shift.amount_of_workers_to_allocate_no_changes-shift.number_of_assigned_workers):
            # print(shift.shift_id)
            for worker in list_of_people:
                if CanWorkerDoShift(worker,shift):
                    AssignWorkerToShift(worker,shift,protected=True)
                else:
                    print("WE HAD A PROBLEM IN THE FIRST FUNCTION")
                    exit()
    return True

def CreateSchedule_AllocateSSpecificShifts(list_of_shifts,list_of_workers,specific_workers_list):
    for element in specific_workers_list:
        worker,id = element.split("-")
        reverse_shift_mapping = {
            "Sunday Morning": "1",
            "Sunday Evening": "2",
            "Sunday Night": "3",
            "Monday Morning": "4",
            "Monday Evening": "5",
            "Monday Night": "6",
            "Tuesday Morning": "7",
            "Tuesday Evening": "8",
            "Tuesday Night": "9",
            "Wednesday Morning": "10",
            "Wednesday Evening": "11",
            "Wednesday Night": "12",
            "Thursday Morning": "13",
            "Thursday Evening": "14",
            "Thursday Night": "15",
            "Friday Morning": "16",
            "Friday Evening": "17",
            "Friday Night": "18",
            "Saturday Morning": "19",
            "Saturday Evening": "20",
            "Saturday Night": "21",
            "Saturday Middle": "22",
            "Sunday Middle": "23"
        }
        id = reverse_shift_mapping[id]
        id = int(id)
        shift_by_id = GetShiftByID(list_of_shifts,id)
        worker_by_name = GetWorkerByName(list_of_workers,worker)
        AssignWorkerToShift(worker_by_name,shift_by_id,hard_coded=True)

def CreateSchedule_Full(list_of_shifts,list_of_workers,specific_workers_list,prefrences_file,shift_config):
    print("WERE IN")
    total_removes = 0
    total_total_removes = 0
    random_save= 0
    total = 0
    x=0
    done = False
    flag_restart = None
    
    list_of_workers = ReadFromGoogleSheets(prefrences_file)
    PrintListOfWorkers(list_of_workers)
    print(shift_config)
    list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)

    dict_test = CheckIfThereAreShiftsThatCannotEverBeCompleted(list_of_shifts,list_of_workers)
    print("TEST")
    PrintListOfShifts(list_of_shifts)
    dict_of_everything = GoOverTheDictionaryOfProblematicWorkers(list_of_shifts,list_of_workers,dict_test)
    print(dict_of_everything)
    error = Checks(list_of_shifts,list_of_workers,dict_of_everything)
    print(error)
    print(specific_workers_list)
    if error != '':
        return error,list_of_shifts,list_of_workers, total_total_removes
    print(error)
    
    while(done == False):
        print("another iteration")
        flag = False
        # list_of_workers = ReadFromGoogleSheets(prefrences_file)
        # list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
        # #checks
        # flag = False
        # if len(specific_workers_list) > 0:
        #     CreateSchedule_AllocateSSpecificShifts(list_of_shifts,list_of_workers,specific_workers_list)
        # for x in range(10):
        #     CreateSchedule_FillingAllProblematicShifts(list_of_shifts,list_of_workers)
        # FillAllHaveToShifts(list_of_shifts,list_of_workers,dict_of_everything)
        
        while(flag == False):
            print("CreateSchedule_UntilEveryShiftIsCoveredByOneWorker")
            list_of_workers = ReadFromGoogleSheets(prefrences_file)
            list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
            if len(specific_workers_list) > 0:
                CreateSchedule_AllocateSSpecificShifts(list_of_shifts,list_of_workers,specific_workers_list)
            for x in range(2): #change back to 10, changed it to 2 for test purpose
                CreateSchedule_FillingAllProblematicShifts(list_of_shifts,list_of_workers)
            FillAllHaveToShifts(list_of_shifts,list_of_workers,dict_of_everything)
          #  print("WE IN??")
            flag = CreateSchedule_UntilEveryShiftIsCoveredByOneWorker(list_of_shifts,list_of_workers)
            if flag==True:
                WriteShiftsToCSVFile(list_of_shifts,filename="shiftsafterfirstfunctiontest.csv")
            else:
                continue
        flag = False
        while(flag == False):
            print("Create_Schedule_TryToAllocateAllRemainingShifts")
            flag = Create_Schedule_TryToAllocateAllRemainingShifts(list_of_shifts,list_of_workers)
            if flag == True:
                WriteShiftsToCSVFile(list_of_shifts,filename="tttttttttttttttttttttttttttt.csv")
            if flag == False:
                WriteShiftsToCSVFile(list_of_shifts,filename="shiftsaftersecondfunctiontest.csv")
                # print(shift_config)
                # print("NEED TO REMOVE WORKERS FROM SHIFTS")
                shifts_to_remove_from = []
                for shift in list_of_shifts:
                    if shift.number_of_assigned_workers > 1 and shift.hardcoded_worker == None and len(shift.protected_shifts) == 0:
                        shifts_to_remove_from.append(shift)
                if (len(shifts_to_remove_from) == 0):
                    print("LEN IS 0")
                # WriteShiftsToCSVFile(list_of_shifts,filename="shifts_before_second_function_test.csv")
                # print("shifts_to_remove_from",PrintListOfShifts(shifts_to_remove_from))
                random_amount_of_removes = random.randint(0,len(shifts_to_remove_from))
                random_save += random_amount_of_removes
                total_removes += random_amount_of_removes
                # print("REMOVING")
                while (random_amount_of_removes > 0):
                    # print("STUCK HERE")
                    random_shift = random.choice(shifts_to_remove_from)
                    random_worker = random.choice(random_shift.list_of_workers)
                    RemoveWorkerFromShift(random_worker,random_shift)
                    shifts_to_remove_from.remove(random_shift)
                    random_amount_of_removes -= 1
                if random_save > 1000:
                    random_save = 0
                    flag_restart = True
                    print("RESTARTING")
                    break
                else:
                    continue
            else:
                print("DONE")
                flag_restart = False
                done = True
                print("YES!")
                break   
        if flag_restart == True:
            continue
        else:
            break
    return total,list_of_shifts,list_of_workers, total_total_removes

# print("STARTING")
# list_of_workers = ReadFromGoogleSheets(prefrences_file)
# shift_config = csv_to_json_test("testfunc.csv")
# print(shift_config)
# list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
# #read csv from testfunc.csv
# total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers,specific_workers_list,prefrences_file,shift_config)
# print(total_removes)
# WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts_nitay.csv")
# exit()

# POST endpoint to receive a JSON file and store it in a global variable
@app.route('/api/upload_json', methods=['POST'])
def upload_json():
    global shift_config
    
    # Check if the file part is in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # Check if the user has not selected a file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read and parse the JSON content from the file
        json_content = json.load(file)
        
        # Store the parsed JSON content in the global variable
        shift_config = json_content
        
        return jsonify({'message': 'JSON file uploaded and stored successfully!', 'shift_config': shift_config}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/get_json', methods=['GET'])
@token_required
def get_json():
    global shift_config
    
    # Check if shift_config exists and is not empty
    if 'shift_config' not in globals() or shift_config is None:
        return jsonify({'error': 'No JSON file has been uploaded yet'}), 404
    
    # Return the stored JSON content
    return jsonify({'shift_config': shift_config}), 200



@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    # Check if the file part is in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    # Check if the user has not selected a file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read the CSV content without changing column names
        csv_data = pd.read_csv(io.StringIO(file.stream.read().decode('UTF-8')), header=None)

        # Define your own column names (adapt as necessary)
        csv_data.columns = ['Name', 'Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7', 'Count', 'Value']

        # Define the path to save the file (same directory as the script)
        save_path = os.path.join(os.getcwd(), 'prefrences.csv')
        
        # Save the CSV to a file without renaming columns
        csv_data.to_csv(save_path, index=False,header=False)

        return jsonify({'message': f'CSV saved successfully to {save_path}'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/get_csv', methods=['GET'])
@token_required
def get_csv():
    # Define the path to the CSV file
    csv_path = os.path.join(os.getcwd(), 'prefrences.csv')
    
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        return jsonify({'error': 'No CSV file has been uploaded yet'}), 404
    
    try:
        # Send the CSV file as a download
        return send_file(csv_path, mimetype='text/csv', as_attachment=True, download_name='prefrences.csv')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/create_shifts', methods=['GET'])
@token_required
def createShifts():
    try:
        # Define the path to the CSV file
        # print("TEST FIRST")
        file_path = os.path.join(os.getcwd(), 'full_shifts.csv')
        list_of_workers = ReadFromGoogleSheets(prefrences_file)
        # print("HERE?")
        list_of_shifts = CreateShiftsByConfigFile(shift_config,list_of_workers)
        # print("YES???")
        total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers)
        WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts.csv")
    
        #PrintWorkersAndTheirShifts(list_of_workers)
        
        stats = {}
        stats = AddWorkersAndTheirShiftsToStats(list_of_workers,stats)
        # Collect stats and store them in the dictionary
        stats["Amount of shifts to allocate at start"] = AmountOfShiftsToAllocateAtStart(list_of_shifts)
        stats["Amount of shifts allocated/amount of total shifts entered"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts) / AmountOfShiftsToAllocateAtStart(list_of_shifts)

        booli = CheckAllShiftsAssigned(list_of_shifts)
        if booli:
            stats["Shifts assignment status"] = "All shifts are assigned correctly!"
        else:
            stats["Shifts assignment status"] = "ERROR - NOT ALL SHIFTS ARE ASSIGNED CORRECTLY"

        stats["Amount of shifts remaining to assign"] = AmountOfRemainingShiftsToAssign(list_of_workers)
        stats["Amount of workers assigned to all shifts"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts)
        stats["TOTAL REMOVES"] = total_removes
        stats["TOTAL_total REMOVES"] = total_total_removes
        
        with open('stats.json', 'w') as json_file:
            json.dump(stats, json_file, indent=4)


        
        # Send the file as a response
        return send_file(file_path, as_attachment=True, mimetype='text/csv')



    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_stats', methods=['GET'])
@token_required
def get_stats():
    # Path to the stats.json file
    stats_file_path = 'stats.json'
    
    # Check if the file exists
    if os.path.exists(stats_file_path):
        try:
            # Send the file as a response
            return send_file(stats_file_path, mimetype='application/json', as_attachment=False)
        except Exception as e:
            return jsonify({'error': f"Failed to send the file: {str(e)}"}), 500
    else:
        return jsonify({'error': 'Stats file not found'}), 404

@app.route('/api/upload_csv_test', methods=['POST'])
def upload_csv_test():
    # Check if the file is part of the request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    
    # Check if the file has a valid name
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the file
    save_path = os.path.join(os.getcwd(), "TESTTTTTTTTTTTTTTTTTTTTTT.csv")
    file.save(save_path)

    return jsonify({"message": "File saved successfully", "file_path": save_path}), 200

@app.route('/api/create', methods=['POST'])
def create_all_shifts():
    global shift_config
    # Ensure both files are in the request
    if 'pref' not in request.files or 'config' not in request.files:
        return jsonify({"error": "Both 'pref' and 'config' files must be provided"}), 400

    pref_file = request.files['pref']
    config_file = request.files['config']
    
    # Ensure the files have names
    if pref_file.filename == '' or config_file.filename == '':
        return jsonify({"error": "One or both files are missing"}), 400

    try:
        # Save files in the current directory with specified names
        pref_save_path = os.path.join(os.getcwd(), 'pref.csv')
        config_save_path = os.path.join(os.getcwd(), 'config.csv')

        pref_file.save(pref_save_path)
        config_file.save(config_save_path)
        time.sleep(1)


    except Exception as e:
        return jsonify({"error": "ERRO!!"}), 500
    
    print("STARTING")

    list_of_workers = ReadFromGoogleSheets(pref_save_path)

    shift_config = csv_to_json_test(config_save_path)
    print(shift_config)

    list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
    #read csv from testfunc.csv
    total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers,specific_workers_list,prefrences_file,shift_config)
    print(total_removes)
    WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts_nitay.csv")
    
    output_file_path = os.path.join(os.getcwd(), "full_shifts_nitay.csv")
    
    stats = {}
    stats = AddWorkersAndTheirShiftsToStats(list_of_workers,stats)
    # Collect stats and store them in the dictionary
    stats["Amount of shifts to allocate at start"] = AmountOfShiftsToAllocateAtStart(list_of_shifts)
    stats["Amount of shifts allocated/amount of total shifts entered"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts) / AmountOfShiftsToAllocateAtStart(list_of_shifts)

    booli = CheckAllShiftsAssigned(list_of_shifts)
    if booli:
        stats["Shifts assignment status"] = "All shifts are assigned correctly!"
    else:
        stats["Shifts assignment status"] = "ERROR - NOT ALL SHIFTS ARE ASSIGNED CORRECTLY"

    stats["Amount of shifts remaining to assign"] = AmountOfRemainingShiftsToAssign(list_of_workers)
    stats["Amount of workers assigned to all shifts"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts)
    stats["TOTAL REMOVES"] = total_removes
    stats["TOTAL_total REMOVES"] = total_total_removes
    
    with open('stats.json', 'w') as json_file:
        json.dump(stats, json_file, indent=4)
    # Return the file as a response
    return send_file(
        output_file_path,
        as_attachment=True,
        download_name="full_shifts_nitay.csv",
        mimetype="application/json"
    )


@app.route('/api/create_all_shifts', methods=['POST'])
@token_required
def upload_files():
    global shift_config

    # Check if both files are present in the request
    if 'csv_file' not in request.files or 'json_file' not in request.files:
        return jsonify({'error': 'Both csv_file and json_file are required.'}), 400
    
    # Access the files from the request
    csv_file = request.files['csv_file']
    json_file = request.files['json_file']
    
    # Check if the files have valid filenames
    if csv_file.filename == '' or json_file.filename == '':
        return jsonify({'error': 'No file selected for one or both of the files.'}), 400
    # Process the CSV file
    csv_data = pd.read_csv(io.StringIO(csv_file.stream.read().decode('UTF-8')), header=None)
    
    # Define your own column names (adapt as necessary)
    csv_data.columns = ['Name', 'Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7', 'Count', 'Value']

    # Define the path to save the file (same directory as the script)
    save_path = os.path.join(os.getcwd(), 'prefrences.csv')
    
    # Save the CSV to a file without renaming columns
    csv_data.to_csv(save_path, index=False,header=False)

    # Process the JSON file
    json_content = json.load(json_file)
            
    # Store the parsed JSON content in the global variable
    shift_config = json_content
    
    file_path = os.path.join(os.getcwd(), 'full_shifts.csv')

    list_of_workers = ReadFromGoogleSheets(prefrences_file)
    list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
    print("TEST")
    # PrintListOfShifts(list_of_shifts)
    total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers,specific_workers_list)
    if type(total_removes) != int:
        print("HERE?")
        return jsonify(total_removes), 501
    print("TEST")
    WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts.csv")
    return send_file(file_path, as_attachment=True, mimetype='text/csv')

@app.route('/api/new_func_create', methods=['POST'])
def newfunctioncreate():
    global shift_config

    # Check if both files are present in the request
    if 'pref' not in request.files or 'config' not in request.files:
        return jsonify({'error': 'Both csv_file and json_file are required.'}), 400
    
    # Access the files from the request
    csv_file = request.files['pref']
    config_csv = request.files['config']
    
    
    # Check if the files have valid filenames
    if csv_file.filename == '' or config_csv.filename == '':
        return jsonify({'error': 'No file selected for one or both of the files.'}), 400
    
    try:
        # Process the CSV file
        csv_data = pd.read_csv(io.StringIO(csv_file.stream.read().decode('UTF-8')), header=None)
        
        # Define your own column names (adapt as necessary)
        csv_data.columns = ['Name', 'Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7', 'Count', 'Value']

        # Define the path to save the file (same directory as the script)
        save_path = os.path.join(os.getcwd(), 'prefrences.csv')
        
        # Save the CSV to a file without renaming columns
        csv_data.to_csv(save_path, index=False,header=False)
        
         # Process the CSV file
        csv_data_2 = pd.read_csv(io.StringIO(config_csv.stream.read().decode('UTF-8')), header=None)
        
        # Define the path to save the file (same directory as the script)
        save_path2 = os.path.join(os.getcwd(), 'config.csv')
        
        # Save the CSV to a file without renaming columns
        csv_data_2.to_csv(save_path2,header=False,index=False)
        
        json_file = csv_to_json_test('config.csv')
        # Process the JSON file
        json_content = json.loads(json_file)

        # Store the parsed JSON content in the global variable
        global shift_config
        shift_config = json_content

        # print(shift_config)
        file_path = os.path.join(os.getcwd(), 'full_shifts.csv')
        
        with open('pref_file_new.json', 'w') as pref_file:
            json.dump(json_content, pref_file, indent=4)
            
        list_of_workers = ReadFromGoogleSheets(save_path)
        # PrintListOfWorkers(list_of_workers)
        # print("YES?")
        list_of_shifts,specific_workers_list = CreateShiftsByConfigFile(shift_config,list_of_workers)
        
        # PrintListOfShifts(list_of_shifts)
        # print("ALMOST")
        total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers,specific_workers_list,save_path,shift_config)
        if type(total_removes) != int:
            print("HERE?")
            return jsonify(total_removes), 501
        print("TEST")
        WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts.csv")
        return send_file(file_path, as_attachment=True, mimetype='text/csv')


    
        # PrintWorkersAndTheirShifts(list_of_workers)
        stats = {}
        stats = AddWorkersAndTheirShiftsToStats(list_of_workers,stats)
        # Collect stats and store them in the dictionary
        stats["Amount of shifts to allocate at start"] = AmountOfShiftsToAllocateAtStart(list_of_shifts)
        stats["Amount of shifts allocated/amount of total shifts entered"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts) / AmountOfShiftsToAllocateAtStart(list_of_shifts)

        booli = CheckAllShiftsAssigned(list_of_shifts)
        if booli:
            stats["Shifts assignment status"] = "All shifts are assigned correctly!"
        else:
            stats["Shifts assignment status"] = "ERROR - NOT ALL SHIFTS ARE ASSIGNED CORRECTLY"

        stats["Amount of shifts remaining to assign"] = AmountOfRemainingShiftsToAssign(list_of_workers)
        stats["Amount of workers assigned to all shifts"] = NumberOfWorkersAssignedToAllShifts(list_of_shifts)
        stats["TOTAL REMOVES"] = total_removes
        stats["TOTAL_total REMOVES"] = total_total_removes
        
        with open('stats.json', 'w') as json_file:
            json.dump(stats, json_file, indent=4)



        
        # Send the file as a response
        
    
        # Now you can work with csv_data (DataFrame) and json_data (Python dict)
        return jsonify({
            'message': 'Files processed successfully!',
            'csv_columns': csv_data.columns.tolist(),
            'json_content': json_content
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
# Root route (GET request)
@app.route('/')
def home():

    
    # updated_json = replace_shift_keys(input_json)
    # print(json.dumps(updated_json, indent=4))
    return jsonify({'message': 'Welcome to my Flask API!'})
    # Return the CSV as a downloadable response
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=name.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)  # Enable debugging for easier development
