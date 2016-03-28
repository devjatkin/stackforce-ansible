#!/usr/bin/env python

import argparse
import ConfigParser
import hashlib
import json
import os
import pwd
import re
import subprocess
import sys

import lxc

import yaml
from ansible.inventory.group import Group
from ansible.inventory.ini import InventoryParser
from ansible.parsing.dataloader import DataLoader

OS_VARIABLE_NAME = 'DYNLXC_CONF'
ANSIBLE_SSH_HOST_INDEX = -1
DEFAULT_CONF = '/etc/stackforce/parameters.ini'


class DynLxcConnectionError(Exception):
    pass


def get_config(config_file):
    cnf = ConfigParser.ConfigParser()
    # setting defaults
    cnf.add_section("os")
    cnf.set("os", "inventory_file", None)
    cnf.set("os", "unique_containers_file", None)

    cnf.read(config_file)
    return cnf


def get_unique_container_name(name, salt, number):
    s = str(name) + str(salt) + str(number)
    hsh = hashlib.sha256(s).hexdigest()
    return "{}_container-{}".format(name, hsh[:8])


def add_var_lxc_containers_to_controllers(inventory, containers_config):
    match = {"groups": "groupvars", "hosts": "hostvars"}
    for m in match:
        for group_name in containers_config.get(m, []):
            container_names = {}
            group = containers_config[m][group_name]
            for container_name, vars in group.items():
                count = vars.pop('count')
                vars['name'] = container_name
                for n in range(count):
                    name = get_unique_container_name(container_name,
                                                     group_name, n)
                    container_names[name] = vars
                # container_names.extend(
                    # [ for i in range(count)])
            inv_group = inventory['_meta'].get(match[m], {}).get(group_name,
                                                                 {})
            inv_group["lxc_containers"] = container_names
            inventory['_meta'][match[m]][group_name] = inv_group
    return inventory


def getlogin():
    return pwd.getpwuid(os.getuid()).pw_name


def run_ssh_command(host, user, port, key, command):
    tmpl = ("ssh -t -o BatchMode=yes "
            "-o UserKnownHostsFile=/dev/null "
            "-o StrictHostKeyChecking=no {host} "
            "-l {user} -p {port} -i {key_filename} "
            "{command}")
    ps = subprocess.Popen(tmpl.format(
        host=host,
        user=user,
        port=port,
        key_filename=key,
        command=command), shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ps.stdout.read()


def get_containers_list(host, user, port, key_filename):
    cmd_run_containers = run_ssh_command(
        host, user, port, key_filename, "sudo lxc-ls --active")
    return cmd_run_containers.split()


def get_container_ip(container, host, user, port, key_filename):
    result = run_ssh_command(host, user, port, key_filename,
                             "sudo lxc-info -i --name " + container,)
    return result.split()


def list_containers_on_host(host, user, port, key_filename):
    res = {"_meta": {"hostvars": {}}}
    containers = get_containers_list(host, user, port, key_filename)
    for container_name in containers:
        srv = re.split('_container', container_name)
        group = re.split('_', srv[0])[0]
        if group not in res:
            res[group] = {}
            res[group]['hosts'] = []
        if isinstance(res[group], dict):
            res[group]['hosts'].append(container_name)
        cmd_run_container_ip = get_container_ip(
            container_name, host, user, port, key_filename)
        if len(cmd_run_container_ip):
            res["_meta"]['hostvars'][container_name] = \
                {"ansible_host": cmd_run_container_ip[-1]}
    res["all"] = list(res['_meta']['hostvars'].keys())
    return res


def list_remote_containers(hostvars):
    """

    @param hostvars: ansible hostvars,like "hostname":{"ansible_*":".."}
    @return: inventory result
    """
    res = {"_meta": {"hostvars": {}}, "all": []}
    for host, data in hostvars.iteritems():
        ssh_host = "local" if (
            data.get("ansible_connection") == "local") else (
                data.get("ansible_host", host)
        )
        ssh_user = data.get("ansible_ssh_user",
                            data.get("ansible_user", getlogin()))
        ssh_port = data.get("ansible_port", 22)
        ssh_key_filename = data.get("ansible_ssh_private_key_file",
                                    os.path.expanduser("~/.ssh/id_rsa"))
        containers = list_containers_on_host(ssh_host, ssh_user, ssh_port,
                                             ssh_key_filename)
        res = merge_results(res, containers)
    return res


def get_remote_controllers(inventory):
    res_hostvars = {}
    controllers = inventory.get("controller", {})
    for host in controllers.get("hosts", []):
        if inventory["_meta"]["hostvars"][host].get(
                "ansible_connection", "remote") != "local":
            res_hostvars[host] = inventory["_meta"]["hostvars"][host]
    return res_hostvars


def read_inventory_file(inventory_filepath):
    res = dict()
    hostvars = {}
    dl = DataLoader()
    inv = InventoryParser(dl, {"ungrouped": Group("ungrouped"),
                               "all": Group("all")},
                          inventory_filepath)
    for grp in inv.groups:
        res[grp] = {'hosts': [], 'vars': {}}
        res[grp]['vars'] = inv.groups[grp].vars
        for host in inv.groups[grp].hosts:
            res[grp]['hosts'].append(host.name)
            hostvars[host.name] = host.vars
    res["_meta"] = {
        "hostvars": hostvars,
    }
    res["all"] = sorted(hostvars.keys())
    return res


def get_group_name_from_container(container_name):
    srv = re.split('_container', container_name)
    group = "{}".format(re.split('_', srv[0])[0])
    return group


def list_containers():
    res = dict()
    hostvars = {}
    containers = lxc.list_containers(active=True, defined=False)
    for container_name in containers:
        group = get_group_name_from_container(container_name)
        if group not in res:
            res[group] = {}
            res[group]['hosts'] = []
        if isinstance(res[group], dict):
            res[group]['hosts'].append(container_name)
        container = lxc.Container(name=container_name)
        if container.get_interfaces():
            ips = container.get_ips()
            if len(ips):
                hostvars[container_name] = \
                    dict(ansible_host=ips[ANSIBLE_SSH_HOST_INDEX])
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
                    res["_meta"]["groupvars"] = b["_meta"]["groupvars"]
                for group in b["_meta"]["groupvars"]:
                    res["_meta"]["groupvars"][group] = \
                        b["_meta"]["groupvars"][group]
            if "hostvars" in b["_meta"]:
                if "hostvars" not in res["_meta"]:
                    res["_meta"]["hostvars"] = []
                for host in b["_meta"]["hostvars"]:
                    res["_meta"]["hostvars"][host] = \
                        b["_meta"]["hostvars"][host]
        else:
            if grp not in res:
                res[grp] = b[grp]
            else:
                res[grp]['hosts'].extend(b[grp]['hosts'])
    return res


def add_extravars(res, extra_vars):
    for host in res["_meta"]["hostvars"]:
        for var in extra_vars:
            res["_meta"]["hostvars"][host][var] = extra_vars[var]
    return res


def main(inventory_file, uniq_containers_file, **extra_vars):
    result = merge_results(list_containers(),
                           read_inventory_file(inventory_file))
    remote_controllers = get_remote_controllers(result)
    if remote_controllers:
        result = merge_results(result,
                               list_remote_containers(remote_controllers))
    if uniq_containers_file:
        with open(uniq_containers_file) as fh:
            unique_containers = yaml.load(fh)
        result = add_var_lxc_containers_to_controllers(result,
                                                       unique_containers)
    result = add_extravars(result, extra_vars)
    return result


def parse_args(args):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--host')

    parser.add_argument('-c', '--conf', default=DEFAULT_CONF, dest='conf')
    return parser.parse_args(args)


if __name__ == "__main__":

    if os.geteuid() != 0:
        os.execlpe('sudo', *['sudo', sys.executable] + sys.argv + [os.environ])

    args = parse_args(sys.argv[1:])
    if args.host:
        raise NotImplementedError("TODO: SSH support")

    config_path = os.environ.get(OS_VARIABLE_NAME, args.conf)
    config = get_config(config_path)

    inventory_file = config.get("os", "inventory_file")
    uniq_containers_file = config.get("os", "unique_containers_file")
    os_vars = {
        'os_rabbit_host': config.get('public', 'address'),
        'os_rabbit_port': config.get('os', 'rabbit_port'),
        'os_verbose': config.get('os_logs', 'verbose'),
        'os_debug': config.get('os_logs', 'debug')}

    result = main(inventory_file, uniq_containers_file, **os_vars)
    print(json.dumps(result))
