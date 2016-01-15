#!/usr/bin/env bats

OS_CLIENT="openstack --os-cloud stackforce"

@test "Admin project" {
    $OS_CLIENT project list | grep admin
}

@test "Admin project description" {
    $OS_CLIENT project show admin | grep description
}

@test "Service project" {
    $OS_CLIENT project list | grep service
}
