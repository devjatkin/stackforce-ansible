#!/usr/bin/env python

import os
import sys
import json
import lxc
import re
import ConfigParser
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.group import Group
from ansible.inventory.ini import InventoryParser

if os.geteuid() != 0:
    os.execvp("sudo", ["sudo"] + sys.argv)

config = ConfigParser.ConfigParser()
# setting defaults
config.add_section("os")
config.set("os", "inventory_file", None)

config.read('/etc/stackforce/parameters.ini')


result = {}
result['all'] = {}
hostvars = {}
os_vars = {
    'os_rabbit_host': config.get('public', 'address'),
    'os_rabbit_port': config.get('os', 'rabbit_port')}

# TODO: Handle hosts with same name
inventory_file = config.get("os", "inventory_file")
if inventory_file:
    dl = DataLoader()
    inv = InventoryParser(dl, {"ungrouped":Group("ungrouped"), "all":Group("all")}, inventory_file)
    for grp in inv.groups:
        if grp not in result:
            result[grp]={'hosts':[], 'vars':os_vars}
        for host in inv.groups[grp].hosts:
            result[grp]['hosts'].append(host.name)
            hostvars[host.name]=host.vars
    

containers = lxc.list_containers(active=True, defined=False)
for container_name in containers:
    srv = re.split('_', container_name)
    group = srv[0]
    if not group in result:
        result[group] = {}
        result[group]['hosts'] = []
        result[group]['vars'] = os_vars
    if isinstance(result[group], dict):
        result[group]['hosts'].append(container_name)
    # get ip from container object
    container = lxc.Container(name=container_name)
    result['all']['hosts'] = containers
    if container.get_interfaces():
        ips = container.get_ips()
        if len(ips):
            hostvars[container_name] = dict(ansible_ssh_host=ips[0])

result['all'] = containers
result['_meta'] = {'hostvars': hostvars}

if len(sys.argv) == 2 and sys.argv[1] == '--list':
    print(json.dumps(result))
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
    print("TODO: SSH support")
else:
    print("Need an argument, either --list or --host <host>")
