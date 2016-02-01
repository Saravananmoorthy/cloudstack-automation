#Apache Cloudstack - Module for the Management Server and Agent
#

class kvm-agent {
  $netmask='255.255.255.192'

  case $operatingsystem  {
    centos: { include cloudstack::no_selinux }
    redhat: { include cloudstack::no_selinux }
  }
  include cloudstack::repo
  include cloudstack::files

  case $operatingsystem {
    centos,redhat : {
      $packagelist =  [ 'cloudstack-agent', 'qemu-kvm', 'expect' ]
      package { $packagelist:
         ensure  => installed,
         require => Yumrepo['cstemp'],
      }
      service { 'libvirtd':
        ensure => running,
        require => Package['qemu-kvm'],
      }
    }
    ubuntu, debian: {
      $packagelist =  [ 'cloudstack-agent', 'qemu-kvm' ]
      package { $packagelist:
         ensure  => latest,
         require => [File['/etc/apt/sources.list.d/cloudstack.list'], Exec['apt-get update']],
      }
    }
    fedora : {
    }
  }

  package { NetworkManager:
    ensure => absent,
  }

  case $operatingsystem {
    centos, redhat : {
      exec {"/bin/echo 'IPADDR=$ipaddress_em1' >> /etc/sysconfig/network-scripts/ifcfg-em1":
        path   => "/etc/sysconfig/network-scripts/",
        onlyif => '/bin/grep -vq IPADDR /etc/sysconfig/network-scripts/ifcfg-em1'
      }

      exec {"/bin/echo 'NETMASK=$netmask' >> /etc/sysconfig/network-scripts/ifcfg-em1":
        path => "/etc/sysconfig/network-scripts/",
        onlyif => '/bin/grep -vq NETMASK /etc/sysconfig/network-scripts/ifcfg-em1'
      }

      exec {"/bin/sed -i 's/\"dhcp\"/\"static\"/g' /etc/sysconfig/network-scripts/ifcfg-em*":
      }

      exec {"/bin/sed -i '/NM_CONTROLLED=/d' /etc/sysconfig/network-scripts/ifcfg-*":
        notify => Notify['networkmanager'],
      }

      notify { 'networkmanager':
        message => 'NM_Controlled set to off'
      }

      file {'/etc/sysconfig/network-scripts/ifcfg-eth0':
        ensure => absent,
      }

      file { '/etc/cloudstack/agent/agent.properties':
        source  => 'puppet:///cloudstack/agent.properties',
        mode    => 744,
        require => Package['cloudstack-agent'],
      }

      file {'/etc/cloudstack/agent/log4j-cloud.xml':
        source => 'puppet:///cloudstack/log4j-agent.xml',
        mode   => 744,
        require => File['/etc/cloudstack/agent/agent.properties'],
      }
    }
    ubuntu, debian: {
      #Still to figure out ubuntu idiosyncracies
      }
  }
}

class kvm-agent::no_selinux {
  file { '/etc/selinux/config':
    source => 'puppet:///cloudstack/config',
  }
  exec { '/usr/sbin/setenforce 0':
    onlyif => '/usr/sbin/getenforce | /bin/grep Enforcing',
  }
}

class kvm-agent::repo {
  #TODO: Repo replace from nodes.pp
  $yumrepo = '/tmp/cloudstack'
  #Wido D. Hollander's repo
  $aptrepo = 'http://cloudstack.apt-get.eu/ubuntu'
  $aptkey = 'http://cloudstack.apt-get.eu/release.asc'

  case $operatingsystem {
    centos,redhat : {
      yumrepo { 'cstemp':
        baseurl  => 'file:///tmp/cloudstack',
        enabled  => 1,
        gpgcheck => 0,
        name     => 'cstemp',
      	require => File['/tmp/cloudstack'],
      }
    }
    ubuntu, debian: {
      file { '/etc/apt/sources.list.d/cloudstack.list':
        ensure  => present,
        content => 'deb ${aptrepo} ${lsbdistcodename} 4.0',
      }
      exec { 'wget -O - ${aptkey} | apt-key add -': 
        path => ['/usr/bin', '/bin'],
      }
      exec { 'apt-get update':
        path => ['/usr/bin', '/bin'],
      }
    }
    fedora : {
    }
  }
}

class kvm-agent::ports {
  firewall { '010 integrationport':
    proto     => 'tcp',
    dport     => 8096,
    action    => accept,
  }
  firewall { '011 apiport':
    proto     => 'tcp',
    dport     => 8080,
    action    => accept,
  }
  firewall { '012 clusterport':
    proto     => 'tcp',
    dport     => 9090,
    action    => accept,
  }
  firewall { '013 agentport':
    proto     => 'tcp',
    dport     => 8250,
    action    => accept,
  }

  firewall { '014 mysqlport':
    proto  => 'tcp',
    dport  => 3306,
    action => accept,
  }

  firewall { '015 nfsudp':
    proto  => 'udp',
    dport  => 2049,
    action => accept,
  }

  firewall { '016 nfstcp':
    proto  => 'tcp',
    dport  => 2049,
    action => accept,
  }
}

class kvm-agent::files {
  file { '/etc/sudoers':
    source => 'puppet:///cloudstack/sudoers',
    mode   => 440,
    owner  => root,
    group  => root,
  }

  file { '/etc/hosts':
    content => template('cloudstack/hosts'),
  }

  case $operatingsystem {
    redhat,centos: { 
    file { '/etc/sysconfig/network':
      content => template('cloudstack/network'),
    }
    }
    default: {}
  }
}
