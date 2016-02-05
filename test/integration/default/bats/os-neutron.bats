#!/usr/bin/env bats


@test "Create external network" {
    source /root/admin-openrc.sh
    neutron net-create public --router:external True --provider:physical_network external  --provider:network_type flat
    neutron subnet-create public --name ext-subnet --allocation-pool start=192.168.1.100,end=192.168.1.200 --gateway 192.168.1.1 192.168.1.0/24
}

@test "Create tenant network" {
    source /root/admin-openrc.sh
    neutron net-create demo-net --provider:network_type vlan
    neutron subnet-create demo-net --name demo-subnet --gateway 192.168.3.1 192.168.3.0/24
}

@test "Create router" {
    source /root/admin-openrc.sh
    neutron router-create demo-router
    neutron router-interface-add demo-router demo-subnet
    neutron router-gateway-set demo-router public
}
