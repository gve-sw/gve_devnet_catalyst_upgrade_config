""" Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

import re, csv, copy

#Function to convert onboarding template to a list ready for analysis
def template_text_to_list(template_text):
    template_list = []
    for line in template_text.splitlines():
        template_list.append(line)
    return template_list

#Extracts jinja lines from the template, produces dictionary of keys representing unique template variables
def get_variables_from_template(template):
    template_var_lines = []
    var_values_dict = {}

    for line in template:
        if "{{" in line and "}}" in line:
            template_var_lines.append(line)

    for line in template_var_lines:
        #This pattern is searching for "{{ }}" which denotes a template variable in jinja
        matches = re.findall(r'\{\{\s*(\w+)\s*\}\}', line)
        for match in matches:
            var_values_dict[match] = None

    return var_values_dict


'''Extract old switch config (and translate interface names according to new syntax)'''
def extract_old_interface_config(config):

    interface_config = []

    for i, line in enumerate(config):

        match_gig = re.search(r'([1]\/[0]\/([2-9]|(1[0-9])|(2[0-9])|(3[0-9])|(4[0-8])))$', line)
        match_ten = re.search(r'([1]\/[1]\/(3|4))$', line)

        if (line.startswith('interface Ten') and match_ten) or (line.startswith('interface Gi') and match_gig) or line.startswith('interface Port-channel1') or line.startswith('vlan') or line.startswith('interface Vlan'):
            
            interface_config.append(line)
            #OR (in case of translations)
            #translated_line = translate_interface_syntax(config[i])
            #interface_config.append(translated_line)
            
            #Copy all lines until ! or lldp run 
            while (config[i+1] != "!" and config[i+1] != "lldp run"):
                interface_config.append(config[i+1])
                i = i+1
            
            #Skip duplicate !
            while config[i+1] == "!":
                i = i+1 
            interface_config.append("!")


    return interface_config


'''Translate interface names according to new syntax
GigabitEthernet1/0/37- GigabitEthernet1/0/48 to TenGigabitEthernet1/0/x
GigabitEthernet1/1/1 - GigabitEthernet1/1/2 To TenGigabitEthernet1/1/x
not needed with test switch but for real switch in PoC
'''
def translate_interface_syntax(line):
    
    match = re.search(r'[1]\/[1]\/[1-2]$', line) or re.search(r'[1]\/[0]\/((3[7-9])|(4[0-8]))$', line)

    if match and line.startswith('interface Gig'):
        line = line.replace("GigabitEthernet", "TenGigabitEthernet")

    return line


'''Extraction function to get corresponding values from each existing switch config, then
   populates dictionary of templates variables, ready to be used as part of the PnP onboarding process'''
def get_variables_from_config(all_configs, template):
    
    config_params = []
    var_values_dict = get_variables_from_template(template)
    
    '''This dictionary is a last resort in case the existing config that will be
       used to fill the template does not have a value to extract. Please update if
       useful. The code will not take on these default values if it is None.'''
    
    default_values = {'HOSTNAME': None, 'MGMT_VLAN_ID': None, 'MGMT_SUBNET': None, 'MGMT_SUBNET_MASK_CIDR': None,
                             'DEFAULT_GATEWAY': None, 'CITY': None, 'STREET': None, 'ROOM': None, 'RACK': None, 
                             'INTERFACE_CONFIG': []}

    for config in all_configs.values():

        try: 

            var_values_dict["INTERFACE_CONFIG"] = extract_old_interface_config(config)

            for line in config:

                #Searches config for a line that contains hostname at the start then assumes the actual hostname follows in the second portion
                #Sample input: hostname my_oldswitch
                #Method: Use .split and take the second item

                if line.startswith('hostname'):
                    var_values_dict['HOSTNAME'] = line.split()[1]

                #Searches config for a line that contains either of theses strings then gets out MGMT_VLAN_ID via regex
                #Sample input: description VLANxx;x;xx;xx;xxxxx;xxxxxx;Management Interface
                #Method: Use r'vlan(\d+)' which looks for 'vlan' followed by one or more digits, match.group(1) gets the Id (14)

                if "Management Interface" in line or "source-interface" in line:
                    match = re.search(r'vlan(\d+)', line, re.IGNORECASE)
                    if match:
                        var_values_dict['MGMT_VLAN_ID'] = match.group(1)
                
                #Searches config for a line that contains "Sw_Mgmt", extracts the subnet and mask via regex
                #Sample input: name x-xx_Sw_Mgmt_xx.xxx.xxx.x/xx
                #Method: The regex below has two matching groups named subnet and mask, after each one
                #  there's a regex pattern, the first pattern matches the subnet, the second finds the mask

                if "Sw_Mgmt" in line: 
                    match = re.search(r"(?P<subnet>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(?P<mask>\d{1,2})", line)
                    if match:
                        var_values_dict['MGMT_SUBNET'] = match.group('subnet')
                        var_values_dict['MGMT_SUBNET_MASK_CIDR'] = '/' + match.group('mask')
                
                #Searches for "ip address", ignores lines with "no" - won't contain an ip address, uses regex to get info 
                #Sample input: ip address xx.xxx.xxx.xx xxx.xxx.xxx.0
                #Method: The regex below is similar to previous, but has groups ip and subnet

                if "ip address" in line and "no" not in line:
                    match = re.search(r"ip address (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (?P<subnet>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                    if match:
                        var_values_dict['MGMT_SUBNET'] = match.group('subnet')
                
                #Simple .split used, sample input would be ip default-gateway xx.xxx.xxx.x
                if "default-gateway" in line:
                    var_values_dict['DEFAULT_GATEWAY'] = line.split()[2]
                
                #Looks for this string, uses regex to extract info
                #Sample input: snmp-server location xxxxx,xxxxxxx x-x,xxx.xx.xxx, xxxx xxx.xx.xx, xx xx + xx
                #Method: the regex pattern ([^,]+) will look for a sequence of characters until it reaches a comma,
                #   repeats to get required info, .strip() will remove any leading whitespaces

                if "snmp-server location" in line:
                    match = re.match(r"snmp-server location ([^,]+),([^,]+),([^,]+),([^,]+)", line)
                    if match:
                        city, street, room, rack = match.groups()
                        var_values_dict["CITY"] = city.strip()
                        var_values_dict["STREET"] = street.strip()
                        var_values_dict["ROOM"] = room.strip()
                        var_values_dict["RACK"] = rack.strip()
            
        except Exception as e: 
            print(e)

        #Checks if any keys still don't have a value, if so will use the default values provided earlier
        for key in var_values_dict:
            if var_values_dict[key] is None:
                var_values_dict[key] = default_values.get(key, None)
        
        #Append each device config info to this list
        config_params.append(var_values_dict)
    return config_params

'''Uses the config_parameters (populated dictionaries of template variables for all devices)
   along with the name of the template which will be the define onboarding template as defined
   in your .env file, to merge the mapping csv data to the config_params list for pnp onboarding,
   fields like serial number and site_name is required for PnP, we merge it here.'''
def format_list_for_pnp(config_params, template_name):
    mapping_file = 'config/mapping.csv'
    pnp_info = copy.deepcopy(config_params)

    with open(mapping_file, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)

        for i, (row, device) in enumerate(zip(csv_reader, pnp_info)):
            old_hostname = device['HOSTNAME']

            device_info = {
                'serialNumber': row['new_switch_serial_Cat9k'],
                'name': old_hostname,
                'pid': row['pid'],
                'site_name': row['site_name'],
                'template_name': template_name
            }
            device['HOSTNAME'] = device_info['name']
            device_info.update(device)
            pnp_info[i] = device_info
        return pnp_info

'''This function is used post PnP switch import, the response from executing pnp import
   is used here to obtain the device Id's, the device Id's will be added to the PnP data
   to be used when claiming the switches'''
def extract_new_device_ids(pnp_info, import_info):
    try:
        for import_info, device in zip(import_info['successList'], pnp_info):
            device_id = import_info['id']

            # Insert the device_id after the serialNumber in the dictionary
            update_device = {}
            for k, v in device.items():
                update_device[k] = v
                if k == "serialNumber":
                    update_device["device_id"] = device_id

            # Replace the original dictionary with the updated one
            device.clear()
            device.update(update_device)
            
    except Exception as e:
        print(e)

    return pnp_info

#Exporting the finalised PnP data before claiming the newly imported switches'''
def export_to_output_csv(pnp_info):
    onboarding_file = 'config/onboarding.csv' 
    headers = list(pnp_info[0].keys())

    with open(onboarding_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=headers)
        csv_writer.writeheader()

    with open(onboarding_file, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=headers)
        csv_writer.writerows(pnp_info)  
