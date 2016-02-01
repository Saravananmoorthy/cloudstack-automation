#Apache CloudStack - infrastructure and nodes
node kvm1 inherits basenode {
  include ssh
  include cloudstack::agent
}

node kvm2 inherits basenode {
  include ssh
  include cloudstack::agent
}

node kvm3 inherits basenode {
  include ssh
  include cloudstack::agent
}
node apache-83-2 inherits basenode {
  include ssh
  include cloudstack::agent
}


node centos-00-16-3e-75-bf-df inherits basenode { 
include nfsclient
include java17
include mysql
include maven
include cloudstack-devSetup }
