import win32com.client


def create_outlook_rule():
    # Access Outlook application
    outlook = win32com.client.Dispatch("Outlook.Application")

    # Get rules object
    rules = outlook.Session.DefaultStore.GetRules()

    # Create a new rule
    new_rule = rules.Create("Forward XYZ Emails", 0)  # 0 means client-side rule
    new_rule.IsLocalRule = False  # Set to False for server-side rule

    # Define conditions
    condition_subject = new_rule.Conditions.Subject
    condition_subject.Text = ["xyz"]  # Specify the subject

    # Define action to move email to a folder
    action_move_to_folder = new_rule.Actions.MoveToFolder
    # Navigate to the target folder
    target_folder_path = "SolarwindsMonitoringVIP/ME_Disk/Aco"
    target_folder = outlook.Session.Folders
    print(target_folder)
    for folder_name in target_folder_path.split('/'):
        target_folder = target_folder.Item(folder_name)
    action_move_to_folder.Folder = target_folder

    # Save the rule
    rules.Save()

    print("Rule created successfully.")