#!/bin/bash
libdir=/var/lib/cobbler
srcdir=/var/www/cobbler
dstdir=/var/lib/tftpboot
for profile in $( grep -l xenserver6.2 $libdir/config/profiles.d/* ); do
    json=${profile##*/}
    name=${json%.json}
    [[ -d $dstdir/images/$name ]] && \
    rsync -av $srcdir/ks_mirror/$name/{install.img,boot/vmlinuz} \
        $dstdir/images/$name/
done
for file in $( grep -l xen.gz $dstdir/pxelinux.cfg/* ); do
    sed -i'' -e 's!initrd=\(/images/.*/\)\(xen.gz \)ks.*ks=\(.*\)$!\1\2dom0_mem=752M com1=115200,8n1 console=com1,vga --- \1vmlinuz xencons=hvc console=hvc0 console=tty0 answerfile=\3 install --- \1install.img!;' $file
done
ln  /var/www/cobbler/ks_mirror/xenserver6.2/install.img /var/lib/tftpboot/images/xenserver6.2/install.img
ln  /var/www/cobbler/ks_mirror/xenserver6.2/boot/vmlinuz /var/lib/tftpboot/images/xenserver6.2/vmlinuz
service iptables stop
chmod -R a+rx /var/www/cobbler/ks_mirror/ 
