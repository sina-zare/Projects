
Table of Scripts 
1	Ansible	Ansible_DynamicHost_vCenter.py	Miremad-Vanak	All SysOps Team VMs	This script creates Ansible host file data for SysOps Team using vCenter team name.	❌	❌	❌	❌	SysOps
2	Confluence	Confluence_SysOps_Management_Servers.py	Miremad	Confluence specific page	This script updates SysOps Team server table on Confluence page.	❌	❌	❌	✅
Every 2 weeks on Saturday at 9:00

SysOps
3	Email	Email_Anonymous_Sender.py	SG	Mail Server	This script sends anonymous emails to a mail server for testing purposes.	❌	❌	❌	❌	SysOps
4	Jira	Jira_New_Issue.py	Miremad	Jira Server	This script creates a 'Network Access' issue for Network Team.	✅
(csv)	❌	❌	❌	SysOps
5	General	Password_Encryotor_Env.py	OS Wide	OS Global Environment Variables	This script Encrypts a given password and saves it to global system environment variables using symmetric method.	❌	❌	❌	❌	SysOps
6	General	Password_Decryptor_Env.py	OS Wide	OS Global Environment Variables	This script Decrypts an Encrypted password by using the encrypted password and encryption key.	❌	❌	❌	❌	SysOps
7	Virtual Machine	vCenter_VM_Creation_Date.py	Miremad-Vanak	vCenter VMs	This script gets the VM creation date and converts it to Jalali format.	❌	❌	❌	❌	SysOps
8	HA Proxy	haproxy-config-creator.py	Vanak	Rahkaran Abri VMs	This script updates HAProxy config file dynamically based on available vms in vCenter and reloads the service if a non conformity is detected.	❌	✅
(txt log)	❌	❌	SysOps
9	HA Proxy	haproxy-state-notifier.py	Vanak	HAProxy Service	This script monitors HAProxy service and mails the owner if the service is facing an abnormal situation and tries to bring it up.	❌	❌	❌	❌	SysOps
10	Grafana	Grafana_Datasource_Creds_Changer.py	Miremad-Vanak	Grafana Data Sources	This script changes credentials for a specific data source on every organization based on tokens. this operation is done for both Miremad and Vanak Grafanas.	❌	❌	❌	❌	SysOps
11	Zabbix	Zabbix_Get_Data_By_HostGroup.py	Miremad-Vanak	Zabbix Hosts	This script takes zabbix host group as input and gets all hosts related to that host group and print it on the screen	❌	❌	❌	❌	SysOps
12	General	Zabbix_Add_GPG.py	Miremad-Vanak	Zabbix Server	This script adds the Zabbix GPG public key to '/etc/apt/sources.list.d/zabbix.list' in order to trust the packages downloaded from Zabbix repositories configured in Nexus server.	❌	❌	❌	❌	SysOps
13	Zabbix	Zabbix_Add_Node_By_vCenter.py	Miremad-Vanak	vCenter VMs	This script searches the vCenter VMs by the specified  criteria and adds them to Zabbix server for monitoring.	❌	❌	❌	❌	SysOps
14	Zabbix	Zabbix_Add_vCenter_ICMP_Fully_Automated.py	Miremad	vCenter Managed VMs	This script adds the vCenter managed VMs to Zabbix automatically and monitors them via ICMP ping	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
15	Zabbix	Zabbix_Agent_Manager_ME_Fully_Automated.py	Miremad	Customer nodes in Zabbix	This script plays the key role in automating servers statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is direly required to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by Zabbix-Agent	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
16	Zabbix	Zabbix_Agent_Manager_VNK_Fully_Automated.py	Vanak	Customer nodes in Zabbix	This script plays the key role in automating servers statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is direly required to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by Zabbix-Agent	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
17	Zabbix	Zabbix_Create_User_From_File.py	Miremad-Vanak	Zabbix users	This script creates users in Zabbix using a .csv file.	✅
(csv)	❌	❌	❌	SysOps
18	Zabbix	Zabbix_Delete_Node.py	Miremad-Vanak	Zabbix nodes	This scrips deletes Zabbix nodes by host group name.	❌	❌	❌	❌	SysOps
19	Zabbix	Zabbix_Downtime_Report.py	Miremad	Zabbix URL monitored hosts	This script reports the downtime of monitored hosts including problem failure time, problem resolution time and total downtime of each host in the selected date.	❌	✅
(email)	sysops@abramad.cpm	❌	SysOps
20	Zabbix	Zabbix_Downtime_Report.exe	Miremad	Zabbix URL monitored hosts	This script reports the downtime of monitored hosts including problem failure time, problem resolution time and total downtime of each host in the selected date.
this is the user executable version holding all needed modules.	❌	✅
(email)	sysops@abramad.com	❌	SysOps
21	Zabbix	 Zabbix_Get_Active_Templates.py	Miremad-Vanak	Zabbix active templates	This script finds the active templates of Zabbix and pushes the exported 'json' outputs to Gitlab.	❌	❌	❌	✅
Daily at 1:00	SysOps
22	Zabbix	Zabbix_Node_Addition.py	Miremad-Vanak	Zabbix nodes	This script adds a single host "defined in the code" to Zabbix.	❌	❌	❌	❌	SysOps
23	Zabbix	Zabbix_Node_Updater_Remove_Add_Existing_Tags.py	Miremad-Vanak	Zabbix nodes	This script removes/adds single the host tags in Zabbix.	❌	❌	❌	❌	SysOps
24	Zabbix	 Zabbix_Node_Updater_Remove_Add_existing_Tags_Groups.py	Miremad-Vanak	Zabbix nodes	This script removes/adds tags and host groups in Zabbix.	❌	❌	❌	❌	SysOps
25	Zabbix	Zabbix_OnPrem_URL_ME_Fully_Automated.py	Miremad	Onpremise server URLs
MEA + MER	This script plays the key role in automating node statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is in dire need to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by web scenarios	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
26	Zabbix	Zabbix_OnPrem_URL_VNK_Fully_Automated.py	Vanak	Onpremise server URLs
VAT + VR1 + VR2 + VR3	This script plays the key role in automating node statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is in dire need to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by web scenarios	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
27	Zabbix	Zabbix_Ping_Logger.py	Miremad-Vanak	specific items of Zabbix hosts	This script records the values of specific items of a selected host while pinging it, meanwhile it logs the data in a file	❌	✅
(txt log)	❌	❌	SysOps
28	Zabbix	Zabbix_Problem_Alerter.py	Miremad-Vanak	Abramad teams	This script emails Zabbix problems of each team that are there for mor than 10 days to the owners	❌	✅
(html, zip)	sysops@abramad.com
network@abramad.com
system@abramad.com
ProductMGMT@abramad.com
development@abramad.com
itsm@abramad.com
support@abramad.com
csb@abramad.com
Security@abramad.com
openstack@abramad.com
datacenter@abramad.com
mlplatform@abramad.com
kubernetes@abramad.com
sds@abramad.com
epm@abramad.com
caas@abramad.com
ProductDevelopment@abramad.com
foroughe@systemgroup.net
ramins@systemgroup.net	✅
Every Saturday and Monday at 9:00	All Abramad Teams
29	Zabbix	Zabbix_RA_Fully_Automated.py	Miremad	Rahkaran Abri URLs	This script plays the key role in automating node statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is in dire need to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by web scenarios	❌	✅
(email)	sysops@abramad.com	❌	SysOps
30	Zabbix	Zabbix_VRA_Fully_Automated.py	Vanak	Rahkaran Abri URLs	This script plays the key role in automating node statuses in Zabbix by means of Addition/Deletion/Enabling/Disabling .

Since customer nodes keep being powered on and off, deleted and created, a system is in dire need to manage the status of nodes in Zabbix.

Nodes: The ones that are monitored by web scenarios	❌	✅
(email)	sysops@abramad.com	✅
Every 4 hours	SysOps
31	Zabbix	Zabbix_Replicator.py	Miremad - Vanak	Zabbix Server	This script replicates a secondary Zabbix server to match the primary Zabbix server, making the secondary server identical to the primary.

Replicating items:
HostGroups
Active Templates
Hosts
❌	❌	❌	❌	SysOps
32	Zabbix	Zabbix_SNMP_Node_Addition.py 	Miremad - Vanak	Zabbix hosts	
This Python script automates the process of adding multiple network devices (such as iLOs or network switches) as monitored hosts in a Zabbix server using the Zabbix API.

✅
(csv)	❌	❌	❌	SysOps
33	Zabbix	Zabbix_SNMP_node_Update.py 	Miremad - Vanak	Zabbix hosts	This Python script connects to a Zabbix server and updates SNMP interface settings for all hosts in a specific host group (e.g., “ILO”) using the Zabbix API.	❌	❌	❌	❌	SysOps
34	Zabbix	Zabbix_Tag_Remover.py	Miremad - Vanak	Zabbix hosts	This Python script connects to multiple Zabbix servers and removes a specific tag (__zbx_jira_test) from all hosts that contain it.	❌	❌	❌	❌	SysOps
35	Zabbix	 Zabbix_Tag_Updater.py	Miremad - Vanak	Zabbix hosts	This Python script connects to multiple Zabbix servers and adds a custom tag (__zbx_jira: 1) to all hosts that don't already have it.
If the tag  is not already present on a host, it updates the host to include it.	❌	❌	❌	❌	SysOps
36	Zabbix	Zabbix_VRA_Node_Add_Excel.py	Miremad - Vanak	Zabbix hosts	This Python script automates the creation of Zabbix hosts based on data from an Excel spreadsheet. It reads VM details, connects to a Zabbix server, and registers each VM as a monitored host with proper tags, groups, and templates.	✅
(xlsx)	❌	❌	❌	SysOps
37	Zabbix	 Zabbix_VRA_Node_Automated.py	Miremad - Vanak	Zabbix hosts based on vCenter VMS	This Python script automates the discovery and registration of virtual machines (VMs) from a VMware vCenter server into Zabbix for monitoring. It retrieves VM information based on naming patterns, categorizes them by power state, and creates Zabbix host entries with appropriate tags, templates, and groups. The script also disables Zabbix hosts for VMs that are powered off.	❌	❌	❌	❌	SysOps
38	Zabbix	Zabbix_VRA_Node_Updater.py 	Miremad - Vanak	Zabbix hosts	This Python script connects to a Zabbix server and identifies hosts (example: all hosts whose names start with vra-) It optionally prepares them for group and tag updates. The script can be used to batch-update host metadata in Zabbix	❌	❌	❌	❌	SysOps
39	Zabbix	 Zabbix_Web_TCP_Node_Adder_From_File.py	Miremad - Vanak	Zabbix hosts	This script automates the creation of Zabbix hosts for TCP and HTTP service monitoring by reading structured data from a CSV file. It supports both ME and VNK environments and uses Zabbix API to register hosts with appropriate templates, groups, tags, and interfaces.	✅
(csv)	❌	❌	❌	SysOps
40	Zabbix	Zabbix_iLO_HTTP_Node_Addition.py	Miremad - Vanak	Zabbix hosts	
This Python script automates the bulk creation of Zabbix hosts using data from a CSV file. It performs the following tasks:

Decrypts Zabbix credentials securely from environment variables using Fernet encryption.

Parses host information (hostname, IP, and URL macro) from a CSV file.

Connects to the Zabbix API using provided credentials.

Dynamically retrieves template and host group IDs based on names.

Creates new Zabbix hosts with:

Agent interface (useip: 1, port 10050)

Custom macros (e.g., {$ILO.URL})

Tags and descriptions

Assigned templates and host groups

Logs the created host IDs and handles errors gracefully.

This script is designed to be generic and reusable, adaptable for other types of devices (e.g., switches, servers) by modifying templates, groups, and tags.

✅
(csv)	❌	❌	❌	SysOps
41	Zabbix	Zabbix_Maintenance.py	Miremad - Vanak	Maintenance	
This script automates creating or updating Zabbix maintenance windows for hosts listed in a CSV, with duration, naming, and error handling.

It connects to a chosen Zabbix server (from two predefined URLs) using user-provided credentials, then:

Reads a CSV file (C://Temp//maintenance_nodes.csv) to get a list of hostnames.

Verifies hosts in Zabbix and collects their host IDs.

Prompts the user to either:

Create a new maintenance window, or

Edit an existing maintenance by name.

Calculates the maintenance duration (from user-provided hours/minutes) and sets start and end times.

For new maintenance, it automatically generates an incremental name (Automated-Maintenance-XX).

Creates/updates the maintenance in Zabbix with:

Host IDs

Active time window

Description including time and username

Provides user-friendly terminal prompts (with color formatting) and handles errors gracefully with clear messages.

✅
(csv)	❌	❌	❌	SysOps/Support
42	Zabbix	Zabbix_Maintenance_Minimal.py	Miremad - Vanak	Maintenance	
This script automates creating one-time Zabbix maintenance windows for a list of hosts from a CSV file, with user-defined duration and auto-incremented naming.


It connects to a selected Zabbix server, reads hostnames from a CSV file, and automatically creates a new maintenance window for those hosts.

Key steps:

Prompts the user to choose a Zabbix server and enter credentials.

Asks for the maintenance duration (hours and/or minutes).

Reads hostnames from C://Temp//maintenance_nodes.csv and looks them up in Zabbix to get host IDs.

Generates a unique, incremented maintenance name (Automated-Maintenance-XX).

Creates a one-time maintenance window in Zabbix with:

The selected hosts,

Start and end times based on the duration,

A description including duration and username.

Provides feedback on successes or errors and exits cleanly.

✅
(csv)	❌	❌	❌	SysOps/Support
41	Netbox	NetBox_Create_VM.py 	Miremad - Vanak	Netbox Virtual Machines	
This script automates the provisioning of a new virtual machine in NetBox along with its network configuration. Here's what it does:

Connects to NetBox using the pynetbox API and an authentication token.

Fetches all existing IP prefixes and their associated VRFs.

Calculates subnet details (like gateway and usable IPs) from a provided CIDR using the ipaddress module.

Creates a new virtual machine  with specified CPU, memory, disk, platform, site, and custom fields.

Adds a virtual interface (eth0) to the VM.

Assigns an IP address to that interface, associating it with the appropriate VRF and DNS name.

Sets the assigned IP as the VM’s primary IPv4 address.

Overall, this script fully automates the lifecycle of a VM in NetBox from creation to IP assignment.

❌	❌	❌	❌	SysOps
42	Netbox	NetBox_Get_Info.py 	Miremad - Vanak	Netbox Virtual Machines	
This script connects to a NetBox instance and retrieves detailed infrastructure data. Specifically, it:

Lists all clusters, VM roles, sites, and platforms.

Displays all virtual machines along with their custom fields.

Lists all defined custom fields with metadata (label, type, required status, etc.).

Fetches all IP prefixes and prints their associated VRF names and IDs.

It's mainly used for auditing and exploring NetBox inventory and configuration data.

❌	❌	❌	❌	SysOps
43	Netbox	NetBox_VM_Addition_Fully_Automated.py 	Miremad - Vanak	Netbox Virtual Machines, Prefixes, IPv4	This script automates the discovery and registration of virtual machines from multiple vCenter instances into NetBox.
Connects to NetBox and builds dictionaries of:

Clusters

Platforms (Operating Systems)

IP Prefixes with VRF & VLAN mappings


Connects to a list of vCenter servers.

For each VM, extracts:

Name, FQDN, OS, power state, cluster, CPU, memory, disk

VLAN ID from distributed port group

IP address from guest info


Matches VLAN IDs from vCenter to NetBox prefixes to derive:

Subnet, CIDR IP, VRF ID, VLAN ID

Flags:

VMs missing IPs

VLANs not found in NetBox


For each VM:

Creates a virtual machine entry in NetBox with relevant metadata.

Adds a virtual interface.

If VM is powered on:

Assigns its IP to the interface (or reassigns if already in use).

Sets the primary IPv4 address.

Lists:

VMs with no IPs

VLANs that couldn't be mapped in NetBox

❌	❌	❌	❌	SysOps
44	Reporting	 Product_Line_Resources.py	Miremad - Vanak	Abramad Products	This Python script collects resource usage data for virtual machines from multiple vCenter servers, categorizes them by product line based on name prefixes, and pushes custom Prometheus metrics to a Pushgateway for monitoring and alerting.
Its purpose is to monitor and track the infrastructure resource usage of different environments/product lines (e.g., ME OnPrem, DaaS, Vanak) by exporting structured, real-time metrics to Prometheus.

Main Steps:
Connects to multiple vCenter servers, gathers data for all VMs:

Name, power status, cluster

CPU, memory, disk usage

Categorizes VMs into product lines (e.g., MER, VR1, VRA) using name prefixes.

Calculates per-product totals:

Number of VMs (on/off)

Used memory, CPU, and disk (on/off)

Defines and updates Prometheus metrics using prometheus_client, including:

Per-product resource usage

Script duration, success status, error message

Total and failed script executions

Pushes all metrics to a Prometheus Pushgateway

Maintains counters for total runs and failures using local files.

❌	❌	❌	✅
Daily at 2:00	Abramad
Managers
45	Backup	 Restic.py	Miremad - Vanak	PostgreSQL DBs	This script automates PostgreSQL database backups over SSH using pg_dumpall, stores the backups using Restic (a secure and efficient backup tool), and supports backup, restore, listing, and deletion of snapshots. It reads target client info from a file and interacts with Restic's REST server.

Supported Operations (via CLI) 
backup:

SSH into target(s), run pg_dumpall, and store the SQL file.

Backup the file using Restic.

Apply a retention policy (--keep-daily 7).

Clean up the dumped file.

restore:

Restore the latest or specified snapshot for the selected host using Restic.

list:

List snapshots and their stats for the given host(s).

remove:

Remove one or all snapshots for a given host using restic forget and prune.

Key Features 
Uses a client list file (restic_clients.txt) with host info and credentials.

Environment variables dynamically set for each operation.

Interactive prompt for single host selection.

Supports bulk operations with target = all.

 Purpose 
To securely back up and manage PostgreSQL databases from remote hosts into a Restic repository over HTTP, with easy CLI interaction.



✅
(pg_dumps)	✅
(snapshots)	❌	❌	SysOps
46	Reporting	All_VMs_Info.py 	Miremad	Customer VMs	
Main Purpose 
The script collects detailed information about VMs (matching a specific naming pattern) from a vCenter server, enriches it with agent info from a CRM Excel file, generates a daily report in Excel, sends it via email, and pushes execution metrics to a Prometheus Pushgateway.

Key Functions 
VM Data Collection
Connects securely to vCenter.

Filters VMs by name prefixes (e.g., MER-, MEF-, etc.).

For each VM, collects:

Hardware info: RAM, CPU, disk sizes (SSD/HDD/Capacity).

Metadata: power state, creation date, cluster, ticket number.

Custom attributes: public IP, URL, WAF, VPN, IDS, dongle, Persian name.

Agent info from a CRM Excel file using the National ID.

Report Generation
Generates an Excel report: Servers-Full-Report-Agents.xlsx with all VM and agent data.

Email Report
On weekdays, sends the Excel report via email to predefined recipients.

HTML body contains a formal Persian message.

Prometheus Metrics
Pushes the following script execution metrics:

script_exec_duration_seconds

script_success

script_total_execs

script_total_failed_execs

script_last_error_message

✅
(.csv)	✅
(.zip)	sales@abramad.com
accounting@abramad.com
admin@abramad.com
sysops@abramad.com	❌	Support Team
Sales team
47	Reporting	All_VMs_info_Agents.py 	Miremad	Customer VMs	This script is same as 'All_VMs_Info.py ' with this difference that it collects the agent information of each VM in a separate cell.	✅
(.csv)	✅
(.zip)	support@abramad.com
ITSM@abramad.com	❌	Support Team
Sales team
48	Update
Scheduling	Downtime.py 	Miremad	Customer VMs	
This script automates the process of managing and notifying customers about scheduled downtimes for virtual machine (VM) updates in the infrastructure.
The script runs on the 20th of each month to rebuild VM lists, then processes updates in batches on specific weekdays until all VMs are updated, with separate handling for VIP customers. 

Core Functionality:
1. VM Inventory & Classification:
   - Connects to vCenter to retrieve a list of VMs (filtered by prefixes like MER-, MES-, etc.)
   - Classifies VMs into categories (normal/VIP) and checks their power status

2. Update Scheduling:
   - Schedules VM updates for 3 days in the future
   - Handles different update batches based on the day of the week:
     - Sat/Sun/Mon/Wed: Updates normal customers (up to 120 VMs per batch)
     - Tue: Updates VIP customers (special handling for Ramak, Alaziz, Domino, TatPSA)

3. Notification System:
   - Generates email/SMS notification templates in Persian (Jalali calendar)
   - Sends emails to support teams with:
     - Lists of VMs to be updated
     - Attachments for system teams (CSV files)
     - Instructions for SMS/ticket notifications

4. Tracking & Metrics:
   - Maintains version numbers for update batches
   - Tracks already updated VMs to avoid duplicates
   - Uses flags  to track completion status
   - Pushes execution metrics to Prometheus Pushgateway (duration, success/fail, error tracking)

5. Security:
   - Uses encrypted credentials for vCenter/SMTP access
   - Handles SSL certificates for secure connections

Key Features:
- Persian calendar/localization support
- Automated CSV generation for different VM categories
- Error handling and alerting for script failures
- Integration with ticketing/SMS systems via file outputs



❌	✅
(.zip)	support@abramad.com
system@abramad.com	✅
15th to 30th of each month at 10:30	Support Team
Managed Services Team
Sales Team
Abramad Managers
49	Update
Scheduling	Downtime_VNK.py 	Vanak	Customer VMs	
This script automates the process of managing and notifying customers about scheduled downtimes for virtual machine (VM) updates in the infrastructure.
The script runs on the 20th of each month to rebuild VM lists, then processes updates in batches on specific weekdays until all VMs are updated, with separate handling for VIP customers. 

Core Functionality:
1. VM Inventory & Classification:
   - Connects to vCenter to retrieve a list of VMs (filtered by prefixes and folder name)

2. Update Scheduling:
   - Schedules VM updates for 3 days in the future
   - Handles different update batches based on the day of the week:
     - Sat/Sun/Mon/Tue/Wed: Updates customers (up to 120 VMs per batch - configurable)

3. Notification System:
   - Generates email/SMS notification templates in Persian (Jalali calendar)
   - Sends emails to support teams with:
     - Lists of VMs to be updated
     - Attachments for system teams (CSV files)
     - Instructions for SMS/ticket notifications

4. Tracking & Metrics:
   - Maintains version numbers for update batches
   - Tracks already updated VMs to avoid duplicates
   - Uses flags  to track completion status
   - Pushes execution metrics to Prometheus Pushgateway (duration, success/fail, error tracking)

5. Security:
   - Uses encrypted credentials for vCenter/SMTP access
   - Handles SSL certificates for secure connections

Key Features:
- Persian calendar/localization support
- Automated CSV generation for different VM categories
- Error handling and alerting for script failures
- Integration with ticketing/SMS systems via file outputs



❌	✅
(.zip)	
support@abramad.com
system@abramad.com

✅
15th to 30th of each month at 10:30	Support Team
Managed Services Team
Sales Team
Abramad Managers
50	Ticketing	 Downtime_Portal_Notification.py	Miremad	Customer VMs	
This script automates customer notifications for scheduled VM maintenance downtimes by:

Data Collection & Processing

Reads a list of VMs (Planned_For_Update_System.csv) scheduled for updates.

Fetches customer details (national ID, agent name, email, phone) from the latest CRM report (CRM Reports/).

Connects to vCenter to validate VM details (name, national ID).

Data Deduplication & Formatting

Merges VM and CRM data, ensuring no duplicates (based on national ID).

Generates a structured Excel file (Portal_Notification.xlsx) for portal-based notifications.

Automated Email Notification

Sends an email (with retry logic) to the ITSM/support team with:

A formatted HTML message (in Persian).

The generated Excel file as an attachment.

Updates a version tracker (Version_Check.txt) to prevent duplicate notifications.

Monitoring & Error Handling

Tracks script execution metrics (duration, success/failure) via Prometheus Pushgateway.

Logs errors and retries failed email sends.

Output 
Excel file (Portal_Notification.xlsx) with customer contact details for portal notifications.

Email to ITSM/support teams with instructions and attachments.

Metrics pushed to Prometheus for monitoring.

This script ensures timely, accurate customer notifications for maintenance windows while minimizing manual effort.

✅
(.csv)	✅
(.zip)	sales@abramad.com
support@abramad.com
noc@abramad.com	✅
15th to 30th of each month at 10:40	Support Team
Managed Services Team
Sales Team
Abramad Managers
51	Jira Change Management	 Ehsan_Jira_Change_MGMT.py	Miremad - Vanak	Jira Changes	
This script automates change management notifications by processing Jira change requests from an email inbox and sending calendar invites to relevant stakeholders and ensures timely, automated notifications for IT change management processes, reducing manual effort and improving coordination.

Key Functions
1. Email Processing  
   - Connects to an IMAP email server and checks the `ChangeManagement` folder for unread messages.  
   - Extracts change request details (ticket number, subject, assignee, start/end times, stakeholders) from email bodies.  

2. Data Formatting  
   - Converts dates/times from Gregorian to Shamsi (Jalali) and 12-hour to 24-hour formats.  
   - Maps email groups (e.g., `DevelopmentTeamMembers`) to their distribution lists using predefined dictionaries.  

3. Calendar Invite Generation 
   - Creates iCalendar (.ics) events for each change request with:  
     - Start/end times
     - Jira ticket link
     - Stakeholder attendees (assignee, informed teams, and default recipients like `abramadalert@abramad.com`).  

4. Email Notifications  
   - Sends HTML-formatted emails with:  
     - A summary table of change details.  
     - An attached .ics calendar invite.  
   - Uses SMTP to dispatch emails.  

5. Monitoring & Error Handling
   - Tracks script execution metrics (duration, success/failure) via Prometheus Pushgateway.  
   - Logs errors and retries failed operations.  



❌	✅
(.ics)	sysops@abramad.com
network@abramad.com
system@abramad.com
ProductMGMT@abramad.com
development@abramad.com
itsm@abramad.com
support@abramad.com
csb@abramad.com
Security@abramad.com
openstack@abramad.com
datacenter@abramad.com
mlplatform@abramad.com
kubernetes@abramad.com
sds@abramad.com
epm@abramad.com
caas@abramad.com
ProductDevelopment@abramad.com
foroughe@systemgroup.net
ramins@systemgroup.net	✅
Every 15 minutes	ITSM Team
52	vCenter	Empty_Attributes.py 	Miremad	vCenter Attributes	
This script audits and reports missing or incorrect VM attributes in a vCenter environment, focusing on both powered-on and powered-off VMs. Here's what it does:

Core Functionality 
VM Attribute Validation

Connects to vCenter and scans VMs with specific prefixes (MER-, MEF-, etc.).

Checks for missing/incorrect attributes:

Creation date (compares custom field vs. actual VM creation date)

Persian name

National ID

Shutdown date/ticket (for powered-off VMs)

Public IP and URL (skips DB servers)

Categorization & Reporting

Separates issues into powered-on and powered-off VM lists.

Generates HTML tables for each defect type (e.g., empty Persian names, wrong dates).

Sends email alerts (via SMTP) with categorized defect reports:

5 email templates for different defect types (e.g., "Create Date Defects").

Localization & Security

Uses Persian (Jalali) dates for reporting.

Monitoring

Tracks execution metrics (duration, success/failure) via Prometheus Pushgateway.

Key Features 
Exclusions: Skips templates/test VMs (e.g., MEI-ava-centos7-template01).

Dynamic Emails: Only sends reports if defects exist (e.g., skips "No defects" emails).

RTL Support: Formats HTML emails for Persian language.


Ensures VM metadata accuracy by automating audits and notifying support teams to fix missing/incorrect attributes.

❌	✅
(email)	support@abramad.com	✅
Daily at 9:15	Support_Team
53	Rahkaran	SA_Authenticator.py

Derivatives:
SA_Authenticator_RAPlus.py
VNK_SA_Authenticator.py
Miremad - Vanak	MSSQL SA Password	
This script controls access to a sensitive system password by verifying a user's permissions through Active Directory (AD) group membership and local administrator checks.

Key Functions 
AD Group Validation

Connects to LDAP to fetch the user's AD groups.

Validates if the user exists in the Customers OU (or cloud.local domain for certain users).

Local Admin Check

Lists local administrators on the machine using Windows API (win32net).

Compares the user's AD groups with local admin groups.

Password Decryption

If authorized, decrypts and displays a secured password (stored in environment variables)

The password is only shown for 30 seconds before the script exits.

Access Control

Grants access if the user is in both an AD group and the local admin group.

Denies access with an error message if checks fail.

Security Features 
Uses LDAPS (secure LDAP) for AD queries.

Passwords are hidden during input (stdiomask.getpass).

Encrypted credentials are stored in environment variables and decrypted on-the-fly.

Clears the console (cls) to prevent password visibility after use.

Output Examples 
Success:

Access Granted: sina.z ~~> Administrators  
Copy the password within 30 seconds:  
xYz123!@#  
Failure:

You Don't have Permission to use SA Password.  
contact 'support@abramad.com'  
Purpose 
Ensures only authorized users (AD + local admins) can access a protected password, enhancing security for privileged operations.

Note: The script exits after 10 seconds on errors or access denial.

❌	❌	❌	❌	Support_Team
54	vCenter	VM_Delete_Alert.py 	Miremad	Customer VMs	
This script identifies and alerts about inactive VMs that have been powered off for more than 31 days, recommending their deletion to free up resources and Automates cleanup of unused VMs to optimize resource utilization.

Key Functions 
VM Inventory Scan

Connects to vCenter  and scans for powered-off VMs (excluding templates/test VMs).

Focuses on customer VMs with prefixes like MER-, MEF-, MES-, etc.

Inactivity Detection

Checks each VM's shutdown date (custom attribute 401) and compares it with the current Persian (Jalali) date.

Flags VMs inactive for >31 days, recording:

VM name

Persian name (custom attribute 103)

Days since shutdown

Email Notification

Sends an HTML-formatted email to support team (support@abramad.com) listing:

Inactive VMs

Duration of inactivity

Errors (e.g., missing shutdown dates)

Uses SMTP with encrypted credentials.

Security & Monitoring

Decrypts vCenter credentials using Fernet encryption.

Tracks script execution metrics (duration, success/failure) via Prometheus Pushgateway.



❌	✅
(email)	support@abramad.com	✅
Every week on Saturday at 9:30	Support_Team
55	vCenter	VM_Delete_Alert_VNK.py 	Vanak	Customer VMs	
This script identifies and alerts about inactive VMs that have been powered off for more than 31 days, recommending their deletion to free up resources and Automates cleanup of unused VMs to optimize resource utilization.

Key Functions 
VM Inventory Scan

Connects to vCenter  and scans for powered-off VMs (excluding templates/test VMs).

Focuses on customer VMs with prefixes like MER-, MEF-, MES-, etc.

Inactivity Detection

Checks each VM's shutdown date (custom attribute 401) and compares it with the current Persian (Jalali) date.

Flags VMs inactive for >31 days, recording:

VM name

Persian name (custom attribute 103)

Days since shutdown

Email Notification

Sends an HTML-formatted email to support team (support@abramad.com) listing:

Inactive VMs

Duration of inactivity

Errors (e.g., missing shutdown dates)

Uses SMTP with encrypted credentials.

Security & Monitoring

Decrypts vCenter credentials using Fernet encryption.

Tracks script execution metrics (duration, success/failure) via Prometheus Pushgateway.



❌	✅
(email)	support@abramad.com	✅
Every week on Saturday at 9:30	Support_Team
56	Reporting	VRA-CloudLock_Members.py 	Vanak	Rahkaran Abri Lock Servers	
This script monitors CloudLock server capacity in a VRA environment, alerting when customer counts approach limits (750+).
It ensures proactive scaling of CloudLock infrastructure by:

Preventing overutilization of existing servers.

Automating capacity alerts in Persian for local teams.

Integrating with monitoring tools (Prometheus).

Key Functions 
VM Inventory Scan

Connects to vCenter (vra-vc01.abramad.com) to identify CloudLock servers (VMs prefixed with VRA-CloudLock).

Collects each server's hostname and IP address.

Customer Count Check

Queries each CloudLock server's web interface (http://[IP]:22352/license_monitoring/sessions.html).

Uses regex to extract:

Connected customer IPs (10.x.x.x)

Customer domain names (*.cloud.local)

Tracks unique customers per CloudLock server.

Capacity Alerts

Triggers email alerts when any CloudLock server exceeds 750 customers.

Email includes:

Server name (e.g., vra_cloudlock01)

Current customer count

Recommendation to provision a new CloudLock server.

Error Handling & Metrics

Logs failures (e.g., unreachable servers) and sends error emails.

Tracks execution metrics (duration, success/failure) via Prometheus Pushgateway.



Note: Uses Fernet encryption for vCenter credentials and skips non-responsive servers.

❌	✅
(email)	
support@abramad.com
sysops@abramad.com

✅
Every Tuesday at 10:00	Support_Team
Managed Services Team
57	Reporting	 VRA_CloudLock_Members_Monitoring.py	Vanak	Rahkaran Abri Lock Servers	
This script monitors CloudLock license servers in a VRA environment, tracking client connections and license dongle usage for capacity planning.

Key Functions 
VM Discovery

Connects to vCenter (vra-vc01.abramad.com) to identify CloudLock servers (VMs named VRA-CloudLock*)

Collects each server's hostname and IP address

License Monitoring

Queries each server's web interface for this path: (:22352/license_monitoring/sessions.html)

Extracts:

Connected clients (IPs and cloud.local domains)

License dongle serial numbers

Client counts per dongle

Metrics Collection

Tracks Prometheus metrics for:

Total clients per server

Clients per dongle serial

Dongle count per server

Alerting

Sends email alerts when servers approach capacity (commented out in current version)

Reports errors to abramadsysops@abramad.com

Technical Details 
Uses Fernet encryption for vCenter credentials

Parses HTML with regex to extract license data

Pushes metrics to Prometheus Pushgateway

Supports Persian (RTL) email formatting

Purpose 
The script runs automated checks and exports metrics for integration with monitoring systems while handling errors gracefully.

❌	❌	❌	✅
Every 30 minutes	Support_Team
Abramad Managers
58	Rahkaran	SA_Password_Changer_Env.py	Miremad - Vanak	MSSQL SA User	
This script automates the change of SQL Server SA (System Administrator) passwords with enhanced security measures for each new Rahkaran server. Here's what it does:

Core Functions 
Password Generation

Creates strong 17-character passwords containing:

Lowercase & uppercase letters

Numbers

Special symbols (!@#$%^&*()-_=+)

Uses cryptographically secure randomization (secrets module)

SQL Server Password Change

Connects to local SQL Server using the current SA password

Executes ALTER LOGIN command to update the SA password

Handles connection errors gracefully

Secure Credential Storage

Encrypts the new password using Fernet encryption

Stores both the encrypted password and decryption key in:

System Environment Variables (sgsp and sgsk)

Uses Windows setx command for persistent storage

Security Features 
No plaintext passwords – All credentials are encrypted

Minimum complexity requirements – Guarantees mixed character types

Random shuffling – Prevents predictable password patterns

Error handling – Prevents exposure of sensitive data during failures


Note: Requires admin privileges to modify system environment variables.

❌	❌	❌	❌	Support_Team
59	vCenter	vCenter_Get_VM_PortGroup.py 	Miremad - Vanak	VM PortGroup	
This script audits virtual machine network configurations in a VMware vCenter environment, specifically tracking:

Key Functions 
vCenter Connection

Securely connects to vCenter using encrypted credentials

Network Configuration Audit

Retrieves all VMs and their:

NIC connection status (Connected/Disconnected)

Port groups (Distributed Virtual Switch only)

VLAN IDs (for each port group)

Output

Prints a structured report to console:

VM Name: [VM_NAME]  
  NIC Status: [Connected/Disconnected]  
  Port Group: [PORTGROUP_NAME], VLAN ID: [VLAN_ID]  
Purpose 
Helps administrators:

Verify correct network assignments

Troubleshoot connectivity issues

Maintain VLAN configuration records

Note: Designed for VMware Distributed Virtual Switches (DVS) – skips standard port groups.

❌	❌	❌	❌	SysOps Team
60	vCenter	vCenter_VM_Creation_Date.py	Miremad - Vanak	VM Creation Date	
This script searches for virtual machines across multiple vCenter servers and reports their details with Persian calendar support. Here's what it does:

Key Features 
Multi-vCenter Search

Checks 4 vCenter servers simultaneously:

vts-vc01, vab-vc01, vra-vc01, me-vc01

Uses encrypted credentials (Fernet) for secure authentication

VM Identification

Searches by both VM name and hostname

Compares against a predefined list from vm_names.csv

Detailed Reporting

Logs results with color-coded output (INFO=green, WARNING=yellow, ERROR=red)

Converts creation timestamps to Jalali (Persian) calendar with Tehran timezone

Tracks whether VMs are found/missing

Error Handling

Gracefully handles connection failures

Skips inaccessible vCenters without crashing

Output Example 
2023-08-15 14:30:00 - INFO - Searching for VM: test-server
2023-08-15 14:30:02 - INFO -     * Found in me-vc01.abramad.com: Test-Server (test-server.cloud.local)
2023-08-15 14:30:02 - INFO -     * Creation Date (Tehran +3:30): 1402/05/24 10:15:00

Note: Requires a CSV input file at C:\Temp\vm_names.csv with VM names to search.

✅
(.csv)	❌	❌	❌	SysOps Team
61	Backup	Sintinel.py	backup clients	postgresql dumps + directories	
Small backup agent that connects to remote hosts over SSH, creates PostgreSQL dumps or archives directories, and pushes encrypted, deduplicated snapshots to a central rest-server repository using Restic.

restserver — restic/rest-server: HTTP endpoint that stores restic repositories.
sintinel — backup agent container that reads sintinel_clients.txt, connects to each client via SSH, performs either a pg_dump (for PostgreSQL backups) or archives a directory, then pushes snapshots to the rest-server repository using Restic.
Snapshots are encrypted, compressed and deduplicated by Restic.

Features 
Agentless backups over SSH (no agent required on the client)
PostgreSQL dumps (pg_dump) or directory archives (tar)
Pushes encrypted Restic snapshots to central rest-server
Retention policy support (restic forget + prune)
Optional metrics pushed to Prometheus Pushgateway
Requirements 
SSH access from the sintinel container to each client (private key mounted into container)
sintinel_clients.txt (one line per client)
Reasonable filesystem permissions on mounted volumes for persistence
✅
(.txt)	❌	❌	✅
Everyday
at 00:00	SysOps Team
62	GitOps	GitOps_Zabbix_pull.py	Miremad	GitLab	
This script automates pulling and applying Zabbix server and agent2 configuration files from a Git repository.

Functions:
1. Git Operations - Clones/pulls configuration files from a GitLab repository using an authentication token
2. File Synchronization - Copies server-specific configuration files from the local repository to `/etc/zabbix`
3. Server Identification - Uses hostname to locate the correct server-specific configuration directory in the repo
4. Logging - Tracks all operations and errors to a log file

Purpose: Maintains Zabbix configuration by synchronizing local configs with version-controlled files from a central repository, ensuring consistent configuration across servers.

❌	❌	❌	❌	SysOps Team
63	GitOps	GitOps_Zabbix_push.py	Miremad	GitLab	
This script automates backing up Zabbix server and agent2 configuration files to a Git repository.

Functions:**
1. File Collection - Copies specified Zabbix config files from `/etc/zabbix/` to a local Git repository
2. Git Operations - Commits and pushes the collected configuration files to a GitLab repository
3. Server Identification - Uses hostname to organize files in server-specific directories within the repo
4. Authentication - Uses a GitLab token for secure repository access

Purpose: Creates version-controlled backups of Zabbix configuration files by pushing local config changes to a central Git repository for change tracking and disaster recovery.

❌	❌	❌	❌	SysOps Team
64	GitOps	GitOps_Patroni_pull.py	Miremad	GitLab	
This script automates pulling and applying Patroni configuration files from a Git repository.

Functions:
1. Git Operations - Clones/pulls configuration files from a GitLab repository using an authentication token
2. File Synchronization - Copies server-specific configuration files from the local repository to `/etc/patroni`
3. Server Identification - Uses hostname to locate the correct server-specific configuration directory in the repo
4. Logging - Tracks all operations and errors to a log file

Purpose: Maintains Patroni configuration by synchronizing local configs with version-controlled files from a central repository, ensuring consistent configuration across servers.

❌	❌	❌	❌	SysOps Team
65	GitOps	GitOps_Patroni_push.py	Miremad	GitLab	
This script automates backing up Patroni configuration files to a Git repository.

Functions:**
1. File Collection - Copies specified Patroni config files from `/etc/patroni/` to a local Git repository
2. Git Operations - Commits and pushes the collected configuration files to a GitLab repository
3. Server Identification - Uses hostname to organize files in server-specific directories within the repo
4. Authentication - Uses a GitLab token for secure repository access

Purpose: Creates version-controlled backups of Patroni configuration files by pushing local config changes to a central Git repository for change tracking and disaster recovery.

❌	❌	❌	❌	SysOps Team
66	vCenter	All_VMs_Info_VNK.py	Vanak	VMs	
The script retrieves and reports detailed information about customer virtual machines (VMs) hosted on a vCenter server, focusing on specific metrics for resource management. Key operations include:

Configuration and Initialization: Sets up Prometheus metrics for execution tracking, VM specifications, and establishes email settings.

vCenter Connection: Connects to the vCenter server using encrypted credentials stored in environment variables, establishing a secure connection.

VM Data Collection:

Identifies VMs based on specified naming prefixes and directories.
Collects detailed specifications for each VM, including:
General Information: Name, hostname, OS, power state, and product line.
Compute Resources: CPU type and core count, and memory allocation.
Network Details: Connection status, VLAN ID, and IP addresses (public and private).
Storage Metrics:
SSD, HDD, NVMe, and hybrid disk sizes in bytes and total capacity.
Each storage type is tracked with specific metrics labeled by VM name and storage cluster.
Excel Report Generation: Writes VM data to an Excel file, which is then compressed into a password-protected ZIP archive.

Email Notification: Sends an email to specified recipients with the attached report.

Error Handling and Metrics Reporting: Captures execution errors, tracks overall execution success and failure counts, and pushes this data to a Prometheus Pushgateway.

Finalization: Ensures comprehensive metric collection and reports the success or failure of the script execution.

❌	✅
(.zip)	sales@abramad.com
admin@abramad.com
accounting@abramad.com
sysops@abramad.com	❌	Sales/Finance/Support Team
67	vCenter	All_VMs_Info_Unified.py	Vanak and Miremad	VMs	
The script retrieves and reports detailed information about customer virtual machines (VMs) hosted on a vCenter server, focusing on specific metrics for resource management. Key operations include:

Configuration and Initialization: Sets up Prometheus metrics for execution tracking, VM specifications, and establishes email settings.

vCenter Connection: Connects to the vCenter server using encrypted credentials stored in environment variables, establishing a secure connection.

VM Data Collection:

Identifies VMs based on specified naming prefixes and directories.
Collects detailed specifications for each VM, including:
General Information: Name, hostname, OS, power state, and product line.
Compute Resources: CPU type and core count, and memory allocation.
Network Details: Connection status, VLAN ID, and IP addresses (public and private).
Storage Metrics:
SSD, HDD, NVMe, and hybrid disk sizes in bytes and total capacity.
Each storage type is tracked with specific metrics labeled by VM name and storage cluster.
Excel Report Generation: Writes VM data to an Excel file, which is then compressed into a password-protected ZIP archive.

Email Notification: Sends an email to specified recipients with the attached report.

Error Handling and Metrics Reporting: Captures execution errors, tracks overall execution success and failure counts, and pushes this data to a Prometheus Pushgateway.

Finalization: Ensures comprehensive metric collection and reports the success or failure of the script execution.

❌	✅
(.zip)	sales@abramad.com
admin@abramad.com
accounting@abramad.com
sysops@abramad.com	✅
Everyday
at
08:00	Sales/Finance/Support Team
68	Zabbix	Zabbix_Maintenance_Reports.py 	Vanak
and
Miremad	Maintenances	
This script automates the process of generating, archiving, and emailing Zabbix maintenance reports.

In detail this script automates the following tasks:



Collects maintenance data from Zabbix.
Generates a summary report in Excel format.
Archives the report into a password-protected ZIP file.
Emails the report to designated recipients.
Tracks script execution metrics and reports them to Prometheus.
Deletes maintenance objects in Zabbix.
❌	✅
(.zip)	admin@abramad.com
sysops@abramad.com	✅
Every
Saturday
at
12:00	SysOps Team
69	Zabbix	Zabbix_Divergence_Detector.py 	Vanak
and
Miremad	VM Monitoring	
This Python script, named zabbix_divergence_detector, is designed to monitor virtual machines (VMs) within VMware environments and check if they are correctly monitored by Zabbix. It collects metrics related to script execution, VM monitoring status, and errors, then pushes these metrics to a Prometheus Pushgateway.


Script Logic:



VM Connection and Discovery:
Connects to multiple vCenter servers.
Retrieves a list of VMs from each vCenter.
Filters VMs based on prefixes, allowed/denied folders, and power state.
Creates dictionaries (vab_vm_dict, vra_vm_dict, me_vm_dict) to store information about VMs (name, hostname, product line, datacenter).
Zabbix Interaction:
Connects to customer Zabbix servers (defined in zabbix_url_dict).
Retrieves template information (name, host list) and status.
Divergence Detection:
Iterates through the discovered VMs.
Checks if each VM's hostname is present in Zabbix templates (either OS agent templates or URL templates).
Sets the zabbix_monitoring_divergence metric to 1 if a VM is not found or if the Zabbix status of the host is disabled.
❌	❌	❌	✅
Every
Thursday
at
8:00	SysOps Team
70	AlertManager	Alertmanager_Problem_Alerter.py 	Vanak
and
Miremad	Team Alerts	
The script's primary goal is to monitor Alertmanager instances for overdue alerts (alerts that have been active for a certain duration) and then send email notifications with detailed information about those alerts. It also tracks its own execution metrics (success/failure, total runs, errors) and pushes these to Prometheus's Pushgateway.
In summary, it is an alerting script that automates the process of checking Alertmanager instances, extracting overdue alert information, and notifying the appropriate teams via email.




Main App:

get_alerts(alertmanager_url, overdue) Function:

Fetches alerts from the specified Alertmanager URL using the requests library.
Parses the JSON response to extract alert information.
Calculates the age of each alert, then returns a dictionary to organize the alerts by team.
Main Loop:
Iterates through the alertmanager_urls dictionary.
Calls get_alerts() to retrieve alerts from each Alertmanager instance.
Processes the returned alerts:
Generates a formatted HTML table with alert details (instance, problem, severity, time, age).
Writes the alert details to a CSV file.
Creates a ZIP archive of the CSV file.
Uses send_anonymous_email() to send an email notification to the appropriate team.
Metric Updates (in finally block):
Calculates the script's execution duration and updates the duration_gauge.
Sets the script_success gauge based on whether the script ran without errors.
Updates the script_total_execs and script_total_failed_execs counters by reading existing values from files, incrementing them, and writing them back.
If an error occurred, updates the script_last_error_message gauge with error information.
Push Metrics:
Uses push_to_gateway() to send the collected Prometheus metrics to the Pushgateway, allowing them to be scraped by Prometheus.
❌	✅
(html, zip)	sysops@abramad.com
network@abramad.com
system@abramad.com
development@abramad.com
support@abramad.com
csb@abramad.com
security@abramad.com
openstack@abramad.com
datacenter@abramad.com
mlplatform@abramad.com
kubernetes@abramad.com
sds@abramad.com
epm@abramad.com
caas@abramad.com
noc@abramad.com	✅
Every Sunday and Tuesday at 9:00	All Abramad Teams
71	Zabbix and AlertManager	Abramad_Problems.py 	Vanak and Mireamd	All Abramad Alerts	
This script monitors and reports on alerts from two different systems: Zabbix and Alertmanager. It collects alert data, aggregates it by team and severity, and then exposes this information as Prometheus metrics. These metrics are then pushed to a Prometheus Pushgateway for visibility and monitoring. It also keeps track of script execution history (successes and failures) and stores that information in local files.

Alert Data Retrieval:



get_alertmanager_alerts(alertmanager_url, overdue_days): Fetches alerts from an Alertmanager API endpoint. Filters alerts based on an overdue_days parameter. Parses the JSON response and extracts relevant information (team, severity, instance, etc.). It then organizes these alerts into a dictionary grouped by team.
get_zabbix_alerts(zbx_url, zbx_username, zbx_password, overdue_days): Connects to a Zabbix API using provided credentials. Retrieves problem/alerts data from Zabbix based on overdue_days. Organizes alerts into a dictionary grouped by team.
❌	❌	❌	✅
Every 3 Hours	All Abramad Teams
72	GitOps	GitOps_Mattermost_Pull.py	Vanak	GitLab	
The script acts as an automated configuration manager for a Mattermost deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
73	GitOps	GitOps_Mattermost_Push.py	Vanak	GitLab	
This script automates the process of pushing updated Mattermost configuration files to a Git repository (GitLab). it synchronizes Mattermost configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
74	GitOps	GitOps_Nexus_Pull.py	Vanak	GitLab	
The script acts as an automated configuration manager for Nexus deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
75	GitOps	GitOps_Nexus_Push.py	Vanak	GitLab	
This script automates the process of pushing updated Nexus configuration files to a Git repository (GitLab). it synchronizes Nexus configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
76	GitOps	GitOps_Gitlab_Pull.py	Vanak	GitLab	
The script acts as an automated configuration manager for GitLab deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
77	GitOps	GitOps_Gitlab_Push.py	Vanak	GitLab	
This script automates the process of pushing updated GitLab configuration files to a Git repository (GitLab). it synchronizes GitLab configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
78	GitOps	GitOps_Dashy_Pull.py	Vanak	GitLab	
The script acts as an automated configuration manager for Dashy deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
79	GitOps	GitOps_Dashy_Push.py	Vanak	GitLab	
This script automates the process of pushing updated Dashy configuration files to a Git repository (GitLab). it synchronizes Dashy configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
80	GitOps	GitOps_ETCD_Pull.py	Vanak	GitLab	
The script acts as an automated configuration manager for ETCD deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
81	GitOps	GitOps_ETCD_Push.py	Vanak	GitLab	
This script automates the process of pushing updated ETCD configuration files to a Git repository (GitLab). it synchronizes ETCD configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
82	GitOps	GitOps_Bind_Pull.py 	Vanak	GitLab	
The script acts as an automated configuration manager for Bind deployment. It fetches the latest configuration from a GitLab repository, and then copies those configuration files to the appropriate places on the server. The script also handles logging and error reporting to help with troubleshooting.



Key Components and Functionality:



Configuration:

REPO_PATH: Defines the local directory where the Git repository will be cloned/updated.
GITLAB_URL: Specifies the URL of the GitLab repository containing the configuration files.
BRANCH: The Git branch to pull from (currently set to "main").
LOG_FILE: The path to a log file where script activity will be recorded.
Logging:

The script uses the logging module to record events, errors, and other information to the LOG_FILE. This is to troubleshoot issues.
Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
83	GitOps	GitOps_ETCD_Push.py	Vanak	GitLab	
This script automates the process of pushing updated Bind configuration files to a Git repository (GitLab). it synchronizes Bind configuration files (defined in FILES_TO_COPY) from a local directory (REPO_PATH) to a remote GitLab repository. It essentially "pushes" these configurations.





Key Steps:



Configuration: Sets up variables for the local repository path (REPO_PATH), the files to be copied (FILES_TO_COPY), GitLab URL (GITLAB_URL), branch (BRANCH), and log file (LOG_FILE).
Logging: Configures logging to record script activity and errors in a log file.
File Copying: Copies the files specified in FILES_TO_COPY into the REPO_PATH. It handles both files and directories, with options to preserve or flatten directory structures.
Git Operations:
setup_git_identity(): Sets the Git username and email for the local repository. This is important for properly attributing commits.
git_pull(): Fetches the latest changes from the remote GitLab repository into the local repository.
git_push(): Commits all changes in the local repository (with a timestamped message) and pushes them to the remote GitLab repository. It uses a GitLab token for authentication.


Note: The script relies on a GITLAB_TOKEN environment variable. Make sure this token has appropriate permissions

❌	❌	❌	❌	SysOps Team
84	Zabbix	Zabbix_Monitor_vCenter_With_VM_Tools.py	Vanak
and
Miremad	vCenter VM Monitoring	
This script automates the process of discovering a VMware virtual machine and adding it to Zabbix for monitoring. Here's a breakdown:



1. Setup and Credentials:



Decryption: Decrypts the VMware vCenter password using Fernet encryption, retrieving the key and encrypted password from environment variables (sysops-svc_enc and sysops-svc_key).
vCenter and VM Details: Defines variables for:
username: The vCenter username.
password: The decrypted vCenter password.
vcenter_addr: The address of the vCenter server.
target_vm_name: The name of the virtual machine to target.


2. VMware vCenter Interaction:



Connect to vCenter: Establishes a connection to the vCenter server using the provided credentials
Retrieve VM Information:
Retrieves the content of the vCenter inventory.
Creates a view of virtual machines.
Finds the specified virtual machine (target_vm_name). Raises an exception if the VM is not found.
Iterates through the found VMs (should be just one).
Extracts the VM's name, IP address (using the first non-loopback or link-local IP address found in the VM's network interfaces), and Instance UUID.
Stores this information in the vm_data dictionary.
Prints the gathered VM data.
Disconnect from vCenter: Closes the connection to vCenter.


3. Zabbix Interaction:



Defines Zabbix Parameters:
zabbix_url: The URL of the Zabbix server.
zabbix_user: The Zabbix username (derived from the vCenter username).
zabbix_password: The decrypted vCenter password (used for Zabbix authentication).
zabbix_templates: A list of Zabbix template names to apply to the new host (e.g., "VMware Guest").
team: Name of a team for tagging the hosts
zabbix_tags: A list of Zabbix tags to apply (e.g., "Owner", "Note").
zabbix_host_groups: A list of Zabbix host groups to add the new host to.
zabbix_node_adder Function: This function encapsulates the Zabbix-related logic.
Connects to Zabbix API: Logs in to the Zabbix API using the provided username and password.
Retrieves Template IDs: Gets the IDs of the specified Zabbix templates by name. Raises an exception if a template is not found.
Retrieves Host Group IDs: Gets the IDs of the specified Zabbix host groups by name. Raises an exception if a host group is not found.
Creates Zabbix Host: Iterates through the vm_data dictionary (containing the VM information). For each VM:
Creates a new Zabbix host with:
The VM's name as the host name and visible name.
The VM's IP address.
A description (empty in this case).
The retrieved template IDs and host group IDs.
Tags as provided
Macros for VMWARE connection including the URL, Username, Password(encrypted), and the Instance UUID.
Configures the host's interface to use the IP address and Zabbix agent port (10050).
Prints a success message with the new host ID.
Error Handling: Includes try...except blocks to handle potential errors during Zabbix API calls.






❌	❌	❌	❌	SysOps Team
85	Prometheus	Prometheus_Rule_Parser.py	Vanak
and
Miremad	Prometheus rule files	
This Python script automates the parsing of Prometheus rule files from a Git repository, generates HTML reports and Excel spreadsheets summarizing the rules, and publishes these reports to a Confluence space. It also tracks script execution metrics using Prometheus and pushes them to a Pushgateway. Here's a breakdown of what it does:



1. Initialization & Configuration:



Imports necessary libraries: os, yaml, time, openpyxl, traceback, subprocess, pathlib, html, atlassian, cryptography, urllib, datetime, and prometheus_client.
Defines configuration variables: Sets script name, file paths for storing execution counts, Pushgateway URL, job name, Prometheus instance name, and target metrics.
Sets up Prometheus metrics: Initializes a Prometheus CollectorRegistry and defines the following gauges and counters:
script_exec_duration_seconds: Tracks script execution time.
script_success: Indicates script success (1) or failure (0).
script_total_execs: Tracks the total number of script executions.
script_total_failed_execs: Tracks the total number of script failures.
script_last_error_message: Records the last error message encountered.


2. Git Repository Handling:



Clones or Pulls from Git: The script clones the repository if it doesn't exist locally, or pulls the latest changes if it does. It uses a Gitlab token provided via the GITLAB_TOKEN environment variable for authentication.
build_authenticated_git_url function: Creates an authenticated Git URL using the Gitlab token.
git_clone_or_pull function: Manages the Git clone or pull process, handling timeouts and errors.


3. Rule Parsing & Data Extraction:



Reads YAML Configuration: It reads Prometheus rule files (.yml or .yaml) from specified directories within the cloned repository. It iterates through the YAML structure to extract key information from each rule (e.g., datacenter, alert name, expression, team, severity, type, group, and file name).
Organizes Data by Team: It groups the extracted rule data by team.


4. Report Generation:



generate_html function: Generates an HTML table summarizing the Prometheus rules. Includes timestamps and a link to a Confluence macro for expansion.
Generates Excel Spreadsheet: Creates an Excel spreadsheet (.xlsx) containing the same rule data as the HTML table.
Iteration and Report Generation: The script iterates through each team and their corresponding rules, generating an HTML report and Excel file for each.


5. Confluence Publishing:



publish_page function: Publishes the generated HTML report and Excel attachment to a Confluence page. It checks if the page already exists, updating it if it does, or creating it if it doesn't.
Uses Confluence API: Connects to Confluence using credentials read from the environment and publishes the report.


6. Error Handling & Metrics Updates:



try...except...finally Block: Handles potential errors during the script's execution.
Error Logging: If an error occurs, it records the error type, message, and traceback information.
Metrics Updates in finally: Regardless of success or failure, the finally block ensures that:
The script execution duration is recorded.
The script's success status is recorded.
Counters for total executions and failed executions are updated.
The last error message is recorded (if any).
Metrics are pushed to the Pushgateway.


7. Decryption



decryptor function: Decrypts environment variables using Fernet encryption.




❌	✅
(excel) on Confluence)	❌	✅
Weekly on Thursdays at 10:00	SysOps Team
86	ECS Monitoring	ECS_InfluxDB_Exporter.py 	Vanak
and
Miremad	ECS InfluxDB	
This Python script acts as a custom Prometheus Exporter designed to bridge data from an InfluxDB instance (specifically from the monitoring_op bucket) to a Prometheus-compatible format. It is structured as a WSGI application, intended to be served via an application server like Gunicorn.

Core Functionality:
The script listens for HTTP requests on the /metrics endpoint. It expects a target parameter in the URL (e.g., /metrics?target=1.2.3.4:8086), which specifies the InfluxDB server to query.

Once triggered, it performs the following four main tasks:

Disk Latency Monitoring (fetch_latency):
Queries InfluxDB for disk I/O stats (reads, writes, read_time, write_time).
Calculates the average Read and Write latency in milliseconds.
Identifies whether disks are physical or logical (ECS-based).
Disk Usage & Inodes (fetch_disk):
Collects detailed storage metrics for various mount paths.
Exports data regarding Bytes used/free/total and Inodes used/free/total.
Automatically calculates usage percentages if not explicitly provided in the source.
CPU Performance (fetch_cpu):
Fetches the overall CPU load.
Breaks down usage into User, System, and I/O Wait categories.
Memory Analysis (fetch_memory):
Retrieves system memory stats including Total, Used, and Free bytes.
Notes:
Dynamic Querying: Uses Flux queries (InfluxDB 2.x/Cloud) to fetch the most recent data (last()) within a 5-minute range.
Multi-Tenancy: Each request creates a fresh CollectorRegistry, allowing it to serve metrics for different targets dynamically without cross-contamination of data.
Labeling: Metrics are labeled with node (hostname), influx_addr, path, and disk names, making them highly searchable in Grafana or Prometheus.
❌	❌	❌	❌	SysOps Team
87	Unity Monitoring	DellEMC_Unity_Exporter.py 	Vanak
and
Miremad	Dell EMC Unity	
This script is a small Prometheus exporter (WSGI app) that queries the Dell EMC Unity storage system’s REST API and exposes the results as Prometheus metrics.

What it does 
Reads credentials from environment variables

Requires UNITY_USERNAME and UNITY_PASSWORD.
If either is missing, the script exits immediately with an error.
Creates a reusable HTTP session

Uses requests.Session() with HTTP Basic Auth.
Sends headers required/expected by Unity’s REST API (e.g., X-EMC-REST-CLIENT: true).
On each /metrics request (with ?target=...)

Creates a fresh Prometheus CollectorRegistry (so metrics are per-request/per-target).
Calls fetch_cpu(target, registry) which:
Sends a GET request to the Unity API endpoint:

https://<target>/api/types/metricValue/instances?filter=path EQ "sp.*.cpu.summary.utilization"&per_page=1

Parses the JSON response and extracts CPU utilization values for storage processors:

spa

spb

Exposes them as a gauge:

dellemc_unity_cpu_utilization_percent{target="<target>", sp="spa|spb"}

Also exposes an “exporter target health” gauge:

dellemc_unity_up{target="<target>", problem="..."}

Sets it to 1 if the API call succeeded and returned expected data, otherwise 0 with a descriptive problem label.

Provides a /health endpoint

Returns 200 OK with body OK for basic service health checks.
:Note 
It’s meant to be run behind Gunicorn (example command at the bottom) and scraped by Prometheus using the /metrics?target=<unity-host> pattern.

✅
(.env)	❌	❌	❌	SysOps Team
88	Abramad Status Page	
Website_Availability_24H.py 

Vanak
and
Miremad	Important Websites	
This Python script is a monitoring tool that calculates the 24-hour availability of various websites/services by querying data from Grafana (Zabbix datasource) and pushing the processed results to a Prometheus Pushgateway.

Key Operations:
Data Retrieval from Grafana:
The script connects to a Grafana instance and executes queries against a Zabbix datasource.
It looks for specific “Failed step” events in web check scenarios for a list of predefined hosts (like Abramad-Website, ECS01, etc.).
It includes a retry mechanism for network or server exceptions.
Smart Availability Calculation (The “Revised” Logic):
Original Availability: Calculates a simple “Up/Down” percentage based on all raw samples.
Revised Availability (Chunking): It uses numpy to group samples into “chunks” (e.g., 3 samples per chunk). If any sample in a chunk is “Up”, the whole chunk is considered “Up”. This helps filter out transient “blips” or false positives in monitoring.
Local State Tracking:
It keeps track of how many times the script itself has run (and how many times it failed) by reading/writing to local text files in C://Temp.
Prometheus Metrics Export:
Instead of waiting for Prometheus to scrape it, this script pushes metrics to a Pushgateway (used for cron jobs/scheduled tasks).
Exported Metrics include:
Availability percentages (Original vs. Revised).
Sample counts (Total vs. Up).
Script meta-metrics: execution duration, success status, and detailed error messages.
Comprehensive Error Handling:
If something goes wrong, it captures the exact line number and traceback info.
It reports these errors as metrics (script_last_error_message), making it easy to see why a script failed directly from a Grafana dashboard.
Technical Stack:
Data Processing: numpy (for reshaping and chunk analysis).
Communication: requests (API calls to Grafana and Pushgateway).
Monitoring: prometheus_client (standard Gauges and Counters).
❌	❌	❌	✅
Daily at 23:45	SysOps Team
89	Abramad Status Page	Website_Availability_Current.py 	Vanak
and
Miremad	Important Websites	
This Python script is an advanced Prometheus Exporter designed to monitor website availability.It runs as a continuous background service with a built-in HTTP server,  robust for real-time monitoring.

1. Architecture & Execution

Dual-Operation Mode: The script uses threading to run a background Collector Loop that periodically fetches data, while simultaneously acting as a WSGI Web Server (via Gunicorn) to serve the collected metrics on the /metrics endpoint.
Thread Safety: It implements a threading.Lock to ensure that the metrics being served are not modified while a collection cycle is active.
Dynamic Configuration: It loads monitoring targets (hosts, groups, and UIDs) from a JSON configuration file (targets.json), allowing updates without changing the code.
2. Data Collection Logic
Grafana/Zabbix Integration: Every few minutes (configured by COLLECTION_INTERVAL), the script queries the Grafana API (Zabbix datasource) for “Failed step” events over the last 3 minutes.
Smart “Revised” Analysis:
It uses Numpy to group raw data into “chunks.”
It applies a “soft-fail” logic: if at least one sample in a chunk is successful, the entire chunk is considered “Up.” This reduces noise from temporary network jitters.
Status Mapping: It converts availability percentages into clear status codes:
1: Up (100% available)
0: Down (0% available)
2: Disruption (Partially available)
-1: No Data
3. Advanced Metrics Management
Stale Metrics Cleanup: The script tracks known_hosts. If a host is removed from the JSON configuration, it automatically removes that host’s metrics from the Prometheus registry to prevent “ghost” data in your dashboards.
Self-Monitoring: It exports “Meta-metrics” about the exporter itself:
last_collection_success: Whether the last API pull worked.
last_collection_duration_seconds: How long the collection took.
collection_errors_total: A counter for any internal failures.
4. Reliability Features
Persistent Session: Uses requests.Session() for better performance and connection pooling.
Retry Logic: Employs an exponential backoff retry mechanism for API calls to handle transient network errors gracefully.
✅
(.json)	❌	❌	❌	SysOps Team
90	Abramad Status Page	powerdns-exporter.py 	Vanak and Miremad	PowerDNS Primary and Secondary nodes	

This is a Python-based, Dockerized Prometheus exporter for monitoring PowerDNS health and availability. It continuously tests DNS resolution (read) and A record creation/deletion (write) against PowerDNS servers, exposes the results as Prometheus metrics, and computes 24-hour availability by querying historical data from Grafana.

How It Works 
The exporter runs four background threads, each on its own collection interval:

pdns-read-status-thread	secondary	status	Resolves a test FQDN via Miremad and Vanak DNS servers
pdns-write-status-thread	primary	status	Creates and deletes a temporary A record via the PowerDNS API
pdns-read-availability-thread	secondary	availability	Queries Grafana for 24h read-status history and computes uptime %
pdns-write-availability-thread	primary	availability	Queries Grafana for 24h write-status history and computes uptime %
Metrics are exposed over a WSGI endpoint (/metrics) served by Gunicorn.


Exposed Metrics 
App Metrics 
pdns_read_current_status	role, miremad, vanak	DNS resolution status: -1=no data, 0=both secondaries down, 1=at least one secondary dns up
pdns_write_current_status	role, datacenter	A record creation status (calculations done against primary dns): -1=no data, 0=down, 1=up
pdns_24h_availability_percent	role, func, date	Availability % over the last 24h (-1 if data unavailable)
pdns_24h_availability_samples_total	role, func, date	Total samples in the 24h window
pdns_24h_availability_samples_up	role, func, date	Number of "up" samples in the 24h window
Exporter Self-Metrics 
pdns_exporter_last_collection_success	role, mode, collection_interval, last_error	1 if the last collection succeeded, 0 otherwise
pdns_exporter_last_collection_duration_seconds	role, mode, collection_interval	Duration of the last collection in seconds
pdns_exporter_collection_errors_total	role, mode, collection_interval	Cumulative collection error count

Full Document: Monitoring PowerDNS

✅
(.env)	❌	❌	❌	SysOps Team
91	DNS Name Resolution	dns-resolver.py 	Vanak and Miremad	DNS Servers	
This script is a DNS health check probe that resolves a given hostname using specified DNS servers and returns JSON containing whether the resolution succeeded, the resolved IP, the response time, and any error encountered.

Takes two arguments [A_RECORD] and [DNS_SERVER]

It is intended for monitoring DNS availability and performance in Zabbix.

Usage:

dns-resolver.py www.google.com 1.1.1.1
On success returns:

{
  "success": true,
  "ip": "142.250.74.78",
  "response_time_ms": 12.43,
  "error": ""
}
On Failure returns:

{
  "success": false,
  "ip": "",
  "response_time_ms": 0,
  "error": "actual error message"
}


❌	❌	❌	❌	SysOps Team
92	
 	








93	
 	








