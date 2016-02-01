class java17 () {	
   
  file {'/opt/jdk-7u45-linux-x64.rpm':
        source => 'puppet:///java17/jdk-7u45-linux-x64.rpm',
        mode   => 744,
  } 

 exec { 'java-install':
      command => "rpm -Uvh /opt/jdk-7u45-linux-x64.rpm",
    }

  file { '/opt/alternatives.sh':
     source => 'puppet:///java17/alternatives.sh', 
     mode => 744,
     require => Exec['java-install'],
  }

  exec { 'run-alternatives.sh':
      command => "sh /opt/alternatives.sh",
      require => Exec['java-install'], 
   }
  
  exec {'java_home':
      command => "echo 'export JAVA_HOME=/usr/java/jdk1.7.0_45' >> /root/.bash_profile"
  }
 
}

