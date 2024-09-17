from flask import Flask, request, jsonify, Response,send_file
import csv
import io
import json
from classes import Shift,Worker
import random
import csv
import pandas as pd
import os

app = Flask(__name__)
stored_name = None
global_config = None
global_prefrences = None
shift_config = None
prefrences_file = 'prefrences.csv'

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


#checks if all shifts are assigned to a worker that has not blocked them
def CheckAllShiftsAssigned(shifts):
    for shift in shifts:
        for worker in shift.list_of_workers:
            if shift.shift_id in worker.closed_shifts_no_changes:
                return False
    return True

def ReadFromGoogleSheets(prefrences_file):
    worker_list = []
    with open(prefrences_file, mode='r',encoding='utf-8') as file:
        reader = csv.reader(file)
        id = 100
        for row in reader:
            name = row[0]
            open_shifts = set()
            start = 1
            night_shifts_requested = int(row[8])
            days_off_taken = int(row[9])
            shifts_to_allocate = 5 - int(days_off_taken)
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


def CreateShiftsByConfigFile(shift_config): # this isnt working right for shifts 22 and 23 - if i try to set them to 0 it doesnt.
    list_of_shifts = []
    specific_shifts_dict = shift_config["amount_of_workers_to_allocate_specific_shifts"]
    print("SPECIFIC SHIFTS DICT: ", specific_shifts_dict)

    for i in range(1,24):
        if i in shift_config["hard_coded_shifts"]:
            amount_of_workers_to_allocate_no_changes = 1
        else:
            amount_of_workers_to_allocate_no_changes = shift_config["amount_of_workers_to_allocate_by_default"]

        if str(i) in specific_shifts_dict:
            amount_of_workers_to_allocate_no_changes = shift_config["amount_of_workers_to_allocate_specific_shifts"][str(i)]
        else:
            amount_of_workers_to_allocate_no_changes = shift_config["amount_of_workers_to_allocate_by_default"]
        if i % 3 == 0:
            night_shift_bool = True
        else:
            night_shift_bool= False
        if i == 22 or i == 23:
            night_shift_bool = False
        shift = Shift(night_shift_bool,shift_id = i,amount_of_workers_to_allocate_no_changes=amount_of_workers_to_allocate_no_changes)
        list_of_shifts.append(shift)
    return list_of_shifts



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
def AssignWorkerToShift(worker,shift):
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

def RemoveWorkerFromShiftNewVersion(worker,shift):
    if worker not in shift.list_of_workers:
        print("Worker is not in the shift!!!!! ERROR")
        return
    if worker is shift.hardcoded_worker:
        print("Worker is hardcoded to the shift, can't remove him!")
        return
    shift.list_of_workers.remove(worker)
    shift.list_of_workers_by_id.remove(worker.worker_id)
    shift.list_of_workers_by_name.remove(worker.name)
    shift.number_of_assigned_workers -= 1
    shift.workers_left_to_assign += 1


    #worker removes
    worker.shifts_assigned.remove(shift)
    worker.shifts_assigned_by_id.remove(shift.shift_id)
    worker.num_shifts_left_to_assign += 1
    banned_set_from_that_shift= ReturnSetOfBannedShiftsPerShift(shift)
    for x in list(banned_set_from_that_shift):
        try:
            if x in worker.closed_shifts_no_changes:
                worker.added_banned_shifts.remove(x)
            else:
                worker.banned_shifts_added.remove(x)
                worker.all_restrictions.remove(x)
        except:
            # print("ERROR - remove worker from shift")
            pass
        

    if shift.is_night_shift:
        worker.night_shifts_allocated -= 1
    if IsShiftAWeekendShift(shift):
        worker.amount_of_weekend_shifts -= 1





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
                print("WE ALLOCATED ALL SHIFTS TO FIRST FUNCTION")
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

def CreateSchedule_Full(list_of_shifts,list_of_workers):
    total_removes = 0
    total_total_removes = 0
    total = 0
    x=0
    done = False
    while(done == False):
        flag = False
        while(flag == False):
            flag = CreateSchedule_UntilEveryShiftIsCoveredByOneWorker(list_of_shifts,list_of_workers)
            if flag == False:
                # print("NEED TO REMOVE WORKERS FROM SHIFTS")
                random_amount_of_removes = random.randint(3,10)
                random_save = random_amount_of_removes
                while (random_amount_of_removes > 0):
                    random_shift = random.choice(list_of_shifts)
                    if random_shift.number_of_assigned_workers != 1:
                        continue
                    random_worker = random.choice(random_shift.list_of_workers)
                    # if random_worker.name == "Uri":
                    #     print("DEBUG")
                    RemoveWorkerFromShift(random_worker,random_shift)
                    random_amount_of_removes -= 1
            # WriteShiftsToCSVFile(list_of_shifts,filename="shifts_after_first_function_test_exit.csv")
            # WriteShiftsToFile(list_of_shifts,filename="shifts_after_first_function_test_exit.txt")            
        print("DONE WITH FIRST PART")
        # WriteShiftsToCSVFile(list_of_shifts,filename="shifts_after_first_function_test_exit.csv")
        flag = False
        while(flag == False):
            flag = Create_Schedule_TryToAllocateAllRemainingShifts(list_of_shifts,list_of_workers)
            # WriteShiftsToCSVFile(list_of_shifts,filename="shifts_after_second_function_test_exit.csv")
            # exit()
            # print("EXITED THE SECOND PART")
            if flag == False:
                # print("NEED TO REMOVE WORKERS FROM SHIFTS")
                random_amount_of_removes = random.randint(3,7)
                random_save = random_amount_of_removes
                error_removing = 0
                while (random_amount_of_removes > 0):
                    error_removing+=1
                    # print("STUCK HERE")
                    random_shift = random.choice(list_of_shifts)
                    if error_removing > 100000:
                        print("STARTING OVER WITH NEW ALLOCATION FOR bc of total_removes")
                        list_of_workers = ReadFromGoogleSheets(prefrences_file)
                        list_of_shifts = CreateShiftsByConfigFile(shift_config)
                        print("REACHED 100kerrors removing")
                        CreateSchedule_UntilEveryShiftIsCoveredByOneWorker(list_of_shifts,list_of_workers)
                        WriteShiftsToCSVFile(list_of_shifts,filename="WHA!!!!T.csv")
                        error_removing = 0
                        break
                    if random_shift.number_of_assigned_workers < 2:
                        continue
                    random_worker = random.choice(random_shift.list_of_workers)
                    # if random_worker.name == "Uri":
                    #     print("DEBUG")
                    RemoveWorkerFromShift(random_worker,random_shift)
                    random_amount_of_removes -= 1
                # print(f'AMOUNT OF WORKERS REMOVED: {random_save}')
                total_removes += random_save
                total += random_save
                # if total_removes > 10000:
                #     WriteShiftsToCSVFile(list_of_shifts,filename="shifts_after_10000remves.csv")
                #     exit()
                if total_removes > 10000:
                    print("STARTING OVER WITH NEW ALLOCATION FOR bc of total_removes")
                    list_of_workers = ReadFromGoogleSheets(prefrences_file)
                    list_of_shifts = CreateShiftsByConfigFile(shift_config)
                    print("REACHED 10000 REMOVES")
                    CreateSchedule_UntilEveryShiftIsCoveredByOneWorker(list_of_shifts,list_of_workers)
                    total += total_removes
                    total_removes = 0
                    total_total_removes += total
            else:
                done = True
                break
    return total,list_of_shifts,list_of_workers, total_total_removes

print("STARTING")



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
def createShifts():
    try:
        # Define the path to the CSV file
        print("TEST FIRST")
        file_path = os.path.join(os.getcwd(), 'full_shifts.csv')

        list_of_workers = ReadFromGoogleSheets(prefrences_file)

        list_of_shifts = CreateShiftsByConfigFile(shift_config)

        total_removes,list_of_shifts,list_of_workers,total_total_removes = CreateSchedule_Full(list_of_shifts,list_of_workers)
        WriteShiftsToCSVFile(list_of_shifts,filename="full_shifts.csv")
        
    
    
        PrintWorkersAndTheirShifts(list_of_workers)
        print("--------------------------------------------------")
        print("Amount of shifts to allocate at start:", AmountOfShiftsToAllocateAtStart(list_of_shifts))

        print("Amount of shifts allocated/amount of total shifts entered:", NumberOfWorkersAssignedToAllShifts(list_of_shifts)/AmountOfShiftsToAllocateAtStart(list_of_shifts))
        booli = CheckAllShiftsAssigned(list_of_shifts)
        if booli:
            print("All shifts are assigned correctly!")
        else: 
            print("ERROR - NOT ALL SHIFTS ARE ASSIGNED CORRECTLY")

        print("Amount of shifts remaining to assign=", AmountOfRemainingShiftsToAssign(list_of_workers))
        print("Amount of workers assigned to all shifts=", NumberOfWorkersAssignedToAllShifts(list_of_shifts))
        print("TOTAL REMOVES: ", total_removes)
        print("TOTAL_total REMOVES: ", total_total_removes)
        
        # Send the file as a response
        return send_file(file_path, as_attachment=True, mimetype='text/csv')



    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Root route (GET request)
@app.route('/')
def home():
    return jsonify({'message': 'Welcome to my Flask API!'})
    # Return the CSV as a downloadable response
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=name.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)  # Enable debugging for easier development