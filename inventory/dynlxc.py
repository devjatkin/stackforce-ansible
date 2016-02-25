#!/usr/bin/env python

import os
import sys
import json
import yaml
import lxc
import re
import ConfigParser
import subprocess
import hashlib
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.group import Group
from ansible.inventory.ini import InventoryParser


def get_config(config_file='/etc/stackforce/parameters.ini'):
    cnf = ConfigParser.ConfigParser()
    # setting defaults
    cnf.add_section("os")
    cnf.set("os", "inventory_file", None)
    cnf.set("os", "unique_containers_file", None)

    cnf.read(config_file)
    return cnf


def get_unique_containers_config(filepath):
    f = open(filepath)
    data = f.read()
    cnf = yaml.load(data)
    return cnf


def get_unique_container_name(name, salt, number):
    s = str(name)+str(salt) + str(number)
    hsh = hashlib.sha256(s).hexdigest()
    return "{}_container-{}".format(name, hsh[:8])


def add_var_lxc_containers_to_controllers(inventory, containers_config):
    match = {"groups": "groupvars", "hosts": "hostvars"}
    for m in match:
        for group_name in containers_config.get(m, []):
            container_names = []
            for container_name, count in containers_config[m][group_name].items():
                container_names.extend([get_unique_container_name(container_name,
                                                                  group_name,
                                                                  i) for i in range(count)])
            inv_group = inventory['_meta'].get(match[m], {}).get(group_name, {})
            inv_group["lxc_containers"] = container_names
            inventory['_meta'][match[m]][group_name] = inv_group
    return inventory


def list_remote_containers(hostvars):
    """

    @param hosts: ansible hostvars, uri:key, ex.: "root@192.168.10.6":"/home/vagrant/id_rsa"
    @return: inventory result
    """
    res = {"_meta": {"hostvars": {}}}
    tmpl_ssh_command = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {host} -l {user} -p {port} -i {key_filename} {command}"
    for host, data in hostvars.iteritems():
        is_local = data.get("ansible_connection") == "local"
        ssh_host = data.get("ansible_ssh_host", data.get("ansible_host"))
        if is_local:
            ssh_host = "localhost"
        ssh_user = data.get("ansible_ssh_user", data.get("ansible_user", "root"))
        ssh_port = data.get("ansible_ssh_port", data.get("ansible_port", 22))
        ssh_key_filename = data.get("ansible_ssh_private_key_file", "~/.ssh/id_rsa")
        cmd_list_containers = tmpl_ssh_command.format(
            host=ssh_host,
            user=ssh_user,
            port=ssh_port,
            key_filename=ssh_key_filename,
            command="sudo lxc-ls --active"
        )
        cmd_run_containers = run_command(cmd_list_containers)
        containers = cmd_run_containers.split()
        for name in containers:
            cmd_get_container_ip = tmpl_ssh_command.format(
                host=ssh_host,
                user=ssh_user,
                port=ssh_port,
                key_filename=ssh_key_filename,
                command="sudo lxc-info -i --name {}".format(name)
            )
            srv = re.split('_', name)
            group = srv[0]
            if group not in res:
                res[group] = {}
                res[group]['hosts'] = []
            if isinstance(res[group], dict):
                res[group]['hosts'].append(srv)
            cmd_run_container_ip = run_command(cmd_get_container_ip).split()
            if len(cmd_run_container_ip):
                res["_meta"]['hostvars'][name] = {"ansible_host": cmd_run_container_ip[-1]}
        res["all"] = list(res['_meta']['hostvars'].keys())
        return res


def get_remote_controllers(inventory):
    res_hostvars = {}
    controllers = inventory.get("controller", {})
    for host in controllers.get("hosts", []):
        if inventory["_meta"]["hostvars"][host].get("ansible_connection", "remote") != "local":
            res_hostvars[host]=inventory["_meta"]["hostvars"][host]
    return res_hostvars


def run_command(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read()


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
    if os.geteuid() != 0:
        os.execvp("sudo", ["sudo"] + sys.argv)

    config = get_config()
    inventory_file = config.get("os", "inventory_file")
    uniq_containers_file = config.get("os", "unique_containers_file")
    os_vars = {
        'os_rabbit_host': config.get('public', 'address'),
        'os_rabbit_port': config.get('os', 'rabbit_port'),
        'os_verbose': config.get('os_logs', 'verbose'),
        'os_debug': config.get('os_logs', 'debug')}
    result = merge_results(list_containers(),
                           read_inventory_file(inventory_file))
    remote_controllers = get_remote_controllers(result)
    if remote_controllers:
        result = merge_results(result,
                               list_remote_containers(remote_controllers))
    if uniq_containers_file:
        unique_containers = get_unique_containers_config(uniq_containers_file)
        result = add_var_lxc_containers_to_controllers(result, unique_containers)
    result = add_extravars(result, os_vars)
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        print(json.dumps(result))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print("TODO: SSH support")
    else:
        print("Need an argument, either --list or --host <host>")
