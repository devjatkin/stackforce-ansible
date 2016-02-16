import unittest
from inventory.dynlxc import get_config, read_inventory_file, list_containers, add_extravars, merge_results


class TestGetConfig(unittest.TestCase):
    def test_config(self):
        config = get_config()
        self.assertTrue(config.has_section("os"))
        self.assertTrue(config.has_section("os_logs"))
        self.assertTrue(config.has_section("public"))
        self.assertTrue(config.has_option("public", "address"))
        self.assertTrue(config.has_option("os", "rabbit_port"))
        self.assertTrue(config.has_option("os_logs", "verbose"))
        self.assertTrue(config.has_option("os_logs", "debug"))


class TestReadInventoryFile(unittest.TestCase):
    def test_base(self):
        res = read_inventory_file("test/inventory/vagrant")
        self.assertIn("all", res)
        self.assertIn("_meta", res)
        self.assertIn("hostvars", res["_meta"])
        self.assertIn("groupvars", res["_meta"])
        self.assertIn("localhost", res["all"])
        self.assertIn("compute", res)
        self.assertIn("localhost", res["compute"]["hosts"])


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


