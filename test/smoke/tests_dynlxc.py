import json
import os
from collections import namedtuple

import yaml
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.vars import VariableManager
from inventory import dynlxc
from mock import Mock, patch


class TestAllInventory(object):

    @classmethod
    def setup_class(cls):
        cls.popen_patcher = patch('inventory.dynlxc.subprocess.Popen')
        cls.mock_popen = cls.popen_patcher.start()

        cls.mock_rv = Mock()
        cls.mock_rv.returncode = 0
        cls.mock_popen.return_value = cls.mock_rv
        cls.mock_rv.stdout.read.return_value = ''

        Options = namedtuple(
            'Options', ['listtags', 'listtasks', 'listhosts', 'syntax',
                        'connection', 'module_path', 'forks', 'remote_user',
                        'private_key_file', 'ssh_common_args',
                        'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args',
                        'become', 'become_method', 'become_user', 'verbosity',
                        'check'])
        cls.options = Options(listtags=False, listtasks=False, listhosts=False,
                              syntax=False, connection='ssh', module_path=None,
                              forks=100, remote_user='slotlocker',
                              private_key_file=None, ssh_common_args=None,
                              ssh_extra_args=None, sftp_extra_args=None,
                              scp_extra_args=None, become=True,
                              become_method=None, become_user='root',
                              verbosity=None, check=True)

    @classmethod
    def teardown_class(cls):
        cls.popen_patcher.stop()

    def test_base(self):
        test_inv_dir = 'test/inventory'
        for inv in os.listdir(test_inv_dir):
            print "Processing ", inv
            res = dynlxc.main(os.path.join(test_inv_dir, inv), '')

            variable_manager = VariableManager()
            loader = DataLoader()
            self.mock_rv.communicate.return_value = [
                json.dumps(res), 'mocked_err']
            try:
                inventory = Inventory(
                    loader=loader,
                    variable_manager=variable_manager,
                    host_list='inventory/dynlxc.py'
                )
            except Exception as err:
                raise Exception("Inventory file {0} processing result '{1}' "
                                "failed with {2}".format(inv, res, err))
            variable_manager.set_inventory(inventory)

            play_source = dict(name="Ansible Play", hosts='localhost',
                               gather_facts='no')

            playbook = os.path.abspath(os.path.join(test_inv_dir,
                                       '../playbooks', inv))
            if os.path.isfile(playbook):
                with open(playbook) as fh:
                    real_playbook = yaml.load(fh)[0]
                    play_source.update(real_playbook)

            play = Play().load(play_source, variable_manager=variable_manager,
                               loader=loader)
            tqm = None
            try:
                tqm = TaskQueueManager(
                    inventory=inventory,
                    variable_manager=variable_manager,
                    loader=loader,
                    options=self.options,
                    passwords=None,
                    stdout_callback='default',
                )
                result = tqm.run(play)
                assert result == 0, ("Ansible playbook exitcode "
                                     "different from 0")
            finally:
                if tqm is not None:
                    tqm.cleanup()
