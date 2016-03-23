#!/bin/bash

set -e
STACKFORCE_USERNAME=$1
if [ -z "$STACKFORCE_USERNAME" ]; then
  echo "Error: Cloud username must be provided as first parameter"
  exit 1
fi
source .venv/bin/activate
pip install -r requirements.txt
export LOCAL_TMP_DIR="/tmp"
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -i "localhost ansible_python_interpreter=python," --extra-vars username=$STACKFORCE_USERNAME -c local test/playbooks/up.yml
LANG=C ansible-playbook -i /tmp/inventory --extra-vars 'username=centos inventory=/tmp/inventory containers=/tmp/containers.yml' test/playbooks/controller.yml
LANG=C ssh -t centos@$(openstack --os-cloud tripleo server show controller01 -c addresses -f value | cut -d ' ' -f 2) "ansible-playbook -i stackforce-ansible/inventory/dynlxc.py --sudo stackforce-ansible/playbooks/stackforce.yml"
LANG=C ssh -t centos@$(openstack --os-cloud tripleo server show controller01 -c addresses -f value | cut -d ' ' -f 2) "ansible-playbook -i stackforce-ansible/inventory/dynlxc.py --sudo stackforce-ansible/playbooks/create_lxc_containers.yml"

