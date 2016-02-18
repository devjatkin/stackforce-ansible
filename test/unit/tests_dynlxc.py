import unittest
from mock import MagicMock, patch
from inventory.dynlxc import get_config, read_inventory_file, list_containers, add_extravars, merge_results


class TestGetConfig(unittest.TestCase):
    @patch('ConfigParser.ConfigParser')
    def test_config(self, mock_class):
        cnf = get_config()
        cnf.add_section.assert_called_with("os")
        cnf.set.assert_called_with("os", "inventory_file", None)
        cnf.read.assert_called_with("/etc/stackforce/parameters.ini")


class TestReadInventoryFile(unittest.TestCase):
    @unittest.skip("non working mockups")
    def test_base(self):
        class MockGroup(MagicMock):
            def __init__(self, name):
                super(MockGroup, self).__init__()
                self.name = name
            hosts = []
            vars = {}

            def __repr__(self):
                return str(self.name)

        group_all = MockGroup("all")
        compute = MockGroup("compute")
        controller = MockGroup("controller")
        ungrouped = MockGroup("ungrouped")
        group_all.hosts = ['localhost']
        compute.hosts = ['localhost']
        compute.vars = {'localhost': {
            "ansible_connection": "local",
            "neutron_physical_interface_mappings": "vlan:enp0s8,external:enp0s3",
            "cinder_disk": "/dev/sdc"}}
        controller.hosts = ['localhost']
        controller.vars = {'localhost': {
            "ansible_connection": "local"
        }}
        mocked_inv = MagicMock()
        mocked_inv.groups = {'all': group_all,
                             'compute': compute,
                             'controller': controller,
                             'ungrouped': ungrouped}
        mocked_dl = MagicMock()
        inventory_path = "NonePath"
        with patch.multiple('inventory.dynlxc', InventoryParser=mocked_inv,
                            DataLoader=mocked_dl):
            res = read_inventory_file(inventory_path)
            mocked_dl.assert_called_once_with()
            self.assertIn("all", res)
            self.assertIn("_meta", res)
            self.assertIn("hostvars", res["_meta"])
            self.assertIn("groupvars", res["_meta"])
            self.assertIn("localhost", res["all"])
            self.assertIn("compute", res)
            self.assertIn("localhost", res["compute"]["hosts"])

    @unittest.skip("non working mockups")
    def test_mocked_dl(self):
        mocked_dl = MagicMock()
        mocked_dl._get_file_contents = MagicMock(return_value=("None", True))
        inventory_path = "inventory_test_path"
        # with patch.multiple('inventory.dynlxc', DataLoader=mocked_dl):
        with patch('inventory.dynlxc.DataLoader', mocked_dl):
            res = read_inventory_file(inventory_path)
            mocked_dl._get_file_contents.assert_called_with(inventory_path)

class TestListContainers(unittest.TestCase):
    def test_base(self):
        res = list_containers()
        self.assertIn("all", res)
        self.assertIn("_meta", res)
        self.assertIn("hostvars", res["_meta"])
        self.assertNotIn("groupvars", res["_meta"])
        self.assertNotIn("localhost", res["all"])


class TestAddExtravars(unittest.TestCase):
    def test_base(self):
        res_mockup = {"all": ["localhost", "server"],
                      "local": {"hosts": ["localhost"]},
                      "remote": {"hosts": ["server"]},
                      "_meta": {"hostvars": {
                                    "localhost": {},
                                    "server": {}
                                },
                                "groupvars:": {
                                    "local": {},
                                    "remote": {}
                                }}}
        res = add_extravars(res_mockup, {"extravar": True})
        for host in res["_meta"]["hostvars"]:
            self.assertTrue(res["_meta"]["hostvars"][host]["extravar"])


class TestMergeResults(unittest.TestCase):
    def test_base(self):
        res_a = {"all": ["localhost"],
                 "local": {"hosts": ["localhost"],
                           "vars": {"ansible_connection": "local"}},
                 "_meta":{"groupvars":{"local":[]},
                          "hostvars":{"localhost": {"os_debug": True}}}}
        res_b = {"all": ["server"],
                 "remote": {"hosts": ["server"],
                            "vars": {"ansible_ssh_host": "192.168.254.1"}},
                 "_meta": {"groupvars": {"remote": []},
                           "hostvars": {"server": {"os_debug": False}}}}
        res = merge_results(res_a, res_b)
        self.assertEqual(res["all"], ["localhost", "server"])
        self.assertTrue(res["_meta"]["hostvars"]["localhost"]["os_debug"])
        self.assertFalse(res["_meta"]["hostvars"]["server"]["os_debug"])


