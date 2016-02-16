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


def get_config(config_file='/etc/stackforce/parameters.ini'):
    cnf = ConfigParser.ConfigParser()
    # setting defaults
    cnf.add_section("os")
    cnf.set("os", "inventory_file", None)

    cnf.read(config_file)
    return cnf


def read_inventory_file(inventory_filepath):
    res = dict()
    hostvars = {}
    groupvars = {}
    dl = DataLoader()
    inv = InventoryParser(dl, {"ungrouped": Group("ungrouped"),
                               "all": Group("all")},
                          inventory_filepath)
    for grp in inv.groups:
        res[grp] = {'hosts': [], 'vars': {}}
        groupvars[grp] = inv.groups[grp].vars
        for host in inv.groups[grp].hosts:
            res[grp]['hosts'].append(host.name)
            hostvars[host.name] = host.vars
    res["_meta"] = {
        "hostvars": hostvars,
        "groupvars": groupvars
    }
    res["all"] = hostvars.keys()
    return res


def list_containers():
    res = dict()
    hostvars = {}
    containers = lxc.list_containers(active=True, defined=False)
    for container_name in containers:
        srv = re.split('_', container_name)
        group = srv[0]
        if group not in res:
            res[group] = {}
            res[group]['hosts'] = []
        if isinstance(res[group], dict):
            res[group]['hosts'].append(container_name)
        container = lxc.Container(name=container_name)
        if container.get_interfaces():
            ips = container.get_ips()
            if len(ips):
                hostvars[container_name] = dict(ansible_ssh_host=ips[0])
    res["_meta"] = {"hostvars": hostvars}
    res['all'] = list(containers)
    return res


# TODO: Handle hosts with same name
# TODO: Handle groups with same name
# TODO: What if groupvars/hostvars doesn't exists?
def merge_results(a, b):
    res = a
    res["all"] = res["all"] + b["all"]
    for grp in b:
        if grp == "all":
            continue
        if grp == "_meta":
            if "groupvars" in b["_meta"]:
                if "groupvars" not in res["_meta"]:
                    res["_meta"]["groupvars"] = {}
                for group in b["_meta"]["groupvars"]:
                    res["_meta"]["groupvars"][group] = b["_meta"]["groupvars"][group]
            if "hostvars" in b["_meta"]:
                if "hostvars" not in res["_meta"]:
                    res["_meta"]["hostvars"] = []
                for host in b["_meta"]["hostvars"]:
                    res["_meta"]["hostvars"][host] = b["_meta"]["hostvars"][host]
        else:
            res[grp] = b[grp]
    return res


def add_extravars(res, extra_vars):
    for host in res["_meta"]["hostvars"]:
        for var in extra_vars:
            res["_meta"]["hostvars"][host][var] = extra_vars[var]
    return res

if __name__ == "__main__":
    config = get_config()
    inventory_file = config.get("os", "inventory_file")
    os_vars = {
        'os_rabbit_host': config.get('public', 'address'),
        'os_rabbit_port': config.get('os', 'rabbit_port'),
        'os_verbose': config.get('os_logs', 'verbose'),
        'os_debug': config.get('os_logs', 'debug')}
    result = merge_results(list_containers(),
                           read_inventory_file(inventory_file))
    result = add_extravars(result, os_vars)
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(result))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print("TODO: SSH support")
    else:
        print("Need an argument, either --list or --host <host>")
