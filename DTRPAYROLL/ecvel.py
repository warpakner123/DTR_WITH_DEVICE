import xlrd
from datetime import datetime
import time

# get workbook
wb_obj = xlrd.open_workbook('try2.xls')

# get sheet
sheet = wb_obj.sheet_by_index(0)

first_id = ''

def convert(a):
    converted_string = str(a)
    converted_string = converted_string.replace('text:\'', '').replace('\'', '')
    return converted_string

# store ang employee
emp_storage = []
temp_storage = []

for rx in range (1, sheet.nrows):
    system_id = sheet.row(rx)[2]
    systemId = int(convert(system_id))
    if first_id == '':
        first_id = systemId
    
    if first_id != systemId:
        first_id = systemId
        emp_storage.append(temp_storage)
        temp_storage = []
    
    if first_id == systemId:
        temp_storage.append(sheet.row(rx))
    if rx == sheet.nrows - 1:
        emp_storage.append(temp_storage)
        temp_storage = []
        
print('Employee Storage')
print(emp_storage)

for first_array in emp_storage:
    temp_date = ''
    temp_time = ''

    for index, second_array in enumerate(first_array):
        time = convert(second_array[3])
        strip_time = datetime.strptime(time, '%d/%m/%Y %H:%M:%S')
        print(strip_time.date())
        if temp_date == '':
            temp_date = strip_time.date()
        
        # if same date check time.
        if index != 0 and temp_date == strip_time.date():
            # check previous - current time
            previous_time = convert(first_array[index - 1][3])
            previous_time = datetime.strptime(previous_time, '%d/%m/%Y %H:%M:%S')
            print('previous: {}'.format(previous_time))
            print(previous_time.timestamp())
            # current time
            current = strip_time
            print('current: {}'.format(current))
            print(current.timestamp())
            # interval time between current and previous time
            interval_nila = current.timestamp() - previous_time.timestamp()
            print('interval: {}'.format(interval_nila / 3600))
            # check if interval in less than 2 hours
            if not (interval_nila < 7200):
                print('counted')
            else:
                print('not counted')
            # print((previous_time + current).time())
            # chop-chop ang date para sa payroll
        
        if temp_date != strip_time.date():
            temp_date = strip_time.date()

            

    # converted_string = str(row)
    # converted_string = converted_string.replace('text:\'', '').replace('\'', '')
    # print(converted_string)
    


# check date

# check time

# check interval time

# change in-out/out-in