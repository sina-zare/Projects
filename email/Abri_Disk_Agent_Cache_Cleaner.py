# Empty the csv file
def empty_csv_file(file_path):
    with open(file_path, 'w', newline='') as csv_file:
        csv_file.truncate()


abri_disk_duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python/EmailsTicketNo/Abri-Disk-Duplicate-Check-DB.csv"
abri_ram_duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python/EmailsTicketNo/Abri-Resource-RAM-Duplicate-Check-DB.csv"
abri_cpu_duplicate_check_db_path = "C:/Users/sina.z/Desktop/Python/EmailsTicketNo/Abri-Resource-CPU-Duplicate-Check-DB.csv"


empty_csv_file(abri_disk_duplicate_check_db_path)
empty_csv_file(abri_ram_duplicate_check_db_path)
empty_csv_file(abri_cpu_duplicate_check_db_path)