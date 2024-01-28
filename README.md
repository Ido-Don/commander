# commander

Commander is a cli scraping tool for network devices.
it offers the ability to connect to multiple devices and run a command at once. 

## Installation

install NetworkCommander with a simple pip install

```bash
pip install NetworkCommander
```

## Why?

Every network device is also a computer that needs to be managed. 
networking and IT teams work hard to maintain a level of standardization in the network but with large scale networks it becomes almost impossible.
Instead of counting on humans to manually check the software version in 200 devices, have the commander check all of them at once!

## High level functionality

* Commander can run commands on multiple devices at once
* Commander stores every connection information (passwords, IPs, ect...) in [Keepass](https://keepass.info)
* You will never need to remember an ip or hostname again!

with commander, you can push a configuration change in seconds to every device in your organization
```bash
commander device deploy "show ip ospf neighbor"
```

