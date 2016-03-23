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
- $ export LOCAL_TMP_DIR="/tmp"
- $ export ANSIBLE_HOST_KEY_CHECKING=False
- $ ansible-playbook -i "localhost ansible_python_interpreter=python," --extra-vars "username=$USER local_tmp_dir=$LOCAL_TMP_DIR" -c local test/playbooks/up.yml
- $ LANG=C ansible-playbook -i $LOCAL_TMP_DIR/inventory --extra-vars "username=centos inventory=$LOCAL_TMP_DIR/inventory containers=$LOCAL_TMP_DIR/containers.yml" test/playbooks/controller.yml

- $ LANG=C ssh -t centos@$(openstack --os-cloud tripleo server show controller01 -c addresses -f value | cut -d ' ' -f 2) "ansible-playbook -i stackforce-ansible/inventory/dynlxc.py --sudo stackforce-ansible/playbooks/create_lxc_containers.yml"
```
IMPORTANT: s/USERNAME/your_username/
example /etc/openstack/clouds.yaml:

```
#!yaml
---
clouds:
  stackforce:
    auth:
      auth_url: "http://192.168.10.7:35357/v3"
      project_name: "admin"
      project_domain_name: default
      user_domain_name: default
      username: "admin"
      password: "PPPGee4soopohsusaki"
    identity_api_version: "3"
    region_name: "RegionOne"
  tripleo:
    auth:
      auth_url: "http://192.168.10.7:35357/v3"
      project_name: "USERNAME"
      project_domain_name: default
      user_domain_name: default
      username: "USERNAME"
      password: "guj3OhV8ub5hauCh"
    identity_api_version: "3"
    region_name: "RegionOne"

```
