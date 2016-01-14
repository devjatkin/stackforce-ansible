#/bin/bash

for i in `lxc-ls`; do echo lxc-stop -n $i && lxc-destroy -n $i; done
rm -rf /var/lib/lxc/*
vgremove -f lxc
pvremove -f /dev/sdb
