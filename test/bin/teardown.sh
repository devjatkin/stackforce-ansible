#/bin/bash

for i in `lxc-ls`; do lxc-stop -n $i && lxc-destroy -n $i; done
rm -rf /var/lib/lxc/*
LXCPV=$(pvs | grep lxc | awk '{print $1 }')
vgremove -f lxc
pvremove -f $LXCPV
