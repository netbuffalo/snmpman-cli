# status snmpman service.
$ sudo supervisorctl status snmpman
snmpman                          RUNNING   pid 5367, uptime 0:00:18

# start snmpman service.
$ sudo supervisorctl start snmpman
snmpman                          RUNNING   pid 5367, uptime 0:00:18

# add ip address to this server. 
$ sudo /opt/snmpman-cli/bin/ipadd.py -s 172.16.0.1 -e 172.16.0.255
 or 
$ sudo /opt/snmpman-cli/bin/ipadd.py -s 172.16.0.1 -n 100
