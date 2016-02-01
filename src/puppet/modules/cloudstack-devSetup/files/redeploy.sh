#!/bin/bash
#set -x
usage() {
  printf "Usage: %s:\n
	[-s nfs path to secondary storage <nfs-server:/export/path> ] [-u url to system template] [-h hypervisor type (kvm|xen|vmware) ] [-p <path to dbProperties file>]\n" $(basename $0) >&2

  printf "\nThe -s flag will clean the secondary path and install the specified
hypervisor's system template as per -h, if -h is not given then xenserver is
assumed\n"	

}

failed() {
	exit $1
}

#flags
sflag=0
hflag=0
uflag=0

VERSION="1.0.1"
echo "Redeploy Version: $VERSION"

#some defaults
spath='nfs2.lab.vmops.com:/export/home/bvt/secondary'

xensysvmurl='http://10.147.28.7/templates/4.3/systemvm64template-2014-01-14-master-xen.vhd.bz2'
kvmsysvmurl='http://10.147.28.7/templates/4.3/systemvm64template-2014-01-14-master-vmware.ova'
vmwaresysvmurl='http://10.147.28.7/templates/4.3/systemvm64template-2014-01-14-master-kvm.qcow2.bz2'

hypervisor='xen'
sysvmurl='http://download.cloud.com/templates/acton/acton-systemvm-02062012.vhd.bz2'

systemvm_seeder='/root/cloud-install-sys-tmplt'
pathToDbpropertiesFile='/automation/cloudstack/client/target/generated-webapp/WEB-INF/classes/db.properties'

while getopts 'u:s:h:p' OPTION
do
  case $OPTION in
  s)    sflag=1
		spath="$OPTARG"
  		;;
  h)    hflag=1
		hypervisor="$OPTARG"
		;;
  u)    uflag=1
		sysvmurl="$OPTARG"
		;;
  p)    pflag=1
                pathToDbpropertiesFile="$OPTARG"
                ;;
  ?)	usage
		failed 2
		;;
  esac
done

if [[ $uflag -eq 0 ]]; then
    case $hypervisor in
    xen) sysvmurl=$xensysvmurl
         ;;
    kvm) sysvmurl=$kvmsysvmurl
         ;;
    vmware) sysvmurl=$vmwaresysvmurl
         ;;
    esac
fi

if [[ -e /etc/redhat-release ]]
then 
	cat /etc/redhat-release
else
	echo "script works on rpm environments only"
	exit 5
fi

#check if process is running
proc=$(ps aux | grep cloud | wc -l)
if [[ $proc -lt 2 ]]
then
        echo "Cloud process not running"
        if [[ -e /var/run/cloudstack-management.pid ]]
        then
            rm -f /var/run/cloudstack-management.pid
        fi
else
        #stop service
        service cloudstack-management stop
fi

#TODO: archive old logs
#refresh log state 
cat /dev/null > /automation/cloudstack/vmops.log
cat /dev/null > /automation/cloudstack/api.log

#replace disk size reqd to 1GB max
sed -i 's/DISKSPACE=5120000/DISKSPACE=20000/g' $systemvm_seeder

if [[ "$uflag" != "1" && "$hypervisor" != "xenserver" ]]
then
    echo "URL of systemvm template is reqd."
    usage
fi

if [[ "$sflag" == "1" ]]
then
	mkdir -p /tmp/secondary
	mount -t nfs $spath /tmp/secondary
	rm -rf /tmp/secondary/*

	if [[ "$hflag" == "1" && "$hypervisor" == "xenserver" ]]
	then
		bash -x $systemvm_seeder -m /tmp/secondary/ -u $sysvmurl -h xenserver -p $pathToDbpropertiesFile 
	elif [[ "$hflag" == "1" && "$hypervisor" == "kvm" ]]
	then
		bash -x $systemvm_seeder -m /tmp/secondary/ -u $sysvmurl -h kvm -p $pathToDbpropertiesFile
	elif [[ "$hflag" == "1" && "$hypervisor" == "vmware" ]]
	then
		bash -x $systemvm_seeder -m /tmp/secondary/ -u $sysvmurl -h vmware -p $pathToDbpropertiesFile
	else
		bash -x $systemvm_seeder -m /tmp/secondary/ -u $sysvmurl -h xenserver -p $pathToDbpropertiesFile
	fi
	umount /tmp/secondary
else
    echo "please provide the nfs secondary storage path where templates are stored"
    usage
fi
