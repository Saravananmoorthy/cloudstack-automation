set -x 

#'/automation/virtenv/00-16-3e-17-43-25/16'
BASEDIR=$1 
#'xenserver'
hypervisor=$2 
WORKSPACE=$3 
#'/automation/jenkins/workspace/report_generator_16_zone-xen_XenServer.xml'
buildNumber=$4 
#'16'
SUITE_PATH=$5 
#'/automation/virtenv/00-16-3e-17-43-25/16/xenserver'
MOUNTPT='/mnt/test_result_archive'
version=$6 
#'master'
MGMT_SVR=$7 
#'10.147.28.221'

mkdir -p $WORKSPACE/${hypervisor}/reports/
rm -rf $WORKSPACE/${hypervisor}/reports/*
for file in $(find $SUITE_PATH -name "test_*.xml")
do  
cp -f $file $WORKSPACE/${hypervisor}/reports/
suite=$(echo $file | sed -e s~.*reports/~~ -e s~\.xml~~g)
rm -rf $WORKSPACE/${hypervisor}/reports/$suite
rm -rf $WORKSPACE/${hypervisor}/reports/$suite.zip
suite_path=`echo $file | sed -e s/reports.*//`
chmod -R a+x $suite_path
path='results/MarvinLogs'
log_folder=$(ls -ltr $suite_path$path | tail -1 | grep -o "test_.*")
mkdir -p $WORKSPACE/${hypervisor}/reports/$suite
cp -f $suite_path/results/MarvinLogs/$log_folder/* $WORKSPACE/${hypervisor}/reports/$suite
cp -f $file $WORKSPACE/${hypervisor}/reports/$suite
zip -rj $WORKSPACE/${hypervisor}/reports/${suite}.zip $WORKSPACE/${hypervisor}/reports/$suite
done
PREFIX=${hypervisor}__
#the path mentioned below should be created and mounted on the cobbler VM first time.
#NFS_PATH=“/automation/test_result_archive” MOUNTPT=“/mnt/test_result_archive HYP=${hypervisor}
#create dir on NFS with CS version and hypervisor mkdir -p $MOUNTPT/$version/$HYP
#collect test_run logs for each suite
mkdir -p $WORKSPACE/tmp
mkdir -p $MOUNTPT/$version/$buildNumber/$hypervisor/
find $WORKSPACE/${hypervisor}/reports -iname "*.zip" -exec zip -j $WORKSPACE/tmp/test_result.zip {} \;
#zip $suite.xml into test_results.zip rm -rf /tmp/test_results.*
#find $WORKSPACE -iname 'test_*.xml' -exec zip -j $WORKSPACE/tmp/test_results.zip {} \;
#cp -rf $WORKSPACE/tmp/test_results.zip $MOUNTPT/$version/$buildNumber/$hypervisor
#use cloud-bugtool to collect mysqldump, management server logs etc.,
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$MGMT_SVR mkdir -p /tmp/management_${buildNumber}/management
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$MGMT_SVR cp /automation/cloudstack/vmops.log /tmp/management_${buildNumber}/management/
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$MGMT_SVR "pushd /tmp/management_${buildNumber} && zip ${PREFIX}Log_$buildNumber -r management && popd"
scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$MGMT_SVR:/tmp/management_${buildNumber}/${PREFIX}Log_$buildNumber.zip $WORKSPACE/tmp/
cp -rf $WORKSPACE/tmp/${PREFIX}Log_$buildNumber.zip $MOUNTPT/$version/$buildNumber/$hypervisor
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$MGMT_SVR rm -rf /tmp/${PREFIX}Log_$buildNumber.zip
zip -rj $MOUNTPT/$version/$buildNumber/$hypervisor/${PREFIX}Log_$buildNumber.zip $WORKSPACE/tmp/test_result.zip
#rm -rf $MOUNTPT/$version/$buildNumber/$hypervisor/test_run.zip
#move to dropbox folder
cp -r $MOUNTPT/$version/$buildNumber '/root/Dropbox/test_archive/.'

