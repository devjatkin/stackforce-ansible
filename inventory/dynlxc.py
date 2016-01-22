#!/usr/bin/env python

import os
import sys
import json
import lxc
import re


if os.geteuid() != 0:
    os.execvp("sudo", ["sudo"] + sys.argv)

result = {}
result['all'] = {}
hostvars = {}

containers = lxc.list_containers(active=True, defined=False)
for container_name in containers:
    srv = re.split('_', container_name)
    group = srv[0]
    if not group in result:
        result[group] = {}
        result[group]['hosts'] = []
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
