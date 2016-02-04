#!/usr/bin/env bats


@test "Create network" {
    source /root/admin-openrc.sh
    neutron net-create public --shared --provider:physical_network provider  --provider:network_type flat
}

@test "Add subnet to network" {
    source /root/admin-openrc.sh
    neutron subnet-create public --name demo-subnet --gateway 192.168.1.1 192.168.1.0/24
}
