# gve_devnet_catalyst_upgrade_config
This example script has been designed for a client who wants to upgrade from their current Catalyst 3k series switches to the new Catalyst 9k series switches. It works by utilizing the configurations from the existing 3k series switches.

The script performs value extraction on the existing configuration and populates a configuration template accordingly. It also transfers the existing interface configuration and makes any necessary adjustments to adapt to the upgraded Catalyst 9k series switches.

## Contacts
* Jordan Coaten

## Solution Components
* Python
* Pandas
* Catalyst 3650 & 9300 Switches
* DNA Center
* DNA Center REST API's

# Workflow of PoV
![Overview of PoV](/IMAGES/flow_diagram.png)


# High Level Design

![High level design of PoV](/IMAGES/high_level_design.png)


## Prerequisites

1. Create an onboarding template for the switches to be deployed, ensure Jinja is being used. Please see "template_example" within the repository files, also this ([resource](https://github.com/kebaldwi/DNAC-TEMPLATES/tree/master/LABS/LAB-B-Onboarding-Template)) may help. 
2. Add onboarding template to a network profile ([Instructions](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/dna-center/2-3-3/user_guide/b_cisco_dna_center_ug_2_3_3/m_configure-network-profiles.html#task_hvy_wwb_wfb))   
3. Add the template to the associated onboarding project, the default should be named "onboarding project", do this via UI ([Instructions](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/dna-center/2-1-2/user_guide/b_cisco_dna_center_ug_2_1_2/b_cisco_dna_center_ug_2_1_1_chapter_01000.html))
4. Populate the provided mapping file with the target switches

   ![/IMAGES/mapping_file.jpeg](/IMAGES/mapping_file.png)

   * In the example mapping file provided above, there are five fields:
      * **old_switch_serial**: Enter the serial number of the existing switch in your DNA Centre environment. The serial number is a unique identifier for the switch.
      * **new_switch_serial_Cat9k**: Provide the serial number of the new switch to be deployed, just like the previous field.
      * **pid**: Input the platform ID for the new switch that will be provisioned.
      * **site_name**: Specify the target site where the switch will be deployed, ensuring it matches the location of the existing switch being replaced.
      * **image_version**: This optional field allows you to define a specific image from your DNA Centre environment for upgrading the image, this will be the **file name** of the image. If left blank, the new switch will use the same image as the existing one. 

## Installation/Configuration
1. Make sure Python 3 and Git is installed in your environment, and if not, you may download Python [here](https://www.python.org/downloads/) and Git [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git).


2.	(Optional) Create and activate a virtual environment - once Python 3 is installed in your environment, you can activate the virtual environment with the instructions found [here](https://docs.python.org/3/tutorial/venv.html).  
    ```
    #MacOS and Linux: 
    python3 -m venv [add name of virtual environment here] 
    source [add name of virtual environment here]/bin/activate
    
    #Windows: 
    python -m venv [add name of virtual environment here] 
    [add name of virtual environment here]/Scripts/activate
    ```
    
  * Access the created virtual environment folder
    ```
    cd [add name of virtual environment here] 
    ```

3. Clone this Github repository:  
    ```
    git clone [add github link here]
    ```
        
  * For Github link: 
      In Github, click on the **Clone or download** button in the upper part of the page > click the **copy icon**  
      ![/IMAGES/giturl.png](/IMAGES/giturl.png)
  * Or simply download the repository as zip file using 'Download ZIP' button and extract it


4. Access the downloaded folder:  
   ```
   cd gve_devnet_catalyst_upgrade_config
   ```
  

5. Install all dependencies:  
   ```
   pip install -r requirements.txt
   ```
 

6. Open the `.env` file and fill out the following environment variables: 
   ```
    DNAC_HOST= <ENTER YOUR DNAC HOST IP>
    USERNAME= <ENTER DNAC USERNAME>
    PASSWORD= <ENTER DNAC PASSWORD>
    DNAC_PROJECT_NAME= <ENTER NAME OF PROJECT> 
    DAY0_TEMPLATE= <ENTER NAME OF TARGET ONBOARDING TEMPLATE>
   ```

## Usage

7. Run the script:   
   ```
   python3 dnac_app.py
   ```

## Limitations 

Limitations of this script: 
   - The script uses Jinja variables, however with some code changes can easily be used with Velocity. 
   - The script is using regex patterns to extraction information from a specific configuration logic, this will have to be adapted to fit your configuration. 
   - The script has not been testing for a wide variety of Catalyst switching models. 
   - Designed for switches with 48 ports. 
   - The script does not check if both the old and newly deployed switches are already available in PnP/DNA Center, please ensure this is checked before populating the mapping file.

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
