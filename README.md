# stdatalog_pnpl

![latest tag](https://img.shields.io/github/v/tag/STMicroelectronics/stdatalog_pnpl.svg?color=brightgreen)

The **[stdatalog_pnpl](https://github.com/STMicroelectronics/stdatalog_pnpl)** package is used to manage device template models, which are high-level descriptors of the (board + firmware) system.

The package is part of the **[STDATALOG-PYSDK](https://github.com/STMicroelectronics/stdatalog-pysdk)**, which is a set of libraries and tools that enable the development of applications for data logging and data monitoring.

Device Template Models are designed following the **[DTDLv2](https://github.com/Azure/opendigitaltwins-dtdl/blob/master/DTDL/v2/DTDL.v2.md)** standard, which is a JSON-based language that describes the capabilities of a system and its components.
The package facilitates the creation and dynamic management of the commands-set that can be exchanged between target devices and the Python SDK.
To achieve this, the package provides the **PnPLCmd** class, which provides a set of methods to create and manage various types of PnP**L** commands.
The PnPL acronym stands for "Plug and Play **Like**", and is inspired by the **[Plug and Play]** standard from the **[Azure IoT](https://docs.microsoft.com/en-us/azure/iot-pnp/overview-iot-plug-and-play)** ecosystem.

This feature is particularly useful for developers who need to customize and integrate various devices into their projects, ensuring seamless communication between the devices and the SDK.

## Features

- Manage device template models
- Follow the DTDLv2 standard
- Facilitate the creation and dynamic management of PnPL commands exchanged between target devices and the SDK

## Installation

To install the `stdatalog_pnpl` package after downloading it, execute the following command from the package's root directory:

On Windows:
```sh
python -m pip install dist\stdatalog_pnpl-1.1.0-py3-none-any.whl
```

On Linux/macOS:
```sh
python3 -m pip install dist/stdatalog_pnpl-1.1.0-py3-none-any.whl
```

The package could also be installed as part of the **STDATALOG-PYSDK** by launching the SDK installation script from the SDK root folder:

On Windows:
```sh
.\STDATALOG-PYSDK_install.bat
```

On Linux/macOS:
```sh
./STDATALOG-PYSDK_install.sh
```

Source code is also available within the inner `stdatalog_pnpl` folder.

## Usage
Here is a basic example of how to use the stdatalog_pnpl package:

```python
from stdatalog_pnpl.DTDL.device_template_manager import DeviceTemplateManager

# Initialize the device template manager
dtm = DeviceTemplateManager()

# Load a device template
template = dtm.load_template('path/to/template.json')

# Print the template
print(template)
```
Here is an example of how to create and manage commands using the PnPLCmd class:

```python
# Initialize the PnPLCmd
cmd = PnPLCmd()

# Create a command to get the presentation string
get_presentation_cmd = cmd.create_get_presentation_string_cmd()
print("Get Presentation Command:", get_presentation_cmd)

# Create a command to get the identity string (for HSDatalog2 > v1.2.0)
get_identity_cmd = cmd.create_get_identity_string_cmd()
print("Get Identity Command:", get_identity_cmd)

# Create a command to get the device status
get_device_status_cmd = cmd.create_get_device_status_cmd()
print("Get Device Status Command:", get_device_status_cmd)

# Create a command to get the status of a specific component
get_component_status_cmd = cmd.create_get_component_status_cmd("component_name")
print("Get Component Status Command:", get_component_status_cmd)

# Create a command to set a property of a component
set_property_cmd = cmd.create_set_property_cmd("component_name", "property_name", "property_value")
print("Set Property Command:", set_property_cmd)

# Create a command to set a nested property of a component
set_nested_property_cmd = cmd.create_set_property_cmd("component_name", ["nested", "property", "name"], "property_value")
print("Set Nested Property Command:", set_nested_property_cmd)
```

## License
This project is licensed under the BSD 3-Clause License - see the LICENSE.md file for details.