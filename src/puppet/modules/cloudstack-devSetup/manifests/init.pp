# Module for building and deploying the simulator.
# This receipe works with centos.

class cloudstack-simulator {
  case $operatingsystem  {
    centos: { include cloudstack::no_selinux }
    redhat: { include cloudstack::no_selinux }
  }
  
  include cloudstack-simulator::ports
  include cloudstack-simulator::files
  include mysql
  include maven
  include java17 

  Class['mysql'] -> Class['maven'] -> Class['java17'] -> Class ['cloudstack-simulator']

  #Seed the syslog enabled log4j
  file {'/root/refreshHost.py':
        source => 'puppet:///cloudstack-simulator/refreshHost.py',
        mode   => 744,
  }
 
  file {'/root/buildAndDeploySimulator.py':
        source => 'puppet:///cloudstack-simulator/buildAndDeploySimulator.py',
        mode   => 744,
  }
  
  file {'/root/.ssh/id_rsa.mgmt':
        source =>  'puppet:///cloudstack-simulator/id_rsa.mgmt',
        owner => root,
        mode => 0600,
   }

  file {'/root/restartMgmtServer.py':
        source => 'puppet:///cloudstack-simulator/restartMgmtServer.py',
        mode   => 744,
  }
 
  file {'/root/.ssh/authorized_keys':
        source => 'puppet:///cloudstack-simulator/authorized_keys',
        owner => root,
        mode   => 0600,
  }
  
  file {'/root/cloud-install-sys-tmplt':
       source =>'puppet:///cloudstack-simulator/cloud-install-sys-tmplt',
       mode   => 744,
  }


  $opt="-XX:MaxPermSize=512m -Xms512m -Xmx1024m -Xdebug -Xrunjdwp:transport=dt_socket,address=8787,server=y,suspend=n -ea:org.apache.cloudstack... -ea:com.cloud..."
  exec {"maven_opts":
      path => "/",
      command => "/bin/echo export MAVEN_OPTS=\'\"$opt\"\' >> /root/.bashrc",
  }
 
  $keytoolPath="/usr/java/jdk1.7.0_45/bin"
  exec {"keytoolPath":
      command => "/bin/echo export PATH=\$PATH:$keytoolPath >> /root/.bashrc",
  }

  $packagelist =  [ 'genisoimage', 'git', 'python-setuptools','java-1.7.0-openjdk-devel','tomcat6','ws-commons-util','jpackage-utils','gcc','glibc-devel','MySQL-python','createrepo', 'rpm-build']
      package { $packagelist:
         ensure  => installed,
  }
 

  package { NetworkManager:
    ensure => absent,
  }

  file { '/root/vhd-util':
    source => 'puppet:///cloudstack-simulator/vhd-util',
    ensure => present,
    owner => 'root',
    mode => 755,
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
   }
    ubuntu, debian: {
      #Still to figure out ubuntu idiosyncracies,
      }
 }

}

class cloudstack-simulator::no_selinux {
  file { '/etc/selinux/config':
    source => 'puppet:///cloudstack/config',
  }
  exec { '/usr/sbin/setenforce 0':
    onlyif => '/usr/sbin/getenforce | /bin/grep Enforcing',
  }
}


class cloudstack-simulator::ports {
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

class cloudstack-simulator::files {
  file { '/etc/sudoers':
    source => 'puppet:///cloudstack/sudoers',
    mode   => 440,
    owner  => root,
    group  => root,
  }

  file { '/etc/hosts':
    content => template('cloudstack/hosts'),
  }

  file { '/root/createtmplt.sh':
     source => 'puppet:///cloudstack-simulator/createtmplt.sh',
     mode   =>  744,
  }

  #  file { '/etc/resolv.conf':
  #  content => template('cloudstack/resolv.conf'),
  #}

  file { '/root/redeploy.sh':
    source  => 'puppet:///cloudstack-simulator/redeploy.sh',
    mode    => 744,
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
