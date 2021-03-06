# -*- mode: ruby -*-
# vi: set ft=ruby :

BOX_NAME = ENV['VAGRANT_BOX_NAME'] || 'bento/centos-7.2'

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = BOX_NAME

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 9000, host: 9000
  config.vm.network "forwarded_port", guest: 6080, host: 6080
  config.vm.network "forwarded_port", guest: 8500, host: 8500
  config.vm.network "forwarded_port", guest: 7400, host: 7400
  config.vm.network "forwarded_port", guest: 7500, host: 7500
  config.vm.network "forwarded_port", guest: 7600, host: 7600

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  VAGRANT_ROOT = File.dirname(File.expand_path(__FILE__))
  config.vm.provider "virtualbox" do |vb|
    file_to_disk = File.join(VAGRANT_ROOT, '.vagrant/lvm_containersi.vdi')
    unless File.exist?(file_to_disk)
      vb.customize ['createhd', '--filename', file_to_disk, '--size', 100 * 1024]
    end
    vb.customize ['storageattach', :id, '--storagectl', 'SATA Controller', '--port', 1, '--device', 0, '--type', 'hdd', '--medium', file_to_disk]
    file_to_disk_cinder = File.join(VAGRANT_ROOT, '.vagrant/lvm_cinder.vdi')
    unless File.exist?(file_to_disk_cinder)
      vb.customize ['createhd', '--filename', file_to_disk_cinder, '--size', 100 * 1024]
    end
    vb.customize ['storageattach', :id, '--storagectl', 'SATA Controller', '--port', 2, '--device', 0, '--type', 'hdd', '--medium', file_to_disk_cinder]
    # Customize the amount of memory on the VM:
    vb.memory = "4096"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end
  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    sudo yum install -y epel-release
    sudo yum install -y http://repo.cloudlinux.com/stackforce/x86_64/stackforce-release-1-1.el7.noarch.rpm
    sudo yum install -y ansible python2-lxc --enablerepo='stackforce-testing'
    ansible-playbook -i /vagrant/test/inventory/vagrant -c local --extra-vars 'username=vagrant inventory=/vagrant/test/inventory/vagrant containers=/vagrant/playbooks/files/allinone_containers.yml' /vagrant/test/playbooks/vagrant.yml
    ansible-playbook -i "/vagrant/inventory/dynlxc.py" -c local --extra-vars 'lxc_container_user_name=vagrant lxc_disk=/dev/sdb' /vagrant/playbooks/create_lxc_containers.yml
    sudo -u vagrant ansible-playbook -i /vagrant/inventory/dynlxc.py --sudo /vagrant/playbooks/stackforce.yml
    ansible-playbook -i "localhost," -c local /vagrant/test/playbooks/install_bats.yml
    bats /vagrant/test/integration/default/bats/*.bats
  SHELL
end
