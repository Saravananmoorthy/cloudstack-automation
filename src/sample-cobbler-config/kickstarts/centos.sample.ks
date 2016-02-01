#platform=x86, AMD64, or Intel EM64T
# System authorization information
auth  --useshadow  --enablemd5
# System bootloader configuration
bootloader --location=mbr
network --bootproto=dhcp --device=eth0
# Partition clearing information
clearpart --all --initlabel
# Use text mode install
text
# Firewall configuration
firewall --enabled
# Run the Setup Agent on first boot
firstboot --disable
# System keyboard
keyboard us
# System language
lang en_US
# Use network installation
url --url=$tree
# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
$yum_repo_stanza
# Network information
$SNIPPET('network_config')
# Reboot after installation
reboot

#Root password
rootpw password
# SELinux configuration
selinux --disabled
# Do not configure the X Window System
skipx
# System timezone
timezone  --utc America/Los_Angeles
# Install OS instead of upgrade
install
# Clear the Master Boot Record
zerombr
# Allow anaconda to partition the system as needed
autopart


%pre
$SNIPPET('log_ks_pre')
$SNIPPET('kickstart_start')
$SNIPPET('pre_install_network_config')
# Enable installation monitoring

$SNIPPET('pre_anamon')

%packages
@Base
ruby-libs
ruby-rdoc
nscd

$SNIPPET('puppet_install_if_enabled')


%post
$SNIPPET('log_ks_post')
#ntpdate cobblerbvt.automation.test.com
ntpdate 10.223.90.200
wget -O /etc/puppet/puppet.conf http://cobblerbvt.automation.hyd.com/puppet.conf
# Start yum configuration 
$yum_config_stanza
# End yum configuration
$SNIPPET('post_install_kernel_options')
$SNIPPET('post_install_network_config')
$SNIPPET('download_puppet_config')
$SNIPPET('func_register_if_enabled')
$SNIPPET('koan_environment')
$SNIPPET('proxy_environment')
$SNIPPET('redhat_register')
$SNIPPET('cobbler_register')
$SNIPPET('inject_keys')

# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('kickstart_done')
# End final steps
