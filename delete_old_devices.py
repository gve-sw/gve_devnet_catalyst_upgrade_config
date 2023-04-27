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

import app
import requests
import time

'''
Request Details for Task
'''
def getTask(token, task_id):
    
    url = f"{app.base_url}/task/{task_id}"
    
    headers = {
        "x-auth-token": token,
        "Content-Type": "application/json",
        }

    task = requests.get(url, headers=headers, verify=False).json()

    task_status = task['response']['progress']
    task_error = task['response']['isError']

    print(f"Task Status: {task_status}, Task Error: {task_error}")

    return task_status, task_error 

'''
Delete old device from the inventory, without changing the config on the switch
'''
def delete_device(id, token):
    
    url = f"{app.base_url}/network-device/{id}?cleanConfig=false"

    payload = None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        'x-auth-token': token
    }

    response = requests.request('DELETE', url, headers=headers, data = payload, verify=False)

    return(response.json())

'''
Delete all old switches from the inventory
'''
def delete_old_switch(token, existing_devices):
    
    for device in existing_devices:
        
        print(f"Deleting old device: {device['serialNumber']}")
        
        response = delete_device(device['id'], token)
        task_id = response["response"]["taskId"]
        
        task_status, task_error  = getTask(token, task_id)

        while task_status.startswith('Deleting device') and not task_error:
            time.sleep(10)
            task_status, task_error = getTask(token, task_id)



   

