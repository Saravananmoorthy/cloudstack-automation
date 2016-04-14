import MySQLdb
from marvin import configGenerator
from paramiko import SSHClient,AutoAddPolicy
from scp import SCPClient
from bashUtils import bash
import logging
import urlparse
import sys
import random
import string
import Queue
import threading
from time import sleep as delay
import contextlib
import telnetlib
import socket
import time
from bashUtils import remoteSSHClient
import os

class hostImager():
      def __init__(self):
          self.resourceMgr=resourceManager()
          self.profileMap=({'xenserver':'xenserver6.2','vmware':'VMware5.1-x86_64','kvm':'kvm-Centos64'})
          self.allocatedResource={}
          self.hypervisorInfo=[]
          self.hostClusterMap={'xenserver':[],'kvm':[],'vmware':[]}
          self.logger=logging.getLogger("hostImager")
          self.json_config={}
          self.mountPt="/tmp/" + ''.join([random.choice(string.ascii_uppercase) for x in xrange(0, 10)])
          bash("mkdir -p %s"%self.mountPt)


      def initLogging(self,logFile=None, lvl=logging.INFO):
        try:
             if logFile is None:
                logging.basicConfig(level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
             else:
                 logging.basicConfig(filename=logFile, level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
        except:
           logging.basicConfig(level=lvl)

      def getcobblerprofile(self,hypervisorType):
          return self.profileMap[hypervisorType.lower()]

      def refreshHosts(self,cscfg, static=True):
            """
            Removes cobbler system from previous run.
            Creates a new system for current run.
            Ipmi boots from PXE - default to Xenserver profile
            """
            for zone in cscfg.zones:
                 for pod in zone.pods:
                     for cluster in pod.clusters:
                          hostsInCluster=[]
                          for host in cluster.hosts:
                              hostname = urlparse.urlsplit(host.url).hostname.replace(' ','')
                              #print "hostname=",hostname
                              if cluster.hypervisor.lower()=="simulator":
                                 self.logger.info("found simulator host, no need to  refresh")
                                 continue

                              self.logger.info("attempting to refresh host %s"%hostname)
                              #revoke certs
                              bash("puppet cert clean %s"%(hostname))
                              #setup cobbler profiles and systems
                              try:
                                  hostmac=None
                                  hostip=None
                                  IPMI_PASS=None
                                  ipmi_hostname=None
                                  netmask=None
                                  gateway=None
                                  if static==True:
                                     staticHostInfo=self.resourceMgr.getStaticHostInfo(hostname)
                                     hostmac=staticHostInfo['mac']
                                     hostip=staticHostInfo['ip']
                                     IPMI_PASS=staticHostInfo['ipmi_password']
                                     ipmi_hostname=staticHostInfo['ipmi_hostname']
                                     netmask=staticHostInfo['netmask']
                                     gateway=staticHostInfo['gateway']
                                  if (hostmac==None):
                                     raise Exception('no host machine avilable')
                                  if (hostip==None):
                                     raise Exception('ips not avilable')

                                  hostprofile = self.getcobblerprofile(cluster.hypervisor)
                                  hostinfo={}
                                  hostinfo.update({'hostname':hostname,'password':'password','host_type':cluster.hypervisor,'hostmac':hostmac, \
                                   'ipmi_pass':IPMI_PASS,'impmi_hostname':ipmi_hostname,'netmask':netmask,'gateway':gateway,'ip':hostip})

                                  hostsInCluster.append(hostinfo)
                                  self.hypervisorInfo.append(hostinfo)
                                  templateFiles="/etc/puppet/agent.conf=/etc/puppet/puppet.conf"
                                  bash("cobbler system remove \
                                         --name=%s"%(hostname))
                                  bash("cobbler system add --name=%s --hostname=%s --dns-name=%s\
                                       --mac-address=%s --netboot-enable=y \
                                       --enable-gpxe=no --profile=%s --ip-address=%s --netmask=%s --gateway=%s %s"%(hostname, hostname, hostname, hostmac,\
                                            hostprofile, hostip, netmask, gateway, "--template-files=%s"%templateFiles if cluster.hypervisor.lower()=="kvm" else ""))
                                  #bash("cobbler sync")
                              except Exception as e:
                                     self.logger.exception(e)
                                     sys.exit(2)
                                     #set ipmi to boot from PXE
                              try:
                                  #self.addPuppetConfig(hostinfo)
                                  bash("cobbler sync")
                                  self.logger.debug("found IPMI nic on %s for host %s"%(ipmi_hostname, hostname))
                                  bash("ipmitool -I lanplus -Uroot -P%s -H%s chassis bootdev \
                                  pxe"%(IPMI_PASS, ipmi_hostname))
                                  bash("ipmitool -I lanplus -Uroot -P%s -H%s chassis power cycle"%(IPMI_PASS, ipmi_hostname))
                                  self.logger.debug("Sent PXE boot for %s"%ipmi_hostname)
                                  self.logger.info("waiting for some time till server starts")
                              except KeyError:
                                  self.logger.error("No ipmi host found against %s. Exiting"%hostname)
                                  sys.exit(2)
                                  raise
                              yield hostname
                          if (cluster.hypervisor.lower() != 'simulator'):
                             self.hostClusterMap[cluster.hypervisor.lower()].append(hostsInCluster)
                             self.logger.info("host cluster map %s"%self.hostClusterMap)
                          #print self.hostClusterMap

      def addPuppetConfig(self,hostinfo):
          if hostinfo['host_type'].lower()=="kvm":
             #add this node to nodes.pp of puppet
             bash(("echo \"node '%s' inherits basenode {\ninclude nfsclient \ninclude kvm-agent }\" >> /etc/puppet/manifests/nodes.pp"%(hostinfo['hostname'])));

      def prepareKVMHost(self,mgmtHostInfo,hypervisor):
          self.logger.info("preparing kvm host %s"%hypervisor['hostname'])
          ssh = SSHClient()
          ssh.set_missing_host_key_policy(AutoAddPolicy())
          ssh.connect(hypervisor['ip'], 22,username="root",password=hypervisor['password'])
          scp = SCPClient(ssh.get_transport())
          scp.put("/etc/puppet/modules/kvm-agent/files/authorized_keys","/root/.ssh/")
          mgmtSsh=remoteSSHClient(mgmtHostInfo['ip'], 22, "root", mgmtHostInfo['password'])
          self.logger.info("copying the cloudstack rpms to kvm host")
          bash("scp -r -q -o StrictHostKeyChecking=no  /etc/puppet/modules/kvm-agent root@%s:/root"%hypervisor['ip'])
          kvmSsh=remoteSSHClient(hypervisor['ip'], 22, "root", hypervisor['password'])
          kvmSsh.execute("mkdir /tmp/cloudstack")
          mgmtSsh.execute("scp -r -q -o StrictHostKeyChecking=no -i /root/.ssh/id_rsa.mgmt /root/cloudstack-repo/*  root@%s:/tmp/cloudstack"%hypervisor['ip'])
          kvmSsh.execute("puppet apply --debug --modulepath=/root -e 'include kvm-agent' >> puppetRun.log  2>&1")
          kvmSsh.close()
          mgmtSsh.close()
          self.logger.info("kicked off puppet install of kvm")


      def createXenPools(self,xenHostClusterList):
          for hostList in xenHostClusterList:
               for hostInfo in hostList[1:]:
                    hostssh=remoteSSHClient(hostInfo['ip'], 22, "root", hostInfo['password'])
                    hostssh.execute("xe pool-join master-address=%s master-username='%s'  master-password='%s'"%(hostList[0]['hostname'],'root',hostList[0]['password']))
                    hostssh.close()

      def mkdirs(self,path):
          dir = bash("mkdir -p %s" % path)

      def pacakageIfKVM(self):
          for hypervisor in self.hypervisorInfo:
              if hypervisor['host_type'].lower()=="kvm":
                 return True
          return False

      def addProxyInfoToHosts(self):
          for hypervisor in self.hypervisorInfo:
              self.logger.info("Adding proxy info to host %s"%hypervisor['ip'])
              hostssh=remoteSSHClient(hypervisor['ip'], 22, "root", hypervisor['password'])
              hostssh.execute('echo "export http_proxy=http://172.16.88.5:3128" >> /root/.bashrc')
              hostssh.close()

      def execPostInstallHooks(self,mgmtHostInfo):
          for hypervisor in self.hypervisorInfo:
              if hypervisor['host_type'].lower() == "kvm":
                 self.prepareKVMHost(mgmtHostInfo,hypervisor)
              elif  hypervisor['host_type'].lower() == "vmware":
                    pass
              elif hypervisor['host_type'].lower() == "xenserver":
                   self.createXenPools(self.hostClusterMap['xenserver'])

      def seedSecondaryStorage(self,cscfg,hostInfo):
          """
          erase secondary store and seed system VM template via puppet. The
          secseeder.sh script is executed on mgmt server bootup which will mount and
          place the system VM templates on the NFS
          """
          mgmt_server = cscfg.mgtSvr[0].mgtSvrIp
          #hypervisors = ["xen","kvm","vmware"]
          ssh = SSHClient()
          ssh.set_missing_host_key_policy(AutoAddPolicy())
          ssh.connect(hostname=hostInfo['ip'],username="root",password=hostInfo['password'])
          scp = SCPClient(ssh.get_transport())

          for zone in cscfg.zones:
               for pod in zone.pods:
                  for cluster in pod.clusters:
                    if cluster.hypervisor.lower() == "xenserver":
                        hypervisor="xen"
                    else:
                       hypervisor=cluster.hypervisor.lower()
                    if hypervisor=="simulator":
                       continue
                    for sstor in zone.secondaryStorages:
                           shost = urlparse.urlsplit(sstor.url).hostname
                           spath = urlparse.urlsplit(sstor.url).path
                           spath = ''.join([shost, ':', spath])
                           self.createStorageDirs(sstor)
                           #for h in hypervisors:
                           self.logger.info("adding template seeding commands to seed %s systemvm template on %s"%(hypervisor, spath))
                           #self.logger.info("seeding from url %s"%self.resourceMgr.getSystemVMdownloadUrl(hostInfo['branch'],cluster.hypervisor.lower()))
                           bash("echo '/bin/bash /root/redeploy.sh -s %s -u %s -h %s' >> /tmp/secseeder.%s.sh"%(spath, self.resourceMgr.getSystemVMdownloadUrl(hostInfo['branch'],cluster.hypervisor.lower())['download_url'],hypervisor,hostInfo['ip']))
          try:
              if (os.path.exists("/tmp/secseeder.%s.sh"%(hostInfo['ip']))):
                 bash("chmod +x /tmp/secseeder.%s.sh"%(hostInfo['ip']))
                 scp.put("/tmp/secseeder.%s.sh"%(hostInfo['ip']),"/root/secseeder.sh")
                 bash("rm -f /tmp/secseeder.%s.sh"%hostInfo['ip'])
          except Exception as e:
                 self.logger.exception(e)
                 raise

      def cleanMount(self):
          bash("umount %s"%self.mountPt)

      def createStorageDirs(self,sstor):
          self.logger.info("mount -t nfs %s %s"%("/".join(sstor.url.replace("nfs://","").split("/")[:2]),self.mountPt))
          mount=bash("mount -t nfs %s %s"%("/".join(sstor.url.replace("nfs://","").split("/")[:2]),self.mountPt))
          if(not mount.isSuccess()):
             self.logger.error("failed to mount %s"%mount.getStderr())
          path = urlparse.urlsplit(sstor.url).path
          self.logger.debug("path %s"%path)
          relativePath=path.replace(path.split("/")[1],self.mountPt)
          self.logger.info("mkdir -p %s"%relativePath)
          bash("mkdir -p %s"%relativePath)
          self.cleanMount()

      def seedBuiltinTemplates(self):
          for zone in self.json_config.zones:
               for pod in zone.pods:
                  for cluster in pod.clusters:
                    if cluster.hypervisor.lower() == "xenserver":
                        hypervisor="xen"
                    else:
                       hypervisor=cluster.hypervisor.lower()
                    if hypervisor=="simulator":
                       continue
                    for sstor in zone.secondaryStorages:
                           path = urlparse.urlsplit(sstor.url).path
                           relativePath=path.replace(path.split("/")[1],self.mountPt)
                           #mount secondary storage on ms.
                           mount=bash("mount -t nfs %s %s"%("/".join(sstor.url.replace("nfs://","").split("/")[:2]),self.mountPt))
                           if(not mount.isSuccess()):
                             self.logger.error("failed to mount %s"%sstor)
                           if(hypervisor=='xen'):
                               if(not bash("mkdir -p  %s/template/tmpl/1/5/"%relativePath).isSuccess()):
                                   self.logger.error("failed to create directory on nfs-server %s"%"".join(ssh.errorlog))
                               if(not bash("cp -f %s/automation/BUILTIN/XEN/* %s/template/tmpl/1/5/."%(self.mountPt,relativePath)).isSuccess()):
                                   self.logger.error("failed to copy builtin template %s"%"".join(ssh.errorlog))
                           if(hypervisor=='kvm'):
                               if(not bash("mkdir -p %s/template/tmpl/1/4/"%relativePath).isSuccess()):
                                   self.logger.error("failed to create directory on nfs-server %s"%"".join(ssh.errorlog))
                               if(bash("cp -f %s/automation/BUILTIN/KVM/* %s/template/tmpl/1/4/."%(self.mountPt,relativePath)).isSuccess()):
                                   self.logger.error("failed to copy builtin template %s"%"".join(ssh.errorlog))
                           bash("umount %s"%self.mountPt)

      def mountAndClean(self,host, path):
        """
        Will mount and clear the files on NFS host in the path given. Obviously the
        NFS server should be mountable where this script runs
        """
        self.mkdirs(self.mountPt)
        self.logger.info("cleaning up %s:%s" % (host, path))
        mnt = bash("mount -t nfs %s:%s %s" % (host, path, self.mountPt))
        erase = bash("rm -rf %s/*" % self.mountPt)
        umnt = bash("umount %s" % self.mountPt)


      def cleanPrimaryStorage(self,cscfg):
          """
          Clean all the NFS primary stores and prepare them for the next run
         """
          for zone in cscfg.zones:
                for pod in zone.pods:
                    for cluster in pod.clusters:
                        if cluster.hypervisor.lower()=="simulator":
                             continue;
                        for primaryStorage in cluster.primaryStorages:
                            if urlparse.urlsplit(primaryStorage.url).scheme == "nfs":
                               self.createStorageDirs(primaryStorage)
                               self.mountAndClean(urlparse.urlsplit(primaryStorage.url).hostname, urlparse.urlsplit(primaryStorage.url).path)
                               self.logger.info("Cleaned up primary stores")


      def _isPortOpen(self,hostQueue, port=22):
          """
          Checks if there is an open socket on specified port. Default is SSH
          """
          ready = []
          host = hostQueue.get()
          while True:
             channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
             channel.settimeout(20)
             try:
                self.logger.debug("Attempting port=%s connect to host %s"%(port, host))
                err = channel.connect_ex((host, port))
             except socket.error, e:
                    self.logger.debug("encountered %s retrying in 5s"%e)
                    err = e.errno
                    delay(5)
             finally:
                if err == 0:
                  ready.append(host)
                  #self.logger.info("host: %s is ready"%host)
                  break
                else:
                  self.logger.debug("[%s] host %s is not ready. Retrying"%(err, host))
                  delay(5)
                  channel.close()
          hostQueue.task_done()


      def waitForHostReady(self,hostlist):
          self.logger.info("Waiting for hosts %s to refresh"%hostlist)
          hostQueue = Queue.Queue()
          for host in hostlist:
              t = threading.Thread(name='HostWait-%s'%hostlist.index(host), target=self._isPortOpen,
                             args=(hostQueue, ))
              t.setDaemon(True)
              t.start()
          [hostQueue.put(host) for host in hostlist]
          hostQueue.join()
          self.logger.info("All hosts %s are up"%hostlist)

      def checkIfHostsUp(self,hosts):
          self.waitForHostReady(hosts)
          delay(30)
          # Re-check because ssh connect works soon as post-installation occurs. But
          # server is rebooted after post-installation. Assuming the server is up is
          # wrong in these cases. To avoid this we will check again before continuing
          # to add the hosts to cloudstack
          self.waitForHostReady(hosts)
          #self.addProxyInfoToHosts()

      def imageHosts(self,mgmtHostInfo):
          hosts=[]
          self.json_config = configGenerator.getSetupConfig(mgmtHostInfo['configfile'])
          hosts.extend(self.refreshHosts(self.json_config))
          self.seedSecondaryStorage(self.json_config, mgmtHostInfo)
          self.cleanPrimaryStorage(self.json_config)
          return hosts


class resourceManager():
       def __init__(self):
           self.dbHost="localhost"
           self.username="root"
           self.passwd=""
           self.database="resource_db"
           self.__con = None
           self.logger=logging.getLogger("resourceManager")

       def initLogging(logFile=None, lvl=logging.INFO):
         try:
             if logFile is None:
                logging.basicConfig(level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
             else:
                 logging.basicConfig(filename=logFile, level=lvl, \
                                format="'%(asctime)-6s: %(name)s \
                                (%(threadName)s) - %(levelname)s - %(message)s'")
         except:
           logging.basicConfig(level=lvl)

       def connect(self):
           self.__con = MySQLdb.connect(self.dbHost,self.username, self.passwd, self.database)
           return self.__con is not None

       def getDict(self, dbResponse, cur):
           if ( dbResponse and len(dbResponse)):
                 desc=cur.description
                 responseDict={}
                 for value in desc:
                     responseDict.update({value[0]:dbResponse[value[0]]})
                 return responseDict

       def getIp(self):
           if self.__con or self.connect():
              cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
              cur.execute("SELECT * FROM `resource_db`.`ip_resource` WHERE state='free'")
              ip=self.getDict(cur.fetchone(),cur)
              if ip!=None:
                 cur.execute("UPDATE `resource_db`.`ip_resource` SET state='active' where id='%s'"%ip['id'])
                 self.__con.commit()
                 return ip['ip']

       def getMac(self):
           if self.__con or self.connect():
              cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
              cur.execute("SELECT * FROM `resource_db`.`mac_resource` WHERE state='free'")
              mac=self.getDict(cur.fetchone(),cur)
              if mac!=None:
                 cur.execute("UPDATE `resource_db`.`mac_resource` SET state='active' where id='%s'"%mac['id'])
                 self.__con.commit()
                 return mac['mac']

       def  getStaticHostInfo(self,hostname):
           if self.__con or self.connect():
              cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
              self.logger.debug("SELECT * FROM `resource_db`.`static_host_info` WHERE hostname='%s'"%hostname)
              cur.execute("SELECT * FROM `resource_db`.`static_host_info` WHERE hostname='%s'"%hostname)
              hostInfo=self.getDict(cur.fetchone(),cur)
              self.logger.debug("staticHostInfo", hostInfo)
              if hostInfo!=None:
                 return hostInfo

       def freeIp(self,ip):
           if self.__con or self.connect():
              cur=self.__con.cursor()
              cur.execute("UPDATE `resource_db`.`ip_resource` SET state='free' where ip='%s'"%ip)
              self.logger.debug("freed ip %s"%ip)

       def freeMac(self,mac):
           if self.__con or self.connect():
              cur=self.__con.cursor()
              cur.execute("UPDATE `resource_db`.`mac_resource` SET state='free' where id='%s'"%mac)
              self.logger.debug("freed mac %s"%mac)

       def getConfig(self,profile,configName=None):
           if self.__con or self.connect():
              cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
              if configName==None:
                 self.logger.debug("SELECT * FROM `resource_db`.`static_config` WHERE state='free' and profile='%s'"%profile)
                 cur.execute("SELECT * FROM `resource_db`.`static_config` WHERE state='free' and profile='%s'"%profile)
              else:
                 self.logger.debug("SELECT * FROM `resource_db`.`static_config` WHERE state='free' and configName='%s' and profile='%s'"%(configName, profile))
                 cur.execute("SELECT * FROM `resource_db`.`static_config` WHERE state='free' and configName='%s' and profile='%s'"%(configName, profile))
              config=self.getDict(cur.fetchone(),cur)
              if config!=None:
                 cur.execute("UPDATE `resource_db`.`static_config` SET state='active' where id='%s'"%config['id'])
                 self.__con.commit()
                 return config


       def freeConfig(self,config):
             if self.__con or self.connect():
              cur=self.__con.cursor()
              cur.execute("UPDATE `resource_db`.`static_config` SET state='free' where configfile='%s'"%config)
              self.logger.info("freed config  %s"%config)

       def getSystemVMdownloadUrl(self,branch,hypervisor_type):
            if self.__con or self.connect():
               cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
               cur.execute("SELECT * FROM `resource_db`.`systemvm_template` WHERE branch='%s' and hypervisor_type='%s'"%(branch,hypervisor_type))
               templateInfo=self.getDict(cur.fetchone(),cur)
               return templateInfo

       def addJobDetails(self,jobDetails):
           if self.__con or self.connect():
              cur=self.__con.cursor()
              cur.execute("INSERT INTO `resource_db`.`jobDetails` (`job_name`, `created`, `related_data_path`) VALUES ('%s', now(), '%s')"%(jobDetails['job_name'],jobDetails['related_data_path'] ))
              self.__con.commit()
              self.logger.info("saved the details of job %s"%jobDetails['job_name'])

       def getJobDetails(self):
           if self.__con or self.connect():
              cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
              cur.execute("SELECT * FROM `resource_db`.`jobDetails`")
              return cur.fetchall()

       def  removeJob(self,jobName):
            if self.__con or self.connect():
               cur=self.__con.cursor()
               cur.execute("DELETE FROM `resource_db`.`jobDetails` where job_name='%s'"%jobName)
               self.__con.commit()
               self.logger.info("removed job %s from db"%jobName)

       def addBuildInfo(self, build_info):
           if self.__con or self.connect():
               cur=self.__con.cursor()
               cur.execute("INSERT INTO `resource_db`.`build_info` (`build_number`,`git_repo_url`, `branch`, `commit_id`, `hypervisor`, `build_date`) VALUES ('%s', '%s', '%s', '%s', '%s', now())"%(build_info['build_number'],build_info['repo_url'], build_info['branch'], build_info['commit_id'], build_info['hypervisor']))
               self.__con.commit()

       def getLastBuildInfo(self,repo_url, branch, hypervisor):
           if self.__con or self.connect():
               cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
               cur.execute("SELECT * FROM `resource_db`.`build_info` WHERE git_repo_url='%s' and branch='%s' and hypervisor='%s' order by build_date DESC"%(repo_url, branch, hypervisor))
               buildInfo=self.getDict(cur.fetchone(),cur)
               return buildInfo
