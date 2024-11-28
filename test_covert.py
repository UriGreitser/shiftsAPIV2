import csv
import json

def csv_to_json(file_path):
    json_data = {}
    full_json = {}
    
    with open(file_path, mode="r", newline="") as csvfile:
        csvreader = list(csv.reader(csvfile))  # Read all rows into a list
        
        # Skip the first line
        rows = csvreader[1:]
        
        # Process the first 3 rows with 7 elements each
        for row_idx, row in enumerate(rows[:5], start=1):
            row_data = row[1:]  # Skip the first item in each row

            if row_idx <= 3:
                for i in range(1, 8):  # Process the first 3 lines with 7 elements after skipping the first one
                    cell_value = row_data[i-1]
                    if cell_value != "2":
                        json_data[f"{(row_idx - 1) * 7 + i}"] = cell_value  # Numbering from 1 to 21
            elif row_idx <= 5:  # Process the next 2 lines with 1 element each
                cell_value = row_data[0]  # After skipping the first item, take the only element
                line_number = 21 + (row_idx - 3)  # Line 22 for the 4th row, line 23 for the 5th row
                if cell_value != "2":
                    json_data[f"{line_number}"] = cell_value  # Add to JSON with number 22 or 23

        # Now process the "Hardcoded Shifts" line (6th line)
        hardcoded_shifts = []
        hardcoded_row = rows[5][1:]  # The 6th line, skipping the first element
        for cell in hardcoded_row:
            if not cell:  # Stop when an empty cell is encountered
                break
            hardcoded_shifts.append(str(cell))  # Add each cell value to the list as a string

        full_json["hard_coded_shifts"] = hardcoded_shifts  # Add the list of shifts to the JSON

    # Adding data to full_json
    full_json["amount_of_workers_to_allocate_specific_shifts"] = json_data
    full_json["amount_of_workers_to_allocate_no_changes"] = 2

    return json.dumps(full_json, indent=4)

# Example usage
file_path = "testfunc.csv"
json_output = csv_to_json(file_path)
print(json_output)
