#!/usr/bin/env bats


@test "List Nova services" {
    source /root/admin-openrc.sh
    nova service-list | grep nova-compute
}

@test "List Nova endpoints" {
    source /root/admin-openrc.sh
    nova endpoints
}
