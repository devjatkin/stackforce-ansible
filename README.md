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
- $ source .venv/bin/activate
- $ pip install -r requirements.txt
- $ ansible-playbook -i "localhost ansible_python_interpreter=python," -c local test/playbooks/up.yml
- $ LANG=C ansible-playbook -i /tmp/inventory --extra-vars 'username=centos inventory=/tmp/inventory containers=/tmp/containers.yml' test/playbooks/controller.yml
- $ LANG=C ssh -t centos@192.168.10.103 "ansible-playbook -i stackforce-ansible/inventory/dynlxc.py --sudo stackforce-ansible/playbooks/create_lxc_containers.yml"
```
