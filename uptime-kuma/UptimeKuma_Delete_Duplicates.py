import time
from uptime_kuma_api import UptimeKumaApi

def find_duplicates(major_list):
    # Step 1: Create an empty set to keep track of elements we've seen
    seen = set()

    # Optional: Create a set to keep track of duplicates if we want to know what they are
    duplicates = set()

    # Step 2: Iterate over each sublist in the major list
    for sublist in major_list:
        # Step 3: Check if the sublist has at least one element to avoid IndexError
        if sublist:
            # Get the first item of the sublist
            node_name = sublist[0]
            node_id = sublist[1]
            #print(node_name + ': ' + str(node_id))

            # Step 4: Check if the first item is already in the 'seen' set
            if node_name in seen:
                # If it is, it's a duplicate, so add it to the duplicates set
                duplicates.add(f"{node_name}, {node_id}")
            else:
                # If it's not, add it to the 'seen' set
                seen.add(node_name)

    # Step 5: Check if we found any duplicates
    # Return True if the duplicates set has any elements, otherwise False
    return len(duplicates) > 0, duplicates


api = UptimeKumaApi('http://172.29.6.102:8080/')
api.login('admin', 'I4=t8K<xn')

# Fetch all monitors
monitors = api.get_monitors()

# Find the monitor by name and get its ID
monitor_list = []
for monitor in monitors:
    monitor_list.append([monitor['name'], monitor['id']])

has_duplicates, duplicates = find_duplicates(monitor_list)

#print(duplicates)

if has_duplicates:
    print('##### Duplicates found #####\n')
    for node in duplicates:
        api.delete_monitor(int(node.split(', ')[1]))
        print(f"{node.split(', ')[0]} --> {node.split(', ')[1]} --> Deleted")
        time.sleep(0.5)
else:
    print('##### No Duplicates #####\n\n\n')

api.disconnect()


