from testEnv import testEnv

hostInfo={'mac':'00:16:3e:3c:ec:8d','password':'password','hostname':'centos-simulator-00-16-3e-3c-ec-8d','ip':'10.147.28.143'} 
print hostInfo['ip']
t=testEnv()
env=t.create(hostInfo,"100")
t.execTests(env)

