import functools
import tempfile

import pytest
from inventory import dynlxc
from mock import MagicMock, call, patch, Mock

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
        cnf = dynlxc.get_config(dynlxc.DEFAULT_CONF)
        cnf.add_section.assert_called_once_with("os")
        calls = [
            call('os', 'inventory_file', None),
            call('os', 'unique_containers_file', None)]
        cnf.set.assert_has_calls(calls)
        cnf.read.assert_called_with("/etc/stackforce/parameters.ini")


def attach_file_from_docstring(clbl):
    """ Adds filename which consits of lines from docstring
    which starts with '>>>' to arguments.
    """

    @functools.wraps(clbl)
    def wrapper(*args, **kwargs):

        with tempfile.NamedTemporaryFile() as fh:
            for l in clbl.__doc__.split('\n'):
                line = l.lstrip()
                if line.startswith('>>>'):
                    fh.write(line[4:] + '\n')
            fh.flush()
            result = clbl(*(args + (fh.name, )), **kwargs)

        return result

    return wrapper


class TestReadInventoryFile(object):

    def test_first(self, inventory_file):
        res = dynlxc.read_inventory_file(inventory_file['file_name'])
        assert res == inventory_file['expect_result']

    @attach_file_from_docstring
    def test_group_vars(self, inventory_file):
        ''' Ansible does not read groupvars from _meta. They should be in
        vars into group. via @dtyzhnenko
        For this:

        >>> cid01-tst ansible_host=192.168.10.5 ansible_user=root
        >>> [compute]
        >>> cid01-tst cinder_disk="/dev/sdb,/dev/sdc"
        >>> [compute:vars]
        >>> compute_virt_type="kvm"

        '''
        res = dynlxc.read_inventory_file(inventory_file)
        assert res['compute']['vars']['compute_virt_type'] == 'kvm'

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
            'groups': {'controller': {'nova': {'count': 2}}},
            'hosts': {'controller01': {
                'cinder_api': {'count': 1},
                'glance': {'count': 1},
                'horizon': {'count': 1},
                'keystone': {'count': 1},
                'mariadb': {'count': 1},
                'memcached': {'count': 1},
                'nova_api': {'count': 1},
                'rabbitmq': {'count': 1},
                'syslog': {'count': 1}
            }}}
        groupnames = [
            dynlxc.get_unique_container_name('nova', 'controller', 1),
            dynlxc.get_unique_container_name('nova', 'controller', 0),
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
        dyngroup = res["_meta"]["groupvars"]["controller"]["lxc_containers"]
        assert sorted(dyngroup.keys()) == sorted(groupnames)
        dynhost = res["_meta"]["hostvars"]["controller01"]["lxc_containers"]
        assert sorted(dynhost) == sorted(hostnames)


class TestListContainersOnHost(object):

    @pytest.mark.skip(reason="It turns out that it is the way it should work")
    def test_call_with_not_existing_host(self):
        with pytest.raises(dynlxc.DynLxcConnectionError):
            dynlxc.list_containers_on_host('notexistsinghost', {})

    @patch('inventory.dynlxc.get_containers_list')
    @patch('inventory.dynlxc.get_container_ip')
    def test_call_for_localhost(self, mock_get_ip, mock_get_list):
        containers = ['container1', 'container2']
        mock_get_list.return_value = containers
        mock_get_ip.return_value = ['127.0.0.1', '10.0.0.1', ]
        result = dynlxc.list_containers_on_host('localhost', 'root', 22, 'nop')
        assert set(result['all']) == set(containers)
        assert 'container1' in result
        assert 'container2' in result
        hostvars = result['_meta']['hostvars']
        assert hostvars['container1']['ansible_host'] == '10.0.0.1'
        assert hostvars['container2']['ansible_host'] == '10.0.0.1'


class TestGetRemoteControllers(object):

    def test_empty(self):
        assert dynlxc.get_remote_controllers({}) == {}
        assert dynlxc.get_remote_controllers(
            {'controller': {}}) == {}
        assert dynlxc.get_remote_controllers({
            'controller': {'hosts': []}}) == {}

    def test_base(self):
        hosts = ['host1', 'host2', 'host3']
        hostvars = {
            'host1': {'ansible_connection': 'remote'},
            'host2': {'ansible_connection': 'local'},
            'host3': {}
        }
        inventory = {
            'controller': {'hosts': hosts},
            '_meta': {'hostvars': hostvars}
        }
        remote = dynlxc.get_remote_controllers(inventory)
        assert 'host1' in remote
        assert 'host2' not in remote
        assert 'host3' in remote


class TestBasicMergeRun(object):

    @attach_file_from_docstring
    def test_simple_inventory(self, inventory_file):
        """ Some empty inventory file
        >>> [controller]
        >>> compute1 ansible_host=10.0.0.1
        """
        self._uniq_containers(inventory_file)

    @attach_file_from_docstring
    def _uniq_containers(self, inventory_file, unique_containers):
        """ Some empty containers conf
            >>> ---
            >>> hosts:
            >>>     compute1:
            >>>         rabbitmq:
            >>>             count: 1
        """
        result = dynlxc.main(inventory_file, unique_containers)
        assert result['all'] == ['compute1', ]
        compute_hostvars = result['_meta']['hostvars']['compute1']
        (key, value), = compute_hostvars['lxc_containers'].items()
        assert key.startswith('rabbit')
        assert compute_hostvars['ansible_host'] == '10.0.0.1'
        assert 'compute1' in result['controller']['hosts']

    @attach_file_from_docstring
    def test_new_containers(self, inventory_file):
        """ Some empty inventory file
        >>> [controller]
        >>> controller01 ansible_host=10.0.0.1
        """
        self._new_uniq_containers(inventory_file)

    @attach_file_from_docstring
    def _new_uniq_containers(self, inventory_file, unique_containers):
        """ Some empty containers conf
            >>> ---
            >>> hosts:
            >>>    controller01:
            >>>        rabbitmq:
            >>>            count: 2
            >>>            size: 3
            >>>            someothervar: 100500
            >>>        mariadb:
            >>>            count: 1
            >>>            size: 10
            >>>            someothervar: 9999
        """
        result = dynlxc.main(inventory_file, unique_containers)
        assert result['all'] == ['controller01', ]
        assert 'controller01' in result['controller']['hosts']
        compute_hostvars = result['_meta']['hostvars']['controller01']
        assert compute_hostvars['ansible_host'] == '10.0.0.1'
        cont1, cont2, cont3, = sorted(compute_hostvars['lxc_containers'])

        container = compute_hostvars['lxc_containers'][cont1]
        assert cont1.startswith('mariadb_container-')
        assert container['name'] == 'mariadb'
        assert container['size'] == 10


def test_parse_args():
    assert dynlxc.parse_args(["--list", ])
    assert dynlxc.parse_args(["--list", '-c', 'test_conf.ini'])


def test_get_containers_list():
    with patch('inventory.dynlxc.subprocess.Popen') as mock_popen:
        mock_rv = Mock()
        mock_rv.stdout.read.return_value = 'test1\ntest2'
        mock_popen.return_value = mock_rv
        result = dynlxc.get_containers_list('localhost', 'root', 22, 'nop')
        assert result == ['test1', 'test2']
        assert mock_popen.call_count == 1


def test_get_container_ip():
    with patch('inventory.dynlxc.subprocess.Popen') as mock_popen:
        mock_rv = Mock()
        mock_rv.stdout.read.return_value = '10.0.0.1\n10.0.0.2'
        mock_popen.return_value = mock_rv
        result = dynlxc.get_container_ip('c1', 'localhost', 'root', 22, 'nop')
        assert result == ['10.0.0.1', '10.0.0.2']
        assert mock_popen.call_count == 1
