# Stackforce Cloudlinux #

Main goal of project is deploying OpenStack using Ansible and rpm packages from RDOproject.

## Quickstart with Vagrant ##

For install vagrant follow this guide: https://docs.vagrantup.com/v2/installation/

Default box: "bento/centos7.2", you can set different box name with VAGRANT_BOX_NAME environment variable

```
#!shell

# git clone --recursive git@bitbucket.org:stackforce/stackforce-ansible.git
# cd stackforce-ansible
# vagrant up
```
## Quickstart with Triple-O ##
Openstack dev-environment over Openstack installation procedure:
```
./run_tripleo.sh USERNAME
```
IMPORTANT: s/USERNAME/your_username/

example ~/.ansible.cfg:
```
[ssh_connection]
ssh_args = -o ForwardAgent=yes -o ControlMaster=no -o StrictHostKeyChecking=no
```


example /etc/openstack/clouds.yaml:

```
#!yaml
---
clouds:
  stackforce:
    auth:
      auth_url: "http://admin_endpoint_ip:35357/v3"
      project_name: "admin"
      project_domain_name: default
      user_domain_name: default
      username: "cloud_admin_username"
      password: "cloud_admin_password"
    identity_api_version: "3"
    region_name: "RegionOne"
  tripleo:
    auth:
      auth_url: "http://admin_endpoint_ip:35357/v3"
      project_name: "USERNAME"
      project_domain_name: default
      user_domain_name: default
      username: "your_username"
      password: "your_password"
    identity_api_version: "3"
    region_name: "RegionOne"

```
