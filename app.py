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

import requests, os, urllib3, json, config_transfer, pandas as pd
from dotenv import load_dotenv
import delete_old_devices

urllib3.disable_warnings()
load_dotenv()

dnac = os.environ["DNAC_HOST"]
username = os.environ["USERNAME"]
password = os.environ["PASSWORD"]
project_name = os.environ["DNAC_PROJECT_NAME"]
onboarding_template = os.environ["DAY0_TEMPLATE"]
base_url = f"https://{dnac}/dna/intent/api/v1"
mapping_file = 'config/mapping.csv'

def csv_column_to_list(column_number):
    df = pd.read_csv(mapping_file)
    #First column in the mapping file
    row_value = df.iloc[:, column_number]
    column_values = row_value.tolist()
    return column_values  

def auth():
    headers = {
              'content-type': "application/json",
              'x-auth-token': ""
    }
    auth_url = f"https://{dnac}/api/system/v1/auth/token"
    resp = requests.post(url=auth_url, auth=requests.auth.HTTPBasicAuth(username, password), headers=headers, verify=False)
    return resp.json()["Token"]


#Uses the gathered existing serial ids to get information about the existing switches
def get_devices(token, serials):
    devices = []
    headers = {
              'content-type': "application/json",
              'x-auth-token': token
    }
    for serial in serials: 
        url = base_url + f"/network-device?serialNumber={serial}"
        device = requests.get(url=url, headers=headers, verify=False)
        device = device.json()["response"]
        devices.extend(device)
    return devices

#Based on the gather device info we now use the device id's to grab the 
# existing config and put into a list of configs
def get_existing_config(token, devices): 
    all_configs = {}
    headers = {
        'content-type': "application/json",
        'x-auth-token': token
    }

    for device in devices:
        device_id = device['id']
        url = base_url + f"/network-device/{device_id}/config"
        resp = requests.get(url=url, headers=headers, verify=False)
        resp = resp.json()["response"]
        config = config_transfer.template_text_to_list(resp)
        all_configs.update({device_id:config})

    return all_configs

#Will get information about the specified onboarding template, contains the template itself
def get_template_details(token, onboarding_template):
    headers = {
        'content-type': "application/json",
        'x-auth-token': token
    }

    url = f"https://{dnac}/dna/intent/api/v2/template-programmer/template?name={onboarding_template}"
    resp = requests.request('GET', url=url, headers=headers, verify=False)
    resp = resp.json()['response'][0]
    return resp

#Require site ids for pnp claiming
def get_site_id(site_name): 
    headers = {
                'content-type': "application/json",
                'x-auth-token': token
        }
    url = base_url + f"/site?name={site_name}"
    resp = requests.get(url=url, headers=headers, verify=False)
    return resp.json()['response'][0]['id']

#Imports devices to DNAC via pnp, to note there are many more fields that can be added if required
def import_device_to_pnp(pnp_import_info):
    
    payload = []
    headers = {
                'content-type': "application/json",
                'x-auth-token': token
        }
    
    for device in pnp_import_info:

        print(device["serialNumber"])

        formatted_item = {
            "deviceInfo": {
                "hostname": device["name"],
                "serialNumber": device["serialNumber"],
                "pid": device["pid"],
                "sudiRequired": False,
                "userSudiSerialNos": [],
                "aaaCredentials": {
                    "username": "",
                    "password": ""
                }
            }
        }
        payload.append(formatted_item)

    headers = {
                'content-type': "application/json",
                'x-auth-token': token
        }
    url = base_url + "/onboarding/pnp-device/import"
    resp = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)
    return resp.json()


def get_image_ids(token, image_names):

    image_ids = []
    for image_name in image_names:
        
        if type(image_name) == str:
            url = f"{base_url}/image/importation?imageName={image_name}"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                'x-auth-token': token
            }

            response = requests.request('GET', url, headers=headers, data = None, verify=False)
            
            #Response should only return one element since we filtered based on the image name
            response = response.json()
            image_uuid = response['response'][0]['imageUuid']

            image_ids.append(image_uuid)
        else:   
            image_ids.append(None)

    return image_ids


#Function to claim devices use finalised pnp info, filled template variables, along with the associated template id
def claim_device_to_site(pnp_info, config_params, template_id, image_ids):
    headers = {
                'content-type': "application/json",
                'x-auth-token': token
        }
    claim_all_devices = []
    claim_results = []

    for device, device_config, image_id in zip(pnp_info, config_params, image_ids):
        
        #update old device name to new
        device_config['HOSTNAME'] = device['HOSTNAME']
        site_name = device['site_name']
        device_id = device['device_id']
        site_id = get_site_id(site_name)


        claim_info = {
            "siteId": site_id,
            "deviceId": device_id,
            "type": "Default",
            "configInfo": {
                "configId": template_id,
                "configParameters": [
                    {"key": key, "value": value} for key, value in device_config.items()
                ]
            }
        }

        if image_id != None:
            claim_info.update({"imageInfo": {"imageId": image_id, "skip": False}})

        claim_all_devices.append(claim_info)
        url = base_url + "/onboarding/pnp-device/site-claim"
        resp = requests.post(url=url, headers=headers, json=claim_info, verify=False)
        claim_results.append(resp.json())

    print(claim_results)
    return claim_results


if __name__ == "__main__":
    token = auth()

    print("Read existing switch serial from mapping file.")
    existing_serials = csv_column_to_list(0)
    print(existing_serials)

    print("Request switch details of existing switches via API e.g. Device ID.")
    existing_devices = get_devices(token, existing_serials)

    print("Request config of existing switches via API.")
    all_configs = get_existing_config(token, existing_devices)
    
    print("Request template details via API.")
    template = get_template_details(token, onboarding_template)
    template_list = config_transfer.template_text_to_list(template['templateContent'])
    
    print("Extracting of old configuration values.")
    config_params = config_transfer.get_variables_from_config(all_configs, template_list)
    pnp_info = config_transfer.format_list_for_pnp(config_params, onboarding_template)
    
    print("Read preferred switch image for new switches.")
    image_names = csv_column_to_list(4)
    image_ids = get_image_ids(token, image_names)

    print("Delete old switches.")
    delete_old_devices.delete_old_switch(token, existing_devices)

    print("Importing new switches to PNP:")
    import_info = import_device_to_pnp(pnp_info)
    pnp_info = config_transfer.extract_new_device_ids(pnp_info, import_info)
    config_transfer.export_to_output_csv(pnp_info)

    print("Claim new switches with associate template, old configuration values and optionally image version.")
    claim_device_to_site(pnp_info, config_params, template['id'], image_ids)


    
