import ConfigParser
import MySQLdb
from bashUtils import bash
from synchronized import synchronized
from marvin import configGenerator
from bashUtils import  remoteSSHClient
from argparse import ArgumentParser
from time import sleep as delay
from netaddr import IPNetwork
from netaddr import IPAddress
import contextlib
import telnetlib
import logging
import threading
import Queue
import sys
import random
import string
import urllib2
import urlparse
import socket
import os
from hostImager  import resourceManager, hostImager
import time	

class hostManager:
    def __init__(self): 
        self.workDir="/root/cloud-autodeploy2/newcode"
        self.IPMI_PASS="root"
        self.DOMAIN = 'automation.hyd.com'
        self.infraxen_ip=None
        self.infraxen_passwd=None
        self.ipmiinfo = {}
        self.cobblerinfo = {}
        self.mgmtHostInfo = {}
        self.resourceMgr=resourceManager()
        self.hostImager=hostImager()
        self.logger=logging.getLogger("hostManager")

    def execCmd(self,cmd):
        pipe = subprocess.PIPE
        self.logger.debug("Executing:%s", cmd)
        proc = subprocess.Popen(cmd, shell=False, stdin=pipe, stdout=pipe,
                            stderr=pipe, close_fds=True)
        ret_code = proc.wait()
        err = proc.stderr.read()
        if ret_code:
           self.logger.debug("The command exited with the error code: " +
                      "%s (stderr output:%s)" % (ret_code, err))
           return FAILED
        output = proc.stdout.read()
        return output



    def prepareCloudstackRepo(self):
     #   bash("rm -f /etc/puppet/modules/cloudstack-simulator/files/tar-cloudstackGitRepo.tar.gz")
     #   bash("tar -zcf /etc/puppet/modules/cloudstack-simulator/files/tar-cloudstackGitRepo.tar.gz /automation/jenkins/workspace/testbuild-hyd/")
        pass
     


    def mkdirs(self,path):
       dir = bash("mkdir -p %s" % path)

    def getProfile(self,breed):
       return "Centos6.3-x86_64" 

    def checkIfSimulatorBuild(self,config):
        for zone in config.zones:
                 for pod in zone.pods:
                     for cluster in pod.clusters:
                         if cluster.hypervisor.lower()=='simulator':
                            return False
        return True

    def configureManagementServer(self,profile, branch, configName=None):
     """
     We currently configure all mgmt servers on a single xen HV. In the future
     replace this by launching instances via the API on a IaaS cloud using
     desired template
     """
     mgmt_vm_mac = bash(self.workDir+"/macgen.py").getStdout()
     mgmt_host = "centos-"+mgmt_vm_mac.replace(':','-')
     mgmt_ip=None
     configPath=None
     configObj=None
     if configName==None:
           configObj=self.resourceMgr.getConfig(profile)
     else:
         configObj=self.resourceMgr.getConfig(profile,configName)
     if configObj==None:
        self.logger.info("either the config you asked for is in use or it is not registered in the db")
        sys.exit(1)

     configPath=configObj['configfile']
     #print "config_path",configPath
     config=configGenerator.getSetupConfig(configPath.replace(' ',''))
     #print config
     mgmt_ip=config.mgtSvr[0].mgtSvrIp
     #validate the ip address
     try:
        ip=IPAddress(mgmt_ip)
     except Exception,e:
            self.logger.error(e)
            #freeconfig and exit
            self.resourceMgr.freeConfig(configPath)
            exit(1)
 
     self.infraxen_ip=config.infraxen
     self.infraxen_passwd=config.infraxen_passwd
     noSimulator=self.checkIfSimulatorBuild(config)
     if (self.infraxen_ip==None or self.infraxen_passwd==None):
        self.logger.info("invalid values for infraxen_ip or infraxen_passwd")
        self.resourceMgr.freeConfig(configPath)
        exit(1)

     self.logger.info("management server ip=%s"%mgmt_ip)
        
     os="centos"
     self.mgmtHostInfo.update({'hostname':mgmt_host})
     #print self.mgmtHostInfo
     self.mgmtHostInfo.update({'ip':mgmt_ip})
     self.mgmtHostInfo.update({'mac':mgmt_vm_mac})
     self.mgmtHostInfo.update({'password':"password"})
     self.mgmtHostInfo.update({'domain':self.DOMAIN})
     self.mgmtHostInfo.update({'os':os})
     #print self.mgmtHostInfo
     self.mgmtHostInfo.update({'configfile':configPath})
     self.mgmtHostInfo.update({'config_id':configObj['id']})
     self.mgmtHostInfo.update({'infra_server':self.infraxen_ip})
     self.mgmtHostInfo.update({'infra_server_passwd':self.infraxen_passwd})
     self.mgmtHostInfo.update({'profile':profile})
     self.mgmtHostInfo.update({'branch':branch})
     self.mgmtHostInfo.update({'noSimulator':noSimulator})
     self.mgmtHostInfo.update({'simulator':'dummy'}) 
     templateFiles="/etc/puppet/agent.conf=/etc/puppet/puppet.conf"
     cobbler_profile=self.getProfile("centos")

     #Remove and re-add cobbler system
     bash("cobbler system remove --name=%s"%mgmt_host)
     bash("cobbler system add --name=%s --hostname=%s --dns-name=%s --mac-address=%s \
          --netboot-enabled=yes --enable-gpxe=no --ip-address=%s \
          --profile=%s --template-files=%s "%(mgmt_host, mgmt_host, (mgmt_host+"."+self.DOMAIN),
                                                 mgmt_vm_mac, mgmt_ip, cobbler_profile, templateFiles));
     bash("cobbler sync")
     #clean puppet reports if any
     bash("rm -f %s"%("/var/lib/puppet/reports/"+self.mgmtHostInfo['hostname']+"."+self.DOMAIN))
     #add this node to nodes.pp of puppet 
     bash(("echo \"node %s inherits basenode { \ninclude nfsclient\ninclude java17\ninclude mysql\ninclude maven\ninclude cloudstack-simulator }\" >> /etc/puppet/manifests/nodes.pp"%(mgmt_host)));
     #Revoke all certs from puppetmaster
     bash("puppet cert clean %s.%s"%(mgmt_host, self.DOMAIN))

     #Start VM on xenserver
     xenssh = \
     remoteSSHClient(self.infraxen_ip,22, "root", self.infraxen_passwd)

     self.logger.debug("bash vm-uninstall.sh -n %s"%(mgmt_host))
     xenssh.execute("xe vm-uninstall force=true vm=%s"%mgmt_host)
     self.logger.debug("bash vm-start.sh -n %s -m %s"%(mgmt_host, mgmt_vm_mac))
     out = xenssh.execute("bash vm-start.sh -n %s -m %s"%(mgmt_host,
                                                  mgmt_vm_mac))
     self.logger.info("started mgmt server: %s. Waiting for services .."%mgmt_host);
     return self.mgmtHostInfo


    def waitTillPuppetFinishes(self):
        filePath = "/var/lib/puppet/reports/"+self.mgmtHostInfo['hostname']+"."+self.DOMAIN
        while not os.path.exists(filePath):
             delay(60)
             self.logger.info("waiting for puppet setup to finish")  
             continue
        pass
   
    def _isPortListening(self,host, port, timeout=120):
      """
      Scans 'host' for a listening service on 'port'
      """
      tn = None
      while timeout != 0:
         try:
            self.logger.debug("Attempting port=%s connect to host %s"%(port, host))
            tn = telnetlib.Telnet(host, port, timeout=timeout)
            timeout = 0
         except Exception, e:
            self.logger.debug("Failed to telnet connect to %s:%s with %s"%(host, port, e))
            delay(5)
            timeout = timeout - 5
         if tn is None:
            self.logger.error("No service listening on port %s:%d"%(host, port))
            delay(5)
            timeout = timeout - 5
         else:
             self.logger.info("Unrecognizable service up on %s:%d"%(host, port))
             return True

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
              print host,port
              err = channel.connect_ex((host, port))
              print err
           except socket.error, e:
              self.logger.debug("encountered %s retrying in 5s"%e)
              err = e.errno
              delay(5)
           finally:
              if err == 0:
                  ready.append(host)
                  self.logger.info("host: %s is ready"%host)
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

    def isManagementServiceStable(self,ssh=None, timeout=300, interval=5):
       self.logger.info("Waiting for cloudstack-management service to become stable")
       if ssh is None:
          return False
       while timeout != 0:
          cs_status = ''.join(ssh.execute("service cloudstack-management status"))
          self.logger.debug("[-%ds] Cloud Management status: %s"%(timeout, cs_status))
          if cs_status.find('running') > 0:
              pass
          else:
              ssh.execute("killall -9 java; mvn -Dsimulator -pl client jetty:run")
          timeout = timeout - interval
          delay(interval)


    def prepareManagementServer(self,url,branch,commit):
       """
       Prepare the mgmt server for a marvin test run
       """
       buildLog=""
       self.logger.info("preparing management server")
       if self._isPortListening(host=self.mgmtHostInfo['ip'], port=22, timeout=300) \
            and self._isPortListening(host=self.mgmtHostInfo['ip'], port=3306, timeout=30):
          mgmt_ip = self.mgmtHostInfo['ip'] 
          mgmt_pass = self.mgmtHostInfo['password']
          self.mgmtHostInfo['branch']=branch
          with contextlib.closing(remoteSSHClient(mgmt_ip, 22, "root", mgmt_pass)) as ssh:
            # Open up 8096 for Marvin initial signup and register
            package=self.hostImager.pacakageIfKVM()

            ssh.execute("python /root/buildAndDeploySimulator.py --package %s --noSimulator %s  -u %s -b %s  --fqdn %s %s -s True>> /var/log/cloudstack.log"%(package, self.mgmtHostInfo['noSimulator'], url, branch,  self.mgmtHostInfo['hostname']+"."+self.DOMAIN, ("" if commit==None else "-c %s"%commit)))
            buildlog="".join(ssh.stdout)
            ssh.execute("sh /root/secseeder.sh > secseeder.log 2>&1")
            self.hostImager.seedBuiltinTemplates()
            ssh.execute("cd /automation/cloudstack/; git log | grep -m 1 'commit' | cut -f 2 -d ' '") 
            self.logger.info('build from commit_id %s'%ssh.stdout[0])
            self.mgmtHostInfo.update({'commit_id':ssh.stdout[0]})
            retry=3
            while retry !=0: 
                  if not  (self._isPortListening(host=self.mgmtHostInfo['ip'], port=8080, timeout=300)):
                          ssh.execute("python /root/restartMgmtServer.py -p /automation/cloudstack/ --noSimulator %s >> /var/log/cloudstack.log"%self.mgmtHostInfo['noSimulator'] )
                          self.logger.debug("exccede timeout restarting the management server and trying again")
                          retry=retry-1
                  else: 
                      break
       else:
          raise Exception("Reqd services (ssh, mysql) on management server are not up. Aborting")

       if self._isPortListening(host=self.mgmtHostInfo['ip'], port=8096, timeout=10):
          self.logger.info("All reqd services are up on the management server %s"%self.mgmtHostInfo['hostname'])
          return
       else:
          self.logger.error("Build log.......................... \n %s"%buildlog)
          raise Exception("Management server %s is not up. Aborting"%self.mgmtHostInfo['hostname'])
       #seed systemvm templates
       '''result=ssh.execute("sh /root/secseeder.sh > secseeder.log 2>&1")
       if (result !=0):
           self.logger.error(''.join(error)); 
           raise Exception("failed to seed systemvm templates")'''
       #execute post install tasks. 
       self.hostImager.execPostInstallHooks(self.mgmtHostInfo)
    
    def refreshHost(self, mgmtHostInfo,branch,commit,reImageHosts=True):
        """
        Prepare the mgmt server for a marvin test run
        """
        buildlog=""
        self.logger.info("refreshing managemet server")
        self.mgmtHostInfo=mgmtHostInfo
        self.mgmtHostInfo.update({'startTime':time.strftime("%c")})
        self.mgmtHostInfo['branch']=branch
        if reImageHosts:
           compute_hosts=self.hostImager.imageHosts(self.mgmtHostInfo)
        if self._isPortListening(host=mgmtHostInfo['ip'], port=22, timeout=300) \
            and self._isPortListening(host=mgmtHostInfo['ip'], port=3306, timeout=30):
          mgmt_ip = self.mgmtHostInfo['ip']
          mgmt_pass = self.mgmtHostInfo['password']
          with contextlib.closing(remoteSSHClient(mgmt_ip, 22, "root", mgmt_pass)) as ssh:
            self.logger.info("seeding systemvm templates")
            #ssh.execute("sh /root/secseeder.sh > secseeder.log 2>&1")
            #self.hostImager.seedBuiltinTemplates()
            package=self.hostImager.pacakageIfKVM()
            config=configGenerator.getSetupConfig(self.mgmtHostInfo['configfile'].replace(' ',''))
            noSimulator=self.checkIfSimulatorBuild(config)
            self.mgmtHostInfo.update({'noSimulator':noSimulator})
            ssh.execute("python /root/refreshHost.py -p %s --noSimulator %s -b  %s %s>> /var/log/cloudstack.log"%(package, self.mgmtHostInfo['noSimulator'], branch,("" if commit==None else "-c %s"%commit)))
            buildlog="".join(ssh.stdout)
            self.logger.info("build log ...............\n%s"%buildlog)
            ssh.execute("cd /automation/cloudstack/; git log | grep -m 1 'commit' | tr -d 'commit' | tr -d ' '")
            self.logger.info('building from commit_id %s'%ssh.stdout[0])
            self.mgmtHostInfo.update({'commit_id':ssh.stdout[0]})
            ssh.execute("sh /root/secseeder.sh > secseeder.log 2>&1")
            self.hostImager.seedBuiltinTemplates()
            retry=3
            while retry !=0:
                  if not  (self._isPortListening(host=self.mgmtHostInfo['ip'], port=8080, timeout=300)):
                          ssh.execute("python /root/restartMgmtServer.py -p /automation/cloudstack/ --noSimulator %s >> /var/log/cloudstack.log"%self.mgmtHostInfo['noSimulator'])
                          self.logger.debug("exceded timeout restarting the management server and trying again")
                          retry=retry-1
                  else:
                      break
          self.hostImager.checkIfHostsUp(compute_hosts)
          self.hostImager.execPostInstallHooks(self.mgmtHostInfo)
          return self.mgmtHostInfo  
 
    def init(lvl=logging.INFO):
         pass 

    def create(self,repo_url, branch,commit,configName,profile):
       # Re-check because ssh connect works soon as post-installation occurs. But 
       # server is rebooted after post-installation. Assuming the server is up is
       # wrong in these cases. To avoid this we will check again before continuing
       # to add the hosts to cloudstack
       try:
          hosts=[]
          self.mgmtHostInfo={}
          self.mgmtHostInfo.update({'startTime':time.strftime("%c"),'repo_url':repo_url,'branch':branch})
          self.prepareCloudstackRepo()
          prepare_mgmt = True
          self.logger.info("Configuring management server")
          self.configureManagementServer(profile, branch, configName)
          hosts.append(self.mgmtHostInfo['hostname'])
          self.waitForHostReady(hosts)
          mgmtSsh=remoteSSHClient(self.mgmtHostInfo['ip'], 22, "root", self.mgmtHostInfo['password'])
          mgmtSsh.execute("echo 'export http_proxy=http://172.16.88.5:3128' >> /root/.bashrc; source /root/.bashrc")
          mgmtSsh.execute("puppet agent -t ")
          mgmtSsh.execute("ssh-copy-id root@%s"%self.mgmtHostInfo['ip'])
          self.waitTillPuppetFinishes()
          #git proxy config
          mgmtSsh.execute("git config --global http.proxy http://172.16.88.5:3128; git config --global https.proxy http://172.16.88.5:3128")
          delay(30)
          if prepare_mgmt:
             compute_hosts=self.hostImager.imageHosts(self.mgmtHostInfo)
             self.prepareManagementServer(repo_url,branch,commit)
             self.mgmtHostInfo.update({'repo_url':repo_url,'branch':branch})
             self.hostImager.checkIfHostsUp(compute_hosts)
             return self.mgmtHostInfo 
       except Exception, e:
            self.logger.error(e)       
            #cleanup resources and exit.
            self.resourceMgr.freeConfig(self.mgmtHostInfo['configfile'])
            xenssh=remoteSSHClient(self.infraxen_ip,22, "root", self.infraxen_passwd)
            self.logger.debug("bash vm-uninstall.sh -n %s"%(self.mgmtHostInfo['hostname']))
            xenssh.execute("xe vm-uninstall force=true vm=%s"%self.mgmtHostInfo['hostname']) 
            bash("cobbler system remove --name=%s"%(self.mgmtHostInfo['hostname']))
            bash("cobbler sync")
            sys.exit(1)
   
          

class poolManager():
   def __init__(self):
      self.dbHost="localhost"
      self.username="root"
      self.passwd=""
      self.database="resource_db"
      self.resourceMgr=resourceManager()
      self.__con = None
      self.logger=logging.getLogger("poolManager" ) 

   def connect(self):
       self.logger.info("acquiring db connection")
       self.__con = MySQLdb.connect(self.dbHost,self.username, self.passwd, self.database)
       return self.__con is not None    
 
   def addToPool(self,hostinfo):
         if self.__con or self.connect():
            cur=self.__con.cursor()
            cur.execute("INSERT INTO `resource_db`.`host` (`mac`, `ip`, `repo_url`, `branch`, `domain`, `hostname`, `os`, `password`, `state`, `config_id`, `infra_server`, `infra_server_passwd`, `simulator`,`profile`)\
                   VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(hostinfo['mac'], hostinfo['ip'], hostinfo['repo_url'], hostinfo['branch'], hostinfo['domain'],\
                   hostinfo['hostname'],hostinfo['os'], hostinfo['password'], hostinfo['state'], hostinfo['config_id'], hostinfo['infra_server'], hostinfo['infra_server_passwd'], hostinfo['simulator'],hostinfo['profile']))
            self.__con.commit()
            self.logger.info("added host %s to the pool"%hostinfo['hostname']) 

   def remove(self,hostId):
         if self.__con or self.connect():
            cur =self.__con.cursor()
            cur.execute("DELETE FROM `resource_db`.`host` WHERE id='%s'"%(hostId))
            self.__con.commit()
  
   def update(self,hostId,name,value):
         if self.__con or self.connect():
            cur =self.__con.cursor()
            #print "UPDATE `resource_db`.`host` SET %s='%s' where id='%s'"%(name,value,hostId)
            cur.execute("UPDATE `resource_db`.`host` SET %s='%s' where id='%s'"%(name,value,hostId))
            self.__con.commit()
            self.logger.info("updating host info")
   
   def findHostbyMac(self,mac):
       if self.__con or self.connect():
          cur=self.__con.cursor(MySQLdb.cursors.DictCursor)
          cur.execute("SELECT * FROM `resource_db`.`host` WHERE mac='%s'"%mac)
          return self.getDict(cur.fetchone(),cur)
 
   def getDict(self, dbResponse, cur):
       if ( dbResponse and len(dbResponse)):
                 desc=cur.description
                 responseDict={}
                 for value in desc:
                     responseDict.update({value[0]:dbResponse[value[0]]})
                 return responseDict

   def findSutableHost(self, repo_url, profile, configName=None, OsType=None):
       if self.__con or self.connect():
             cur =self.__con.cursor(MySQLdb.cursors.DictCursor)
             #print ("SELECT * FROM `resource_db`.`host`,`resource_db`.`static_config` WHERE `host`.config_id=`static_config`.id and `host`.state='free' and `static_config`.state='free' and repo_url='%s' and `host`.profile='%s'  %s"%(repo_url, profile, ("and `static_config`.configName ='%s'"%configName if configName!=None else "" )))
             if (OsType==None):
                cur.execute("SELECT * FROM `resource_db`.`host`,`resource_db`.`static_config` WHERE `host`.config_id=`static_config`.id and `host`.state='free' and `static_config`.state='free' and repo_url='%s' and `host`.profile='%s'  %s"%(repo_url, profile, ("and `static_config`.configName ='%s'"%configName if configName!=None else "" )))    
             else:
                cur.execute("SELECT * FROM `resource_db`.`host`,`resource_db`.`static_config` WHERE `host`.config_id=`static_config`.id and `host`.state='free' and `static_config`.state='free' and repo_url='%s' and `host`.profile='%s' and`host`.os='%s'  %s"%(repo_url, profile, OsType, ("and `static_config`.configName ='%s'"%configName if configName!=None else "" )))
             host=cur.fetchone()
             if ( host and len(host)):
                 #print "one host found", host
                 hostInfo=self.getDict(host,cur)
                 #print hostInfo
                 cur.execute("UPDATE `resource_db`.`host` SET state='%s' WHERE id='%s'"%("active",hostInfo['id']))
                 cur.execute("UPDATE `resource_db`.`static_config` SET state='%s' WHERE id='%s'"%("active",hostInfo['config_id']))
                 self.__con.commit()
                 self.logger.info("found a sutable host %s"%hostInfo['hostname']) 
                 return hostInfo
             else:
                 #print ("SELECT * FROM `resource_db`.`host`,`resource_db`.`static_config` WHERE `host`.config_id=`static_config`.id and `host`.state='free' and `static_config`.state='free' and `host`.profile='%s' %s"%(profile, ("and `static_config`.configName ='%s'"%configName if configName!=None else "" )))
                 cur.execute("SELECT * FROM `resource_db`.`host`,`resource_db`.`static_config` WHERE `host`.config_id=`static_config`.id and `host`.state='free' and `static_config`.state='free' and `host`.profile='%s' %s"%(profile, ("and `static_config`.configName ='%s'"%configName if configName!=None else "" )))
                 host=cur.fetchone()
                 if ( host and len(host)):
                     self.logger.info("A host with the given config exists but was not deployed using the given repo, destroying the host and creating a new one")
                     hostInfo=self.getDict(host, cur)
                     self.destroy(hostInfo['hostname'])
                     

   def destroy(self,hostname):
       #print "****in destroy *******"
       if self.__con or self.connect():
          cur =self.__con.cursor(MySQLdb.cursors.DictCursor)
          #print hostname
          #print "SELECT * FROM `resource_db`.`host` WHERE hostname='%s' and state='free'"%hostname
          cur.execute("SELECT * FROM `resource_db`.`host` WHERE hostname='%s' and state='free'"%hostname)
          host= cur.fetchone()
          #print host
          hostInfo=self.getDict(host,cur)
          #print "SELECT * FROM `resource_db`.`static_config` WHERE id='%s'"%hostInfo['config_id']
          cur.execute("SELECT * FROM `resource_db`.`static_config` WHERE id='%s'"%hostInfo['config_id'])
          configInfo=self.getDict(cur.fetchone(),cur)
          self.logger.info("destroying host %s"%hostInfo['hostname'])
          bash("cobbler system remove --name=%s"%hostInfo['hostname'])
          xenssh = \
                  remoteSSHClient(hostInfo['infra_server'],22, "root", hostInfo['infra_server_passwd'])

          self.logger.debug("bash vm-uninstall.sh -n %s"%(hostInfo['hostname']))
          xenssh.execute("xe vm-uninstall force=true vm=%s"%hostInfo['hostname'])
          #print hostInfo
          self.resourceMgr.freeConfig(configInfo['configfile'])
          self.remove(hostInfo['id'])

   def free(self,mgmtHostInfo):
           mgmthost=self.findHostbyMac(mgmtHostInfo['mac'])
           self.update(mgmthost['id'],"state","free")
           self.resourceMgr.freeConfig(mgmtHostInfo['configfile'])        
 
