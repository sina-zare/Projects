try:
    import subprocess
    import os

    # Change User Env
    subprocess.run(['setx', 'test', 'zinzin'], check=True)

    # Change System Env
    subprocess.run(['setx', '/M', 'boyz', 'wowz'], check=True)


    # Verify the change (this may require restarting the command prompt or reopening Python)

    # Verify the value has been saved
    #print(os.environ.get('boy'))

    #input()
except Exception as e:
    input(e)