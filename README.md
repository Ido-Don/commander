# Commander

Commander is a powerful command-line interface (CLI) scraping tool designed for managing and interacting with multiple network devices simultaneously.

## Features

- **:zap:Blazingly Fast:** Commander is optimized for speed, allowing you to execute commands swiftly across your network devices.
- **:thread:Multi-threaded:** Leverage the efficiency of multi-threading to process commands concurrently, ensuring quick and efficient communication with all devices.
- **:lock:Secure by Design:** Prioritizing security, Every connection is made from your local machine. in addition, Commander stores sensitive connection information, such as passwords and IPs locally on your computer, in [Keepass](https://keepass.info), a renowned open-source password manager.

## Problem Statement

Networks, especially in large-scale environments, often face challenges in maintaining standardization. The complexity grows, making it challenging for networking and IT teams to enforce uniform configurations across devices. Without proper tools, networks may become scattered and prone to inconsistencies, or administrators may spend hours manually configuring each device.

While tools like [Ansible](https://www.ansible.com/), [Puppet](https://www.puppet.com/), and [Chef](https://www.chef.io/) are excellent for maintaining standardization, they come with a steep learning curve, additional infrastructure management, and setup complexities.

Commander aims to provide a simpler alternative, allowing users to swiftly execute commands across multiple devices without the overhead of a complex infrastructure.

## Installation

Install Commander with a simple pip command:

```bash
pip install NetworkCommander
```

## compile from source

if you want to compile from source you can do that with [poetry](https://python-poetry.org/https://python-poetry.org/).

first you have to make sure poetry is installed

```bash
poetry --version
```

after you did that you can start the build.

```bash
poetry install
poetry build
```

a folder named dist will apper with the .tar.gz and .whl files.

```bash
pip install ./dist/path/to/.whl
```

after that you can fully use commander

## Usage
### Version Check

Check the version of Commander:

```bash
commander version
```

### Initialization

Before using Commander, ensure it's initialized. Run the following command to generate the keepass database and provide the password for it:

```bash
commander init
```

## Device Management
### List Devices

List all devices under your command, optionally filtered by tags:

```bash
commander device list --tag <tag_name>
```

### Add Device

Add a new device to the database, specifying the device's password:

```bash
commander device add "router1(cisco_ios) -> root@1.1.1.1"
```

Alternatively, you can provide a file containing device strings:

```bash
commander device add --devices_file path/to/devices_file
```

If you don't enter any device or a device file the program defaultly will read from devices from stdin.

```bash
commander device add

r1(cisco_ios) -> root@localhost:5000
^Z
```

### Remove Device

Remove one or more devices from the database:

```bash
commander device remove <device_name_1> <device_name_2> ...
```

## Tag Management
### Add Tag

Add a tag to devices for better segmentation:

```bash
commander device tag add <tag_name> <device_name_1> <device_name_2> ...
```
### Remove Tag

Remove a tag from devices:

```bash
commander device tag remove <tag_name> <device_name_1> <device_name_2> ...
```

### List Tags

List all tags applied to devices:

```bash
commander device tag list
```
## Device Connectivity
### Ping Devices

this command will try to connect to every device in your database, it will not deploy any commands to the device.

optionally filter by tags.

```bash
commander device ping --tag <tag_name>
```

### Command Deployment

in order to deploy a command to the devices in your database need to use the deploy command

```bash
commander device deploy "<command_1>" "<command_2>" 
```

in case you want to deploy the commands to some devices but not all you can use tags.

```bash
commander device deploy --tag "router" "<command_1>" "<command_2>" 
```

if there are any spasific devices you need to deploy to you can use the --device option also

```bash
commander device deploy --tag "router" --device "device not tagged with router" "<command_1>" "<command_2>" 
```

By default, the "deploy" command will deploy with the most basic permission level possible.

In order to escalate the permisions you need to specify the --permision_level flag

```bash
commander device deploy  --permision_level "configure_terminal" "<command_1>" "<command_2>" 
```

Output Folder (Optional)

Save command output to a specified folder:

```bash
commander device deploy --output_folder <path/to/output_folder> "<command>"
```

## Conclusion

Commander provides a streamlined solution for scraping network devices, offering speed and simplicity without the complexities of traditional configuration management tools. Empower your networking and IT teams to enforce standardization across your network effortlessly.

Have a great experience with Commander!