#!/usr/bin/env bats


@test "List images" {
    source /root/admin-openrc.sh
    glance image-list
}

@test "Upload image" {
    curl -O stackforce.cloudlinux.com/repos/cirros-lxc.img
    source /root/admin-openrc.sh
	glance image-create --name cirros-lxc --visibility public --disk-format raw --container-format bare --progress --file  cirros-lxc.img
}

@test "List uploaded image" {
    source /root/admin-openrc.sh
    glance image-list | grep cirros
}

#@test "Delete test image" {
#    source /root/admin-openrc.sh
#    glance image-list | grep cirros | echo `awk -F "| " '{print $2}'` | xargs glance image-delete
#    rm -rf cirros-0.3.4-x86_64-disk.img
#}
