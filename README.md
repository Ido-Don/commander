# commander

Commander is a cli scraping tool for network devices.
it offers the ability to connect and run a command on a lot of network devices at once. 

## Installation

install NetworkCommander with a simple pip install

```bash
pip install NetworkCommander
```

## Why?

every network device is also a computer that needs to be managed. 
networking and IT teams work hard to maintain a level of standardization in the network but with large scale networks it becomes almost impossible.
Instead of counting on humans to mannualy check the software version in 200 devices, have the commander check all of them at once!

## high level functionality

* can run commands on multiple devices at once
* stores all the connection information (passwords, IPs, ect...) in [Keepass](https://keepass.info)
* never need to remember an ip or hostname again

with commander, you can push a configuration change in seconds to every device in your organization
```bash
commander device deploy "show ip ospf neighbor"
```

