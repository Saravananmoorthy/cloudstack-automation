from marvin import configGenerator

config=configGenerator.getSetupConfig('/root/cloud-autodeploy2/newcode/config-templates/advanced-xen-2cluster.cfg')

for zone in config.zones:
                 print "zone :",zone.name
                 for pod in zone.pods:
                     print "pod :",pod.name
                     for cluster in pod.clusters:
                         for host in cluster.hosts:
                             print host.url
                         print "cluster :", cluster.hypervisor
                         print "creating a jeknins job to generate results and email notfication for hypervisor %s and zone %s"%(cluster.hypervisor, zone.name)
