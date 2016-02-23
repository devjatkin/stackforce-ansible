# Stackforce Cloudlinux #
## Quickstart ##
Install vagrant using https://docs.vagrantup.com/v2/installation/
Default box: "bento/centos7.2", you can set different box name with VAGRANT_BOX_NAME enviroment variable

```
#!shell

# git clone --recursive git@bitbucket.org:stackforce/stackforce-ansible.git
# cd stackforce-ansible
# vagrant up
```

Openstack dev-environment over Openstack installation procedure:

```
#!shell
$ vagrant plugin install vagrant-openstack-provider
```
- A "centos7" image
- Edit Vagrantfile.openstack, populating it with your tenant account
- Get your local PC username: $ echo $USER
- Create 2 100GB volumes, called "$USER-lxc" and "$USER-cinder"
- Edit the "default" security group, permitting all ingress traffic(the simpliest case)
```
#!shell
- $ export VAGRANT_OPENSTACK_LOG=debug
- $ VAGRANT_VAGRANTFILE=Vagrantfile.openstack vagrant up --provider=openstack
- $ VAGRANT_VAGRANTFILE=Vagrantfile.openstack vagrant ssh
- $ VAGRANT_VAGRANTFILE=Vagrantfile.openstack vagrant destroy
- $ rm -rf .vagrant
```
