# Class: maven::maven
#
# A puppet recipe to install Apache Maven
#
# Parameters:
#   - $version:
#         Maven version.
#
# Requires:
#   Java package installed.
#
# Sample Usage:
#   class {'maven::maven':
#     version => "3.0.5",
#   }
#

class maven ( $version = '3.0.5' ) {	
    
    include wget  
    $archive = "/tmp/apache-maven-${version}-bin.tar.gz" 
 
    wget::fetch { 'fetch-maven':
        source      => "http://archive.apache.org/dist/maven/binaries/apache-maven-${version}-bin.tar.gz",
        destination => $archive,
        before      => Exec['maven-untar'],
      }
   
    exec { 'maven-untar':
      command => "tar -xf /tmp/apache-maven-${version}-bin.tar.gz",
      cwd     => '/opt',
      creates => "/opt/apache-maven-${version}",
      path    => ['/bin','/usr/bin'],
    }

    file { '/usr/bin/mvn':
      ensure  => link,
      target  => "/opt/apache-maven-${version}/bin/mvn",
      require => Exec['maven-untar'],
    } ->
    file { '/usr/local/bin/mvn':
      ensure  => absent,
    }
    file {'maven-proxy':
        source => 'puppet:///maven/maven_proxy.sh',
        path => "/opt/apache-maven-${version}/conf/maven_proxy.sh",
        mode   => 744,
        require => Exec['maven-untar'],
  }
  exec { 'set-proxy':
      command => "sh /opt/apache-maven-${version}/conf/maven_proxy.sh",
      require => File['maven-proxy'],
    }
}

