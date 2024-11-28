class Shift:

    def __init__(self,is_night_shift,amount_of_workers_to_allocate_no_changes=None,shift_id=None,hardcoded_worker=None):
        self.list_of_workers_by_name = [] # list of workers by name
        self.list_of_workers_by_id = [] # list of workers by ID
        self.amount_of_workers_to_allocate_no_changes = amount_of_workers_to_allocate_no_changes
        self.is_night_shift = is_night_shift # True if night shift, False if not
        self.protected_shifts = [] # shifts that are protected - no changes can be made to them
        if hardcoded_worker is None:   #worker to add to the shift hardcoded by admin
            self.list_of_workers = []
            self.hardcoded_worker = None
        else:
            self.list_of_workers = [hardcoded_worker]
            self.hardcoded_worker = hardcoded_worker
        if shift_id is None:
            shift_id = -1
        else:
            self.shift_id = shift_id
        if hardcoded_worker is None:
            self.number_of_assigned_workers = 0 # Number of workers assigned to the shift
        else:  
            self.number_of_assigned_workers = 1
        x = self.amount_of_workers_to_allocate_no_changes #how many workers should be in this shift - no changes.
        self.workers_left_to_assign = x # how many workers are we missing in that shift
        

    def GetShiftDay(self):
        day = self.shift_id 
        if day == 22:
            day_of_week = "Saturday"
        elif day == 23:
            day_of_week = "Sunday"
            
        if day <= 3:
            day_of_week = "Sunday"
        elif day <= 6:
            day_of_week = "Monday"
        elif day <= 9:
            day_of_week = "Tuesday"
        elif day <= 12:
            day_of_week = "Wednesday"
        elif day <= 15:
            day_of_week = "Thursday"
        elif day <= 18:
            day_of_week = "Friday"
        else:
            day_of_week = "Saturday"
            
        return day_of_week
    
    def GetShiftTime(self):
        time = self.shift_id % 3
        if self.shift_id == 22 or self.shift_id == 23:
            return "Middle"
        # print(self.shift_id)
        if time == 1:
            part_of_day = "Morning"
        elif time == 2:
            part_of_day = "Evening"
        else:
            part_of_day = "Night"
        return part_of_day


    def PrintShiftIDByDayAndTime(self):
        day = self.GetShiftDay()
        time = self.GetShiftTime()
        if self.shift_id == 22:
            shift_name = "Saturday Middle"
        elif self.shift_id == 23:
            shift_name = "Sunday Middle"
        else:
            shift_name = day + " " + time
            # print("Shift: ", shift_name)
        return shift_name
    
    def ReturnShiftIDByDayAndTime(self):
        day = self.GetShiftDay()
        time = self.GetShiftTime()
        if self.shift_id == 22:
            shift_name = "Saturday Middle"
        elif self.shift_id == 23:
            shift_name = "Sunday Middle"
        else:
            shift_name = day + " " + time
        return shift_name

    
    def PrintShift(self):
        print("SHIFT DETAILS:")
        print("Number of assigned workers: ", self.number_of_assigned_workers)
        print("Amount of workers to allocate no changes: ", self.amount_of_workers_to_allocate_no_changes)
        print("Workers left to assign: ", self.workers_left_to_assign)
        print("List of workers: ", self.list_of_workers)
        print("Shift ID: ", self.shift_id)        
        print("Is night shift: ", self.is_night_shift)
        # print("Number of assigned workers: ", self.number_of_assigned_workers)
        print("List of workers by name: ", self.list_of_workers_by_name)
        print("List of workers by ID: ", self.list_of_workers_by_id)
        self.PrintShiftIDByDayAndTime()
        print("\n")




class Worker:
    def __init__(self, name, worker_id, num_shifts_left_to_assign,open_shifts_no_changes,closed_shifts_no_changes,night_shifts_requested, did_night_shift_saturday=None):
        self.name = name
        self.worker_id = worker_id
        self.shifts_assigned = [] # List of shift objects
        self.shifts_assigned_by_id = [] # List of shift IDs
        self.num_shifts_left_to_assign = num_shifts_left_to_assign # Number of shifts left to assign
        self.num_shifts_at_start = num_shifts_left_to_assign # Number of shifts at start - how many shifts each worker is gonna work this week
        self.open_shifts_no_changes = open_shifts_no_changes # the list of all the open shifts that the worker can do - no changes
        self.closed_shifts_no_changes = closed_shifts_no_changes # the list of all the closed shifts that the worker can not do - no changes
        self.banned_shifts_added = set() #shifts that the worker can not do because of other shifts he got allocated 
        self.all_restrictions = set()
        self.all_restrictions.update(closed_shifts_no_changes) # all the restrictions that the worker has - which is banned shifts + closed shifts intizialed with all the shifts the worker closed
        self.night_shifts_requested_no_changes = night_shifts_requested
        self.night_shifts_allocated = 0 
        self.amount_of_weekend_shifts = 0
        if did_night_shift_saturday is None:
            self.did_night_shift_saturday = False
        else:
            self.did_night_shift_saturday = True
            self.all_restrictions.append(1)
            self.closed_shifts_no_changes.append(1)
        

    def PrintWorker(self):
        print("WORKER DETAILS:")
        print("Name: ", self.name)
        print("Worker ID: ", self.worker_id)
        print("Number of shifts left to assign: ", self.num_shifts_left_to_assign)
        print("Number of shifts at start: ", self.num_shifts_at_start)
        print("Open shifts no changes: ", self.open_shifts_no_changes)
        print("Closed shifts no changes: ", self.closed_shifts_no_changes)
        print("Banned shifts added: ", self.banned_shifts_added)
        print("All restrictions: ", self.all_restrictions)
        print("Night shifts requested no changes: ", self.night_shifts_requested_no_changes)
        print("Night shifts allocated: ", self.night_shifts_allocated)
        print("Did night shift Saturday: ", self.did_night_shift_saturday)
        print("Shifts assigned: ", self.shifts_assigned)
        print("Shifts assigned by ID: ", self.shifts_assigned_by_id)
        print("amount of weekend shifts: ", self.amount_of_weekend_shifts)
        print("\n")


