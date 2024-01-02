# commander

a cli scraping tool for network devices.

## abilities

* can connect to multiple devices at once
* stores all the connection information (passwords, IPs, ect...) in [Keepass](https://keepass.info)

### the problem

every network device is also a computer that needs to be managed. 
networking and IT teams work hard to maintain a level of standardization in the network but with large scale networks it becomes almost impossible.

### the solution

with commander, you can push a configuration change in seconds to every device in your organization
```bash
commander deploy change_snmp_secret.txt
```

