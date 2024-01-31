# commander

Commander is a cli scraping tool for network devices.

* blazingly fast
* multi-threaded 
* secure by design - stores every connection information (passwords, IPs, ect...) in [Keepass](https://keepass.info)

it offers the ability to send commands to multiple devices at once. 

networking and IT teams work hard to maintain a level of standardization in the network but with a  large scale networks it becomes almost impossible.
so we leave our networks scattered and flawed or spend hours doing it by hand.
tools like [Ansible](https://www.ansible.com/), [Puppet](https://www.puppet.com/) and [Chef](https://www.chef.io/) are also really great for maintaining standardization,
but they come with a very high learning carve, another set of infrastructure that you need to manage and are sometimes are a headache to set up. 

## Installation

install NetworkCommander with a simple pip install

```bash
pip install NetworkCommander
```

## usage

with commander, you can push a configuration change in seconds to every device in your organization
```bash
commander device deploy "show ip ospf neighbor"
```

you can add devices 