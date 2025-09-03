
# ******************************************************************************
# * @attention
# *
# * Copyright (c) 2022 STMicroelectronics.
# * All rights reserved.
# *
# * This software is licensed under terms that can be found in the LICENSE file
# * in the root directory of this software component.
# * If no LICENSE file comes with this software, it is provided AS-IS.
# *
# *
# ******************************************************************************
#

import os
import sys
import json
from enum import Enum
from datetime import datetime
from stdatalog_pnpl.DTDL import device_template_model as DTM
import requests

class ComponentType(Enum):
    SENSOR = 0
    ALGORITHM = 1
    OTHER = 2
    ACTUATOR = 3
    NONE = -1

BOARD_MAP = {
    10: "STEVAL-STWINKT1",
    14: "STEVAL-STWINBX1",
    18: "STEVAL-STWINBX1B",
    13: "STEVAL-MKBOXPRO",
    17: "STEVAL-MKBOXPROB",
    9: "STEVAL-STWINKT1B",
    1: "STEVAL-MKSBOX1V1",
    2: "STEVAL-PROTEUS1",
    32: "B-U585I-IOT02A",
    48: "NUCLEO-H7A3ZI-Q",
    16: "NUCLEO-U575ZI-Q",
    127: "NUCLEO-STM32F401RE",
    126: "NUCLEO-STM32L476RG",
}

DEV_FLAG = True  # Set to True for development/testing, False for production

if DEV_FLAG:
    # Development URL to be used for RC testing purposes
    DEFAULT_URL = "https://raw.githubusercontent.com/SW-Platforms/appconfig/refs/heads/fwdb-automation/usb/catalog.json"
else:
    # Production URL to be used for final release
    DEFAULT_URL = "https://raw.githubusercontent.com/STMicroelectronics/appconfig/refs/heads/release/usb/catalog.json"

LOCAL_DEVICE_CATALOG_PATH = os.path.join(os.path.dirname(sys.modules[__name__].__file__), "usb_device_catalog.json")

def generate_datetime_string():
    now = datetime.now()
    datetime_string = now.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    return datetime_string

def print_error(text):
    print("\033[31m{}\033[0m".format(text))

def print_warning(text):
    print("\033[33m{}\033[0m".format(text))

class DeviceCatalogEntry:
    def __init__(self, board_id, fw_id, protocol, board_name, fw_name, fw_version, dtmi, fw_bin_url, boudrate=None):

        self.board_id = board_id
        self.fw_id = fw_id
        self.protocol = protocol
        self.board_name = board_name
        self.fw_name = fw_name
        self.fw_version = fw_version
        self.dtmi = dtmi
        if self.dtmi:
            self.dtmi_local_path = DeviceCatalogManager.get_path_from_dtmi(dtmi)
            self.dtmi_url = DeviceCatalogManager.get_url_from_dtmi(dtmi)
        else:
            self.dtmi_local_path = None
            self.dtmi_url = None
        self.fw_bin_url = fw_bin_url

        self.boudrate = boudrate

    def __repr__(self):
        return f"DeviceCatalogEntry(board_id={self.board_id}, fw_id={self.fw_id}, protocol={self.protocol}, board_name={self.board_name}, fw_name={self.fw_name}, fw_version={self.fw_version}, dtmi={self.dtmi}, dtmi_path={self.dtmi_local_path}, dtmi_url={self.dtmi_url}, fw_bin_url={self.fw_bin_url})"

class DeviceCatalogManager:
    _instance = None  # Static variable to hold the singleton instance

    @staticmethod
    def get_instance():
        """
        Static method to get the singleton instance of DeviceCatalogManager.
        If the instance does not exist, it initializes it.
        """
        if DeviceCatalogManager._instance is None:
            DeviceCatalogManager._instance = DeviceCatalogManager._initialize()
        return DeviceCatalogManager._instance

    @staticmethod
    def _initialize():
        """
        Private static method to initialize the DeviceCatalogManager.
        """
        instance = DeviceCatalogManager.__new__(DeviceCatalogManager)  # Create a new instance
        instance.catalog_dict = {}
        instance.catalog_info = {}
        instance.new_catalog_flag = False

        instance.catalog_entries = []
        instance.dev_mode = DEV_FLAG  # Set the development mode flag

        # Load the catalog
        with open(LOCAL_DEVICE_CATALOG_PATH, "r") as catalog:
            catalog_dict = json.load(catalog)
            if "usb" in catalog_dict:
                instance.catalog_dict = catalog_dict.get("usb")
                instance.new_catalog_flag = True
            else:
                instance.catalog_dict = catalog_dict
            instance.catalog_info = {"date": catalog_dict.get("date","1970-01-01T00:00:00.000000"), "version": catalog_dict.get("version","0.0.0"), "checksum": catalog_dict.get("checksum","00000000000000000000000000000000")}
            instance.catalog_entries = [
                DeviceCatalogEntry(
                    board_id=int(entry.get("board_id"), 16) if entry.get('board_id') not in ('', None) and isinstance(entry.get("board_id"), str) else entry.get("board_id"),
                    fw_id=int(entry.get("usb_fw_id"), 16) if entry.get('usb_fw_id') not in ('', None) and isinstance(entry.get("usb_fw_id"), str) else entry.get("usb_fw_id"),
                    protocol=entry.get("protocol"),
                    board_name=entry.get("brd_name", BOARD_MAP.get(entry.get("board_id"), 16) if entry.get('board_id') not in ('', None) and isinstance(entry.get("board_id"), str) else entry.get("board_id")),
                    fw_name=entry.get("fw_name", "no_name"),
                    fw_version=entry.get("fw_version", "no_version"),
                    dtmi=entry.get("dtmi", ""),
                    fw_bin_url=entry.get("dwn_url", ""),
                    boudrate=entry.get("baudrate", None)
                )
                for entry in instance.catalog_dict
            ]
        return instance

    @staticmethod
    def is_dev_mode():
        """
        Returns the development mode flag.
        """
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        return instance.dev_mode

    @staticmethod
    def get_board_names_list():
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_entries attribute
        catalog_entries = instance.catalog_entries

        # Extract unique board names from catalog_entries
        unique_board_names = {entry.board_name for entry in catalog_entries}
        return unique_board_names
    
    @staticmethod
    def get_boards_list():
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_entries attribute
        catalog_entries = instance.catalog_entries

        board_list = {
            entry.board_id: {
                "board_id": entry.board_id,
                "board_name": entry.board_name
            }
            for entry in catalog_entries
        }
        return list(board_list.values())

    @staticmethod
    def get_firmwares_list(board_identifier):
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_entries attribute
        catalog_entries = instance.catalog_entries
        if isinstance(board_identifier, str):
            # Handle the case where the identifier is a board name
            firmware_list = [
                {"fw_id": entry.fw_id, "fw_name": entry.fw_name, "fw_version": entry.fw_version}
                for entry in catalog_entries
                if entry.board_name == board_identifier
            ]
        elif isinstance(board_identifier, int):
            # Handle the case where the identifier is a board ID
            firmware_list = [
                {"fw_id": entry.fw_id, "fw_name": entry.fw_name, "fw_version": entry.fw_version}
                for entry in catalog_entries
                if entry.board_id == board_identifier
            ]
        else:
            raise TypeError("board_identifier must be either a string (board name) or an integer (board ID)")
        return firmware_list

    @staticmethod
    def get_device_model(board_id, fw_id):
        """
        Searches the catalog for an entry matching the given board_id and fw_id,
        and returns the corresponding dtmi.

        Args:
            board_id (int): The board ID to search for.
            fw_id (int): The firmware ID to search for.

        Returns:
            str: The dtmi if found, otherwise None.
        """
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        catalog_entries = instance.catalog_entries
        for entry in catalog_entries:
            if entry.board_id == board_id and entry.fw_id == fw_id:
                dtdl_json_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), entry.dtmi_local_path)
                if not os.path.exists(dtdl_json_path):
                    # If the file does not exist, download it from the URL and return the content
                    DeviceCatalogManager.download_dtdl_model_from_url(entry.dtmi_url, dtdl_json_path)
                with open(dtdl_json_path, "r") as device_model:
                    return json.load(device_model)
        return None
    
    @staticmethod
    def get_catalog_entry(board_id, fw_id) -> DeviceCatalogEntry:
        """
        Searches the catalog for an entry matching the given board_id and fw_id,
        and returns the corresponding DeviceCatalogEntry.

        Args:
            board_id (int): The board ID to search for.
            fw_id (int): The firmware ID to search for.

        Returns:
            DeviceCatalogEntry: The matching entry if found, otherwise None.
        """
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_entries attribute
        catalog_entries = instance.catalog_entries
        for entry in catalog_entries:
            if entry.board_id == board_id and entry.fw_id == fw_id:
                return entry
        return None
    
    @staticmethod
    def compare_catalogs(local_catalog_dict, online_catalog_usb):
        """
        Compares the local catalog dictionary with the online catalog's USB data.

        Args:
            local_catalog_dict (list): The local catalog dictionary (list of entries).
            online_catalog_usb (list): The online catalog's USB data (list of entries).

        Returns:
            dict: A dictionary containing added, removed, and modified entries.
        """
        added = []
        removed = []
        modified = []

        # Convert entries to dictionaries indexed by a unique key (e.g., board_id + fw_id)
        def create_key(entry):
            return f"{entry.get('board_id', '')}_{entry.get('usb_fw_id', '')}"

        local_dict = {create_key(entry): entry for entry in local_catalog_dict}
        online_dict = {create_key(entry): entry for entry in online_catalog_usb}

        # Check for added and modified entries
        for key, online_entry in online_dict.items():
            if key not in local_dict:
                added.append(online_entry)
            elif local_dict[key] != online_entry:
                modified.append({"local": local_dict[key], "online": online_entry})

        # Check for removed entries
        for key, local_entry in local_dict.items():
            if key not in online_dict:
                removed.append(local_entry)

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
        }

    @staticmethod
    def update_catalog( url = DEFAULT_URL):
        """
        Updates the catalog by fetching the latest version from the given URL.
        If the fetch is successful, it updates the local catalog file.
            
        Parameters:
        - url: The URL to fetch the latest catalog from. Defaults to DEFAULT_URL.
        """
        
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        local_catalog_dict = instance.catalog_dict
        # Access the catalog_info attribute
        local_catalog_info = instance.catalog_info

        try:
            response = requests.get(url, timeout=10)
        
            catalog_data = response.json()
            date = catalog_data.get("date")
            version = catalog_data.get("version")
            checksum = catalog_data.get("checksum")
            online_catalog_info = {"date": date, "version": version, "checksum": checksum}
            local_date = datetime.strptime(local_catalog_info["date"], "%Y-%m-%d %H:%M:%S.%f")
            online_date = datetime.strptime(online_catalog_info["date"], "%Y-%m-%d %H:%M:%S.%f")
            if online_date > local_date:
                print_warning(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - WARNING - Online catalog date is more recent than local catalog date.")
                print_warning(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - WARNING - The local catalog will be updated with the online catalog data.")
                print_warning(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - WARNING - The old local catalog json file will be renamed to usb_device_catalog_old.json.")
                
                differences = DeviceCatalogManager.compare_catalogs(local_catalog_dict, catalog_data["usb"])
                print("Added entries:", differences["added"])
                print("Removed entries:", differences["removed"])
                print("Modified entries:", differences["modified"])

                if len(differences["added"]) > 0:
                    # Print the "dtmi" field for added entries
                    for entry in differences["added"]:
                        if "dtmi" in entry and entry["dtmi"]:
                            print(f"Added DTMI: {entry['dtmi']}")
                            # print(f"URL: {DeviceCatalogManager.get_url_from_dtmi(entry['dtmi'])}")
                            DeviceCatalogManager.download_dtdl_model_from_url(DeviceCatalogManager.get_url_from_dtmi(entry["dtmi"]), os.path.join(os.path.dirname(sys.modules[__name__].__file__), DeviceCatalogManager.get_path_from_dtmi(entry["dtmi"])))

                if len(differences["removed"]) > 0:
                    # Print the "dtmi" field for removed entries
                    for entry in differences["removed"]:
                        if "dtmi" in entry and entry["dtmi"]:
                            print(f"Removed DTMI: {entry['dtmi']}")
                            # print(f"URL: {DeviceCatalogManager.get_url_from_dtmi(entry['dtmi'])}")
                            DeviceCatalogManager.remove_dtdl_model_from_local_catalog(entry["board_id"], entry["usb_fw_id"])

                if len(differences["modified"]) > 0:
                    # Print the "dtmi" field for modified entries
                    for entry in differences["modified"]:
                        if "dtmi" in entry["online"] and entry["online"]["dtmi"]:
                            print(f"Modified DTMI: {entry['online']['dtmi']}")
                            # print(f"URL: {DeviceCatalogManager.get_url_from_dtmi(entry['online']['dtmi'])}")
                            DeviceCatalogManager.download_dtdl_model_from_url(DeviceCatalogManager.get_url_from_dtmi(entry["online"]["dtmi"]), os.path.join(os.path.dirname(sys.modules[__name__].__file__), DeviceCatalogManager.get_path_from_dtmi(entry["online"]["dtmi"])))
                
                usb_device_catalog_bkp_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), "usb_device_catalog_bkp.json")

                # Check if a backup file already exists and remove it
                if os.path.exists(usb_device_catalog_bkp_path):
                    os.remove(usb_device_catalog_bkp_path)  # Remove the existing backup file

                # Rename the current catalog file to a backup file
                os.rename(LOCAL_DEVICE_CATALOG_PATH, usb_device_catalog_bkp_path)

                # Retrieve the custom dtmi entries added by the user from the local catalog
                custom_dtmi_entries = [entry for entry in local_catalog_dict if "custom_dtmi" in entry and entry["custom_dtmi"]]

                # Update the local catalog with the online catalog data (maintaining the custom dtmi entries)
                with open(LOCAL_DEVICE_CATALOG_PATH, "w") as catalog:
                    # Add the custom dtmi entries to the online catalog data                        
                    catalog_data["usb"].extend(custom_dtmi_entries)
                    # Save the updated catalog data to the local catalog file
                    json.dump(catalog_data, catalog, indent=4)
                
                # Update the catalog_dict and catalog_info attributes of the instance
                DeviceCatalogManager._instance = DeviceCatalogManager._initialize()

                print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Local catalog updated with online catalog data.")
            else:
                print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Online catalog data matches local catalog data.")
            print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Date: {date}, Version: {version}, Checksum: {checksum}")
        except json.JSONDecodeError:
            print_error(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - ERROR - Invalid JSON response from URL: {url}")
        except requests.exceptions.RequestException as e:
            print_warning(f"Network error while trying to fetch the catalog from {url}")
            print_warning(f"Impossible to update the catalog. Local catalog will be used instead.")
    
    @staticmethod
    def download_dtdl_model_from_url(url, save_path):
        """
        Downloads a DTDL model from the given URL and saves it to the specified path.

        Args:
            url (str): The URL to download the DTDL model from.
            save_path (str): The path to save the downloaded DTDL model.

        Returns:
            bool: True if the download was successful, False otherwise.
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Parse the JSON content
                json_content = response.json()
                # Ensure the directory exists before saving the JSON content to a file
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'w') as json_file:
                    json.dump(json_content, json_file, indent=4)
                print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Downloaded DTDL model from {url} and saved to {save_path}.")
                return True
            else:
                print_error(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - ERROR - Failed to download DTDL model from {url}. Status code: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - ERROR - Exception occurred while downloading DTDL model: {e}")
            return False
        
    @staticmethod
    def remove_dtdl_model_from_local_catalog(board_id, fw_id):
        """
        Removes the DTDL model from the local catalog for the specified board_id and fw_id.

        Parameters:
        - board_id: The board ID as an integer.
        - fw_id: The firmware ID as an integer.
        """
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        catalog_dict = instance.catalog_dict

        # for each entry in the catalog_dict, check if the board_id and fw_id match
        # and remove the catalog entry and device model json file if it exists 
        for entry in catalog_dict: 
            if entry["board_id"] == board_id and entry.get("fw_id",entry.get("usb_fw_id")) == fw_id:
                target_file_path = os.path.join(os.path.dirname(LOCAL_DEVICE_CATALOG_PATH), DeviceCatalogManager.get_path_from_dtmi(entry["dtmi"]))
                if os.path.exists(target_file_path):
                    os.remove(target_file_path)
                catalog_dict.remove(entry)
        
        # Save the updated catalog_dict back to the catalog file
        with open(LOCAL_DEVICE_CATALOG_PATH, "w") as catalog:
            catalog_json = {"usb": catalog_dict , "date": instance.catalog_info["date"], "version": instance.catalog_info["version"], "checksum": instance.catalog_info["checksum"]} 
            json.dump(catalog_json, catalog, indent=4)
    
    @staticmethod
    def get_path_from_dtmi(dtmi_string):
        """
        Creates a path from the given DTMI string by replacing ':' with the appropriate path separator,
        replacing the last ';' with a '-', and adding a '.json' postfix.

        Parameters:
        - dtmi_string: The DTMI string.

        Returns:
        - The created path as a string.
        """
        if not dtmi_string.startswith("dtmi:"):
            raise ValueError("Invalid DTMI string format")

        # Replace ':' with the appropriate path separator
        dtmi_path = dtmi_string.replace(":", os.sep)

        # Replace the last ';' with a '-'
        dtmi_path = dtmi_path.replace(";", "-", 1)

        # Add the '.json' postfix
        dtmi_path += ".json"

        return dtmi_path
    
    @staticmethod
    def get_url_from_dtmi(dtmi_string):
        """
        Converts a DTMI string into a URL pointing to the corresponding expanded JSON file.

        Args:
            dtmi_string (str): The DTMI string.

        Returns:
            str: The URL pointing to the expanded JSON file.
        """
        if not dtmi_string.startswith("dtmi:"):
            raise ValueError("Invalid DTMI string format")

        # Replace ':' with '/' and the last ';' with '-'
        dtmi_path = dtmi_string.replace(":", "/").replace(";", "-", 1)

        if DEV_FLAG:
            # Development URL to be used for RC testing purposes
            base_url = "https://raw.githubusercontent.com/SW-Platforms/appconfig/refs/heads/fwdb-automation/"
        else:
            # Production URL to be used for final release
            base_url = "https://raw.githubusercontent.com/STMicroelectronics/appconfig/refs/heads/release/"
        return f"{base_url}{dtmi_path}.expanded.json"

    @staticmethod
    def remove_custom_dtdl_model(board_id, fw_id):
        """
        Removes the custom DTDL model for the specified board_id and fw_id from the local catalog.
        If the custom DTDL model file exists, it is deleted from the filesystem.

        Parameters:
        - board_id: The board ID as an integer.
        - fw_id: The firmware ID as an integer.
        """
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        catalog_dict = instance.catalog_dict
        # Access the catalog_info attribute
        catalog_info = instance.catalog_info

        # for each entry in the catalog_dict, check if the board_id and fw_id match
        # and remove the custom dtmi file if it exists 
        for entry in catalog_dict: 
            if entry["board_id"] == board_id and entry.get("fw_id",entry.get("usb_fw_id")) == fw_id:
                target_file_path = entry["custom_dtmi"]
                if os.path.exists(target_file_path):
                    os.remove(target_file_path)
                entry["custom_dtmi"] = ""
        
        # Save the updated catalog_dict back to the catalog file
        with open(LOCAL_DEVICE_CATALOG_PATH, "w") as catalog:
            catalog_json = {"usb": catalog_dict , "date": catalog_info["date"], "version": catalog_info["version"], "checksum": catalog_info["checksum"]} 
            json.dump(catalog_json, catalog, indent=4)

    @staticmethod
    def add_dtdl_model(board_id:int, fw_id:int, dtdl_model_name, dtdl_model_json):
        """
        Adds a new DTDL model to the local catalog or updates an existing one.

        Parameters:
        - board_id: The board ID as an integer.
        - fw_id: The firmware ID as an integer.
        - dtdl_model_name: The name of the DTDL model.
        - dtdl_model_json: The JSON content of the DTDL model.
        """
        
        # Convert board_id and fw_id to hexadecimal string
        board_id = hex(board_id)
        fw_id = hex(fw_id)    
        
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        catalog_dict = instance.catalog_dict
        # Access the catalog_info attribute
        catalog_info = instance.catalog_info

        # Prepare the target folder and file path
        target_folder = os.path.join(os.path.dirname(sys.modules[__name__].__file__), "dtmi", "custom")
        target_file_path = os.path.join(target_folder, os.path.basename(dtdl_model_name) + ".json")
        
        # Check if the entry already exists and update it
        dtm_updated = False
        for entry in catalog_dict:
            # Convert board_id and fw_id to integers if they are in hexadecimal string format 
            if entry["board_id"] == board_id and entry["fw_id"] == fw_id:
                entry["custom_dtmi"] = target_file_path
                print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Local version of existing Device Template Updated [{board_id},{fw_id}]")
                dtm_updated = True
                break
        
        # If the entry does not exist, add a new one
        if not dtm_updated:
            new_dtdl = {
                "board_id": board_id,
                "fw_id": fw_id,
                "custom_dtmi": target_file_path
            }
            catalog_dict.append(new_dtdl)
            print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - Added new Device Template [{board_id},{fw_id}] {target_file_path}")

        # Ensure the target folder exists
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        
        # Write the DTDL model JSON to the target file
        with open(target_file_path, "w") as file:
            file.write(dtdl_model_json)

        # Save the updated catalog_dict back to the catalog file
        with open(LOCAL_DEVICE_CATALOG_PATH, "w") as catalog:
            catalog_json = {"usb": catalog_dict , "date": catalog_info["date"], "version": catalog_info["version"], "checksum": catalog_info["checksum"]} 
            json.dump(catalog_json, catalog, indent=4)

    @staticmethod
    def query_dtdl_model(board_id, fw_id):
        
        # Access the singleton instance of DeviceCatalogManager
        instance = DeviceCatalogManager.get_instance()
        # Access the catalog_dict attribute
        catalog_dict = instance.catalog_dict
        
        dtdl_model_ids = []
        for entry in catalog_dict:
            if "board_id" in entry and entry["board_id"] != "":
                entry["board_id"] = int(entry["board_id"], 16) if isinstance(entry["board_id"], str) else entry["board_id"]
            else:
                # Skip the entry if the board_id is not present
                continue
            if "fw_id" in entry:
                entry["fw_id"] = int(entry["fw_id"], 16) if isinstance(entry["fw_id"], str) else entry["fw_id"]
            else:
                entry["usb_fw_id"] = int(entry["usb_fw_id"], 16) if isinstance(entry["usb_fw_id"], str) else entry["usb_fw_id"]
            board_id = int(board_id, 16) if isinstance(board_id, str) else board_id
            fw_id = int(fw_id, 16) if isinstance(fw_id, str) else fw_id
            if entry["board_id"] == board_id and (entry.get("fw_id") == fw_id or entry.get("usb_fw_id") == fw_id):
                if "custom_dtmi" in entry and entry["custom_dtmi"] != "":
                    print_warning(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - WARNING - CUSTOM User Device Model selected for (fw_id: {fw_id}, board_id {board_id}).")
                    dtdl_model_id = entry["custom_dtmi"]
                    dtdl_model_ids.append(dtdl_model_id)
                    print("{} - HSDatalogApp.{} - INFO - dtmi: {}".format(generate_datetime_string(), __name__, dtdl_model_id))
                elif "dtmi" in entry and entry["dtmi"] != "":
                    print(f"{generate_datetime_string()} - HSDatalogApp.{ __name__} - INFO - dtmi found in SDK supported models")
                    dtdl_model_id = DeviceCatalogManager.get_path_from_dtmi(entry["dtmi"])
                    dtdl_model_ids.append(dtdl_model_id)
                    print(f"{generate_datetime_string()} - HSDatalogApp.{__name__} - INFO - dtmi: {dtdl_model_id}")
        if len(dtdl_model_ids) == 1:
            dtdl_json_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), dtdl_model_id)
            with open(dtdl_json_path, "r") as device_model:
                return json.load(device_model)
        else:
            device_models = {}
            for dtm_id in dtdl_model_ids:
                dtdl_json_path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), dtm_id)
                with open(dtdl_json_path, "r") as device_model:
                    device_models[dtm_id] = json.load(device_model)
            return device_models
        return ""

class DeviceTemplateManager:

    def __init__(self, device_template_json: dict) -> None:
        self.device_template_model = device_template_json
        self.interface_list = self.__get_interface_list()
        
        self.root_component = None
        for interface in self.interface_list:
            if self.__is_root_interface(interface):
                self.root_component = interface
                break

        self.components = {}
        for content in self.root_component.contents:
            if content.type == DTM.ContentType.COMPONENT:
                for interface in self.interface_list:
                    if(content.schema == interface.id):
                        self.components[content.name] = interface

        # self.root_component = self.get_root_component()
        # self.components = self.get_components()

    def __get_interface_list(self):
        interfaces = []
        for d in self.device_template_model:
            if "contents" in d:
                interfaces.append(DTM.InterfaceElement.from_dict(d)) 
        return interfaces
    
    def __is_root_interface(self, interface):
        return interface.contents[0].type == DTM.ContentType.COMPONENT

    def get_root_component(self):
        return self.root_component
    
    def get_components(self):    
        return self.components

    def get_components_name_list(self):
        comp_names_list = []
        for c in self.components:
            comp_names_list.append(c.name)
        return comp_names_list

    def get_component(self, comp_name:str):
        try:
            res = self.components[comp_name]
            return res
        except:
            print_error("{} - HSDatalogApp.{} - ERROR - Component \'{}\' doesn't exist in your selected Device Template.".format(generate_datetime_string(), __name__, comp_name))
            # print("DeviceTemplateManager - ERROR - Component \'{}\' doesn't exist in your selected Device Template".format(comp_name))
            return None