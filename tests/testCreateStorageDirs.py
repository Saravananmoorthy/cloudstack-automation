from hostImagerProfiles import hostImager
sstor="nfs://nfs-server.automation.hyd.com:/export/automation/1/z0primary1"
hi=hostImager()
class primaryStorage():
      pass

a=primaryStorage()
a.url=sstor
hi.createStorageDirs(a)
