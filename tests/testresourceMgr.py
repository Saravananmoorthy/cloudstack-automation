from hostImager import resourceManager

resourceMgr=resourceManager()
ip1=resourceMgr.getIp()
print "received ip %s"%ip1
ip2=resourceMgr.getIp()
print "received ip %s"%ip2
resourceMgr.freeIp(ip1)
resourceMgr.freeIp(ip2)


