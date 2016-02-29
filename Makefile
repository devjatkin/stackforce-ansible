.PHONY: all test clean
test:
	./bin/check_venv.sh
	ansible-playbook --syntax-check --list-tasks -i inventory/localhost playbooks/*.yml
	ansible-lint --version
	ansible-lint playbooks/*yml --exclude playbooks/roles/mysql/
	nose2
