import pytest
from mock import MagicMock, patch, call

from inventory import dynlxc


inventories = [
    {
        "file_name": "test/unit/files/inventory_vagrant",
        "expect_result": {
            'ungrouped': {'hosts': [], 'vars': {}},
            'all': [u'localhost'],
            u'compute': {'hosts': [u'localhost'], 'vars': {}},
            u'controller': {'hosts': [u'localhost'], 'vars': {}},
            '_meta': {
                'hostvars': {u'localhost': {
                    u'cinder_disk': u'/dev/sdc',
                    u'neutron_physical_interface_mappings':
                        u'vlan:enp0s8,external:enp0s3',
                    u'ansible_connection': u'local'}}}}
    },
    {
        "file_name": "test/unit/files/tst_two",
        "expect_result": {
            'all': [u'cid01-tst', u'cid02-tst', u'cid03-tst'],
            'ungrouped': {
                'hosts': [u'cid01-tst', u'cid02-tst', u'cid03-tst'],
                'vars': {}},
            u'baremetal': {
                'hosts': [u'cid01-tst', u'cid02-tst', u'cid03-tst'],
                'vars': {}},
            u'compute': {
                'hosts': [u'cid01-tst', u'cid02-tst'],
                'vars': {
                    u'compute_virt_type': u"kvm",
                    u'os_rabbit_port': 5672,
                    u'cinder_disk': u"/dev/sdb"}},
            u'controller': {
                'hosts': [u'cid03-tst'], 'vars': {}},
            '_meta': {
                'hostvars': {
                    u'cid01-tst': {
                        u'cinder_disk': u'/dev/sdb,/dev/sdc',
                        u'ansible_host': u'192.168.10.5',
                        u'ansible_user': u'root'},
                    u'cid02-tst': {
                        u'cinder_disk': u'/dev/sdb,/dev/sdc',
                        u'ansible_host': u'192.168.10.6',
                        u'ansible_user': u'root'},
                    u'cid03-tst': {
                        u'ansible_connection': u'local'}
                }
            }
        }
    }
]


@pytest.fixture(params=inventories)
def inventory_file(request):
    """Return path to test inventory file"""
    return request.param


class TestGetConfig(object):

    @patch('ConfigParser.ConfigParser')
    def test_config(self, mock_class):
        cnf = dynlxc.get_config()
        cnf.add_section.assert_called_once_with("os")
        calls = [
            call('os', 'inventory_file', None),
            call('os', 'unique_containers_file', None)]
        cnf.set.assert_has_calls(calls)
        cnf.read.assert_called_with("/etc/stackforce/parameters.ini")


class TestReadInventoryFile(object):

    def test_first(self, inventory_file):
        res = dynlxc.read_inventory_file(inventory_file['file_name'])
        assert res == inventory_file['expect_result']

    @pytest.mark.skip(reason="non working mockups")
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
            "neutron_physical_interface_mappings": "vlan:enp0s8,"
                                                   "external:enp0s3",
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
            res = dynlxc.read_inventory_file(inventory_path)
            mocked_dl.assert_called_once_with()
            assert "all" in res
            assert "_meta" in res
            assert "hostvars" in res["_meta"]
            assert "groupvars" in res["_meta"]
            assert "localhost" in res["all"]
            assert "compute" in res
            assert "localhost" in res["compute"]["hosts"]

    @pytest.mark.skip(reason="non working mockups")
    def test_mocked_dl(self):
        mocked_dl = MagicMock()
        mocked_dl._get_file_contents = MagicMock(return_value=("None", True))
        inventory_path = "inventory_test_path"
        with patch('inventory.dynlxc.DataLoader', mocked_dl):
            res = dynlxc.read_inventory_file(inventory_path)
            mocked_dl._get_file_contents.assert_called_with(inventory_path)
            assert res


class TestListContainers(object):
    def test_getting_list_of_containers(self):
        mocked_lxc_list_containers = MagicMock()
        mocked_lxc_list_containers.return_value = [
            "nova_api_container-2f22c87b",
            "stackforce_base_container"]
        mocked_lxc_container = MagicMock()
        get_interfaces = MagicMock()
        get_interfaces.side_effect = [("eth0", "lo"), False]
        mocked_lxc_container.get_interfaces = get_interfaces
        with patch("lxc.list_containers", mocked_lxc_list_containers):
            with patch("lxc.Container", mocked_lxc_container):
                res = dynlxc.list_containers()
                assert res["nova"] == \
                    {'hosts': ['nova_api_container-2f22c87b']}
                assert res["all"] == \
                    ['nova_api_container-2f22c87b',
                     'stackforce_base_container']


class TestAddExtravars(object):
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
                              "remote": {}}}}
        res = dynlxc.add_extravars(res_mockup, {"extravar": True})
        for host in res["_meta"]["hostvars"]:
            assert res["_meta"]["hostvars"][host]["extravar"]


class TestMergeResults(object):
    def test_base(self):
        res_a = {"all": ["localhost"],
                 "local": {"hosts": ["localhost"],
                           "vars": {"ansible_connection": "local"}},
                 "_meta": {"groupvars": {"local": []},
                           "hostvars": {"localhost": {"os_debug": True}}}}
        res_b = {"all": ["server"],
                 "remote": {"hosts": ["server"],
                            "vars": {"ansible_host": "192.168.254.1"}},
                 "_meta": {"groupvars": {"remote": []},
                           "hostvars": {"server": {"os_debug": False}}}}
        res = dynlxc.merge_results(res_a, res_b)
        assert res["all"] == ["localhost", "server"]
        assert res["_meta"]["hostvars"]["localhost"]["os_debug"]
        assert not res["_meta"]["hostvars"]["server"]["os_debug"]


class TestAddLxcContainersToInventory(object):
    def test_first(self):
        inv = {
            '_meta': {
                'groupvars': {'all': {},
                              u'compute': {},
                              u'controller': {
                                  'lxc_containers': ['nova_01629964',
                                                     'nova_83786ee8']},
                              'ungrouped': {}},
                'hostvars': {'controller01': {},
                             u'localhost': {
                                 u'ansible_connection': u'local',
                                 u'cinder_disk': u'/dev/sdc',
                                 u'neutron_physical_interface_mappings':
                                     u'vlan:enp0s8,external:enp0s3'}}},
            'all': [u'localhost'],
            u'compute': {'hosts': [u'localhost'], 'vars': {}},
            u'controller': {'hosts': [u'localhost'], 'vars': {}},
            'ungrouped': {'hosts': [], 'vars': {}}}
        yml_cnf = {
            'groups': {'controller': {'nova': 2}},
            'hosts': {'controller01': {'cinder_api': 1,
                                       'glance': 1,
                                       'horizon': 1,
                                       'keystone': 1,
                                       'mariadb': 1,
                                       'memcached': 1,
                                       'nova_api': 1,
                                       'rabbitmq': 1,
                                       'syslog': 1}}}
        groupnames = [
            dynlxc.get_unique_container_name('nova', 'controller', 0),
            dynlxc.get_unique_container_name('nova', 'controller', 1),
        ]
        hostnames = [
            dynlxc.get_unique_container_name('cinder_api', 'controller01', 0),
            dynlxc.get_unique_container_name('glance', 'controller01', 0),
            dynlxc.get_unique_container_name('horizon', 'controller01', 0),
            dynlxc.get_unique_container_name('keystone', 'controller01', 0),
            dynlxc.get_unique_container_name('mariadb', 'controller01', 0),
            dynlxc.get_unique_container_name('memcached', 'controller01', 0),
            dynlxc.get_unique_container_name('nova_api', 'controller01', 0),
            dynlxc.get_unique_container_name('rabbitmq', 'controller01', 0),
            dynlxc.get_unique_container_name('syslog', 'controller01', 0),
        ]
        res = dynlxc.add_var_lxc_containers_to_controllers(inv, yml_cnf)
        assert res["_meta"]["groupvars"]["controller"]["lxc_containers"] == \
            groupnames
        assert sorted(
            res["_meta"]["hostvars"]["controller01"]["lxc_containers"]) == \
            sorted(hostnames)
