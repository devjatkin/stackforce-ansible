#!/usr/bin/env bats

@test "Check admin_openrc" {
	    source /root/admin-openrc.sh 
		/usr/bin/openstack endpoint list
}

