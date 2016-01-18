#!/usr/bin/env bats


@test "List images" {
    source /root/admin-openrc.sh
    glance image-list
}

@test "Upload image" {
    curl -O http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-x86_64-disk.img
    source /root/admin-openrc.sh
    glance  image-create --name "cirros"   --file cirros-0.3.4-x86_64-disk.img   --disk-format qcow2 --container-format bare  --visibility public --progress
}

@test "List uploaded image" {
    source /root/admin-openrc.sh
    glance image-list | grep cirros
}

@test "Delete test image" {
    source /root/admin-openrc.sh
    glance image-list | grep cirros | echo `awk -F "| " '{print $2}'` | xargs glance image-delete
    rm -rf cirros-0.3.4-x86_64-disk.img
}
