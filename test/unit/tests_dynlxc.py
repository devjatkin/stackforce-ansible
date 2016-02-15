import unittest
from inventory.dynlxc import get_config, read_inventory_file, list_containers, add_extravars


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
                      "local": ["localhost"],
                      "remote": ["server"],
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