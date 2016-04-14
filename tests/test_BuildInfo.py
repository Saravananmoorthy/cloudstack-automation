from hostImagerProfiles import resourceManager
env={'build_number':'101','repo_url':'dummy','branch':'4.4-froward','commit_id':'8923471423047800','hypervisor':'dummyh'}
resourceMgr=resourceManager()
#resourceMgr.addBuildInfo(env)
print resourceMgr.getLastBuildInfo(env['repo_url'], env['branch'], env['hypervisor'])

