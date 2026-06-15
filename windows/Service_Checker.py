import time

import winrm
import os
from jdatetime import date, datetime

# Credentials
from cryptography.fernet import Fernet
def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    return decrypted_password.decode()

#username_abramad = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
username_cloud = decryptor("enc_sinaz_cloud","key_sinaz_cloud")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

hostname = input('VM Name: ') + '.cloud.local'

# Log Path
today_date_jalali = date.today().strftime("%Y-%m-%d")
current_time = (str(datetime.now())[11:19]).replace(":", "-")
log_path = f"Helper-Logs\\{today_date_jalali}"
log_name = f"{hostname.split('.')[0].replace('mer-','')}-Fault-{current_time}-Log.txt"
#os.system('cls' if os.name == 'nt' else 'clear')

# Ensure log directory exists, create if it doesn't
if not os.path.exists(log_path):
    os.makedirs(log_path)


def logger(log, log_path, log_name):
    with open(f"{log_path}\\{log_name}", "a") as text_file:
        text_file.write(f"{log}\n")

    print(f"{log}\n")

def service_checker(service, host, username, password):

    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command = f"Get-Service -Name '{service}'"
    result = session.run_ps(command)

    # Check the output for service status
    if result.status_code == 0:
        output = result.std_out.decode('utf-8')
        output_as_list = output.split()
        service_name = output_as_list[7]
        service_state = output_as_list[6]

        #print(f"The {service_name} service is {service_state} on {host}")
        final_result = f"{host.split('.')[0]}:{service_name}:{service_state}"
        logger(final_result, log_path, log_name)
        return final_result

    elif "Cannot find any service with service name" in result.std_err.decode('utf-8'):
        final_result = f"{host.split('.')[0]}:{service}:Not Found"
        logger((f"{host.split('.')[0]}:{service}:Not Found"), log_path, log_name)
        return final_result

    else:
        error = f"{20 * '#'}\nFailed to execute the command. Error: {result.std_err.decode('utf-8')}\n{20 * '#'}"
        logger(error, log_path, log_name)
        return error

def service_checker_regex(service, host, username, password):
    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command1 = f'''
    $serviceName = "{service}"'''
    command2 = '''
    $services = Get-Service -Name $serviceName

    if ($services) {
        foreach ($service in $services) {'''
    command3 = f'''
            "{host.split('.')[0]}:$($service.Name):$($service.Status)"'''
    command4 = '''    }
    } else {'''
    command5 = f'''   "{host.split('.')[0]}:{service}:Not Found"'''
    command6 = '''}'''

    command = command1 + command2 + command3 + command4 + command5 + command6
    result = session.run_ps(command)
    output = result.std_out.decode('utf-8').strip()

    logger(output, log_path, log_name)
    return output

def service_starter(service, host, username, password):

    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command = f"Start-Service -Name '{service}'"

    result = session.run_ps(command)

    # Check the output for service status
    if result.status_code == 0:
        output = result.std_out.decode('utf-8')

        if output == "":
            final_result = f"{host.split('.')[0]}:{service}:Started"
            logger(final_result, log_path, log_name)
            return final_result

    elif "Cannot find any service with service name" in result.std_err.decode('utf-8'):
        error = f"{host.split('.')[0]}:{service}:Not Found"
        logger(error, log_path, log_name)
        return error

    else:
        error = f"{20 * '#'}\nFailed to execute the command. Error: {result.std_err.decode('utf-8')}\n{20 * '#'}"
        logger(error, log_path, log_name)
        return error


    #return f"{host.split('.')[0]}:{service_name}:{service_state}"

def service_starter_regex(service, host, username, password):

    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command = f"Get-Service -Name '{service}' | Start-Service"

    result = session.run_ps(command)

    # Check the output for service status
    if result.status_code == 0:
        output = result.std_out.decode('utf-8')

        if output == "":
            final_result = f"{host.split('.')[0]}:{service}:Started"
            logger(final_result, log_path, log_name)
            return final_result

    elif "Cannot find any service with service name" in result.std_err.decode('utf-8'):
        error = f"{host.split('.')[0]}:{service}:Not Found"
        logger(error, log_path, log_name)
        return error

    else:
        error = f"{20 * '#'}\nFailed to execute the command. Error: {result.std_err.decode('utf-8')}\n{20 * '#'}"
        logger(error, log_path, log_name)
        return error


    #return f"{host.split('.')[0]}:{service_name}:{service_state}"

def iis_restarter(host, username, password):

    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command = f"iisreset /restart"

    result = session.run_ps(command)

    # Check the output for service status
    if result.status_code == 0:
        output = result.std_out.decode('utf-8')

        if output == "":
            final_result = f"{host.split('.')[0]}:IISServices:Restarted"
            logger(final_result, log_path, log_name)
            return final_result

    else:
        error = f"{20 * '#'}\nFailed to execute the command. Error: {result.std_err.decode('utf-8')}\n{20 * '#'}"
        logger(error, log_path, log_name)
        return error

def iis_checker(host, username, password):

    # Create a WinRM session
    session = winrm.Session(
        target=host,
        auth=(username, password),
        transport='ntlm',
        server_cert_validation='ignore'
    )

    # Execute the command remotely
    command = f"iisreset /status"

    result = session.run_ps(command)

    # Check the output for service status
    if result.status_code == 0:
        output = result.std_out
        output_better_view = []
        step1 = str((str(output).split('\\r\\n'))).replace('\\\\r','').split(',')

        for i in step1[1:-1]:
            output_better_view.append(i.strip().replace('Status for ','').replace("'","").split(' : '))

        svc_flag = 0
        for status in output_better_view:
            if 'IISADMIN' in status[0]:
                iisadmin_final_result = f"{host.split('.')[0]}:{status[0]}:{status[1]}"
                logger(iisadmin_final_result, log_path, log_name)
                svc_flag += 1

            if 'WAS' in status[0]:
                was_final_result = f"{host.split('.')[0]}:{status[0]}:{status[1]}"
                logger(was_final_result, log_path, log_name)
                svc_flag += 1

            if 'W3SVC' in status[0]:
                w3svc_final_result = f"{host.split('.')[0]}:{status[0]}:{status[1]}"
                logger(w3svc_final_result, log_path, log_name)
                svc_flag += 1


            if svc_flag == 3:
                return f"{iisadmin_final_result}|{was_final_result}|{w3svc_final_result}"


    else:
        error = f"{20 * '#'}\nFailed to execute the command. Error: {result.std_err.decode('utf-8')}\n{20 * '#'}"
        logger(error, log_path, log_name)
        return error


# Main Functionality
try:

    ### Checking SQL Services ###
    #logger(f"{70 * '#'}\n", log_path, log_name)
    #logger(f"### Checking SQL Services ###", log_path, log_name)

    # Querying status of service
    ms_sqlserver = service_checker("MSSQLSERVER", hostname, username_cloud, password)
    if ms_sqlserver.split(':')[2].lower() != "running":
        if ms_sqlserver.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter("MSSQLSERVER", hostname, username_cloud, password)
            time.sleep(1.5)
            # Check if service has started
            logger("Verify if service has started", log_path, log_name)
            ms_sqlserver_verify = service_checker("MSSQLSERVER", hostname, username_cloud, password)
            if ms_sqlserver_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'MSSQLSERVER' manually --> {ms_sqlserver_verify.split(':')[2]}", log_path, log_name)


    # Querying status of service
    sql_server_agent = service_checker("SQLSERVERAGENT", hostname, username_cloud, password)
    if sql_server_agent.split(':')[2].lower() != "running":
        if sql_server_agent.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter("SQLSERVERAGENT", hostname, username_cloud, password)
            time.sleep(1.5)
            # Check if service has started
            logger("Verify if service has started", log_path, log_name)
            sql_server_agent_verify = service_checker("SQLSERVERAGENT", hostname, username_cloud, password)
            if sql_server_agent_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SQLSERVERAGENT' manually --> {sql_server_agent_verify.split(':')[2]}", log_path, log_name)


    # Querying status of service
    sql_telemetry = service_checker("SQLTELEMETRY", hostname, username_cloud, password)
    if sql_telemetry.split(':')[2].lower() != "running":
        if sql_telemetry.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter("SQLTELEMETRY", hostname, username_cloud, password)
            time.sleep(1.5)
            # Check if service has started
            logger("Verify if service has started", log_path, log_name)
            sql_telemetry_verify = service_checker("SQLTELEMETRY", hostname, username_cloud, password)
            if sql_telemetry_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SQLTELEMETRY' manually --> {sql_telemetry_verify.split(':')[2]}", log_path, log_name)


    # Querying status of service
    reporting_service = service_checker("SQLServerReportingServices", hostname, username_cloud, password)
    if reporting_service.split(':')[2].lower() != "running":
        if reporting_service.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter("SQLServerReportingServices", hostname, username_cloud, password)
            time.sleep(1.5)
            # Verify if service has started
            logger("Verify if service has started", log_path, log_name)
            reporting_service_verify = service_checker("SQLServerReportingServices", hostname, username_cloud, password)
            if reporting_service_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SQLServerReportingServices' manually --> {reporting_service_verify.split(':')[2]}", log_path, log_name)




    ### SG-Replication* Service ###
    logger(f"\n\n### Checking SG-Replication Service ###", log_path, log_name)

    # Querying status of service
    sg_replication = service_checker_regex("SGReplication*", hostname, username_cloud, password)
    if sg_replication.split(':')[2].lower() != "running":
        if sg_replication.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter_regex("SGReplication*", hostname, username_cloud, password)
            time.sleep(1.5)
            # Verify if service has started
            logger("Verify if service has started", log_path, log_name)
            sg_replication_verify = service_checker_regex("SGReplication*", hostname, username_cloud, password)
            if sg_replication_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SGReplication' manually --> {sg_replication_verify.split(':')[2]}",log_path, log_name)




    ### SGRahkaranRedis* Service ###
    logger(f"\n\n### Checking SG-Rahkaran-Redis Service ###", log_path, log_name)

    # Querying status of service
    sg_rahkaran_redis = service_checker_regex("SGRahkaranRedis*", hostname, username_cloud, password)
    if sg_rahkaran_redis.split(':')[2].lower() != "running":
        if sg_rahkaran_redis.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter_regex("SGRahkaranRedis*", hostname, username_cloud, password)
            time.sleep(1.5)
            # Verify if service has started
            logger("Verify if service has started", log_path, log_name)
            sg_rahkaran_redis_verify = service_checker_regex("SGRahkaranRedis*", hostname, username_cloud, password)
            if sg_rahkaran_redis_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SGRahkaranRedis' manually --> {sg_rahkaran_redis_verify.split(':')[2]}", log_path, log_name)





    ### SG-Tax-Payer Service ###
    logger(f"\n\n### Checking SG-Tax-Payer Service ###", log_path, log_name)

    # Querying status of service SgTaxPayerMiddleware
    sg_tax_payer = service_checker_regex("SGTaxPayer*", hostname, username_cloud, password)
    if sg_tax_payer.split(':')[2].lower() != "running":
        if sg_tax_payer.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter("SGTaxPayer", hostname, username_cloud, password)
            time.sleep(1.5)
            # Verify if service has started
            logger("Verify if service has started", log_path, log_name)
            sg_tax_payer_verify = service_checker_regex("SGTaxPayer*", hostname, username_cloud, password)
            if sg_tax_payer_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SGTaxPayer' manually --> {sg_tax_payer_verify.split(':')[2]}", log_path, log_name)




    ### SG-Process-Engine Service ###
    logger(f"\n\n### Checking SG-Process-Engine Service ###", log_path, log_name)

    # Querying status of service
    sg_process_engine = service_checker_regex("SgProcessEngine*", hostname, username_cloud, password)
    if sg_process_engine.split(':')[2].lower() != "running":
        if sg_process_engine.split(':')[2].lower() != "not found":
            # Try starting service
            logger("Try starting service", log_path, log_name)
            service_starter_regex("SgProcessEngine*", hostname, username_cloud, password)
            time.sleep(1.5)
            # Verify if service has started
            logger("Verify if service has started", log_path, log_name)
            sg_process_engine_verify = service_checker_regex("SgProcessEngine*", hostname, username_cloud, password)
            if sg_process_engine_verify.split(':')[2].lower() != "running":
                logger(f"Unable to start 'SgProcessEngine' manually --> {sg_process_engine_verify.split(':')[2]}", log_path, log_name)




    ### IIS Services ###
    logger(f"\n\n### Checking IIS Services ###", log_path, log_name)

    # Querying status of service
    iis_services = iis_checker(hostname, username_cloud, password).split('|')
    iis_server_running_counter = 0
    for iis_svc in iis_services:
        if 'Running' in iis_svc:
            iis_server_running_counter += 1

    if iis_server_running_counter != 3:
        # Try starting service
        logger("Try starting service", log_path, log_name)
        iis_restarter(hostname, username_cloud, password)
        time.sleep(5)
        # Verify if service has started
        logger("Verify if services have started", log_path, log_name)
        iis_services_verify = iis_checker(hostname, username_cloud, password).split('|')
        iis_server_running_counter = 0
        for iis_svc in iis_services:
            if 'Running' in iis_svc:
                iis_server_running_counter += 1
        if iis_server_running_counter <= 3:
            logger(f"Unable to start 'IIS Services' manually as described below:\n{iis_services_verify[0]}\n{iis_services_verify[1]}\n{iis_services_verify[2]}", log_path, log_name)



    # End of Log
    logger(f"\n{70 * '#'}", log_path, log_name)

except Exception as e:
    if "Caused by ConnectTimeoutError" in str(e):
        logger(f"Network Access to {hostname} via WinRM has failed. --> TCP 5985\nFull Error:\n{str(e)}\n", log_path, log_name)

