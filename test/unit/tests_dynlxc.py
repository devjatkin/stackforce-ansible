import unittest
from inventory.dynlxc import result, config


class TestInventory(unittest.TestCase):
    def test_common_result(self):
        self.assertIn("all", result)
        self.assertIn("_meta", result)
        self.assertIn("hostvars", result["_meta"])
        self.assertIn("groupvars", result["_meta"])

    def test_inventory_file_vagrant(self):
        # self.assertIn("localhost", result["all"])
        self.assertIn("compute", result)
        self.assertIn("localhost", result["compute"]["hosts"])
        self.assertEqual(result["compute"]["vars"]["os_debug"], "true")
        self.assertEqual(result["compute"]["vars"]["os_rabbit_port"], "5672")
        self.assertEqual(result["compute"]["vars"]["os_verbose"], "true")

    def test_config(self):
        self.assertTrue(config.has_section("os"))
        self.assertTrue(config.has_section("os_logs"))
        self.assertTrue(config.has_section("public"))
        self.assertTrue(config.has_option("public", "address"))
        self.assertTrue(config.has_option("os", "rabbit_port"))
        self.assertTrue(config.has_option("os_logs", "verbose"))
        self.assertTrue(config.has_option("os_logs", "debug"))
