#!/bin/bash
#
# Post install script for test environments
#
yum install -y wget

source /root/admin-openrc.sh

neutron net-create ext-net --router:external True \
    --provider:physical_network external --provider:network_type flat

neutron subnet-create ext-net --name ext-subnet \
    --allocation-pool start=192.168.10.100,end=192.168.10.200 --disable-dhcp\
    --gateway 192.168.10.1 192.168.10.0/24

openstack project list

ADMIN=`openstack project list | grep admin | awk '{print $2}'`

neutron net-create demo-net --tenant-id $ADMIN --provider:network_type vlan
neutron subnet-create demo-net --name demo-subnet --gateway 192.168.1.1 192.168.1.0/24

neutron router-create router01
neutron router-interface-add router01 demo-subnet
neutron router-gateway-set router01 ext-net

# Glance
wget -P /tmp/images http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1601.qcow2
glance image-create --name centos7 --visibility public --disk-format qcow2 --container-format bare --file /tmp/images/CentOS-7-x86_64-GenericCloud-1601.qcow2
