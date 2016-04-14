from hostResourceMysqlProfiles import poolManager

class testClass:
  def __init__(self):
       self.hostInfo={}
       self.hostInfo.update({'mac':"AE:DE:RE:DF:ED:34",'ip':"10.147.500.10",'repo_url':"dummby",'branch':"master",\
       'domain':"dummyDomain",'hostname':"centos-simulator-dummy",'os':"centos",'password':"password","state":"free","config_id":9,"infra_server":"10.147.28.65", "infra_server_passwd":"password","simulator":'true',"profile":'bharat'})
       print "Init complete" 
  def test(self):
      poolmgr=poolManager()
      print poolmgr
      #poolmgr.addToPool(self.hostInfo)
      hostinfo=poolmgr.findSutableHost("dummby","bharat")
      print "hostinfo", hostinfo
      poolmgr.free(hostinfo)
      poolmgr.update(hostinfo['id'],"state","free")
      poolmgr.remove(hostinfo['id'])



