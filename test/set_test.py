

live_vms_set = {'A', 'B', 'C'}
db_vms_set = {'D', 'A', 'B', 'F'}

deletion_list = []
addition_list = []

print(f"\nLeaving/Coming Servers:  --> Symmetric Difference <--  {live_vms_set.symmetric_difference(db_vms_set)}\n\n")

if len(db_vms_set) != len(live_vms_set):

    # Finding Old Nodes that should be deleted
    temp_db_vms_set = db_vms_set.copy()
    for db_item in temp_db_vms_set:
        if db_item not in live_vms_set:
            # Appending Deletion list
            deletion_list.append(db_item)
            # Discarding item from DB
            db_vms_set.discard(db_item)

    # Finding New Nodes that should be added
    temp_live_vms_set = live_vms_set.copy()
    for live_item in live_vms_set:
        if live_item not in db_vms_set:
            # Appending Addition list
            addition_list.append(live_item)
            # Adding item to DB
            db_vms_set.add(live_item)

print(f"Addition List: {addition_list}")
print(f"Deletion List: {deletion_list}\n\nDB_VMs_Set: {db_vms_set}\n")
