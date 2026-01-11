#!/usr/bin/env bash
#Usage: init centos 6.
#Created by spark <park8888@gmail.com> 2014-12-04
#Last Modified:

PWD=$(pwd)
HOSTNAME=`hostname`
IPADDR=`ip a | grep "global eth0" | awk '{print $2}' | awk -F "/" '{print $1}'`
GATEWAY=`netstat -rn | grep UG | awk '{print $2}'`


#Change motd
cat > /etc/motd << "EOF"
            ____             ___              __             ______
           / __ \           /   |            / /            / ____/
          / / / /          / /| |           / /            / __/
         / /_/ /          / __  |          / /___         / /___
        /_____/          /_/  |_|         /_____/        /_____/
 
Hostname: hostname-all
Date of Deployment: deploy-date

EOF

#sed -i -e "s/hostname-all/`hostname`/" /etc/motd
sed -i -e "s/hostname-all/$HOSTNAME/" /etc/motd
sed -i -e "s/deploy-date/`stat /lost+found/ | grep Modify | awk '{print $2}'`/" /etc/motd


#Change hostname
cat > /etc/sysconfig/network << "EOF"
NETWORKING=yes
HOSTNAME=hostname-all
GATEWAY=gateway
NOZEROCONF=yes
EOF

sed -i -e "s/hostname-all/$HOSTNAME/" /etc/sysconfig/network
sed -i -e "s/gateway/$GATEWAY/" /etc/sysconfig/network


#Change eth0
cat > /etc/sysconfig/network-scripts/ifcfg-eth0  << "EOF"
DEVICE=eth0
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=none
IPADDR=ipaddr
PREFIX=24
GATEWAY=gateway
IPV6INIT=no
EOF

sed -i -e "s/ipaddr/$IPADDR/" /etc/sysconfig/network-scripts/ifcfg-eth0
sed -i -e "s/gateway/$GATEWAY/" /etc/sysconfig/network-scripts/ifcfg-eth0


#Change repo
mv -f /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup

cat > /etc/yum.repos.d/CentOS-Base.repo << "EOF"
# CentOS-Base.repo
#
# The mirror system uses the connecting IP address of the client and the
# update status of each mirror to pick mirrors that are updated to and
# geographically close to the client.  You should use this for CentOS updates
# unless you are manually picking other mirrors.
#
# If the mirrorlist= does not work for you, as a fall back you can try the
# remarked out baseurl= line instead.
#
#

[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/os/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=os
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#released updates
[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/updates/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=updates
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#additional packages that may be useful
[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/extras/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=extras
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/centosplus/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=centosplus
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6

#contrib - packages by Centos Users
[contrib]
name=CentOS-$releasever - Contrib - mirrors.aliyun.com
failovermethod=priority
baseurl=http://mirrors.aliyun.com/centos/$releasever/contrib/$basearch/
        http://mirrors.aliyuncs.com/centos/$releasever/contrib/$basearch/
#mirrorlist=http://mirrorlist.centos.org/?release=$releasever&arch=$basearch&repo=contrib
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-6
EOF

if [ -f /etc/yum.repos.d/epel.repo ]; then 
  mv -f /etc/yum.repos.d/epel.repo /etc/yum.repos.d/epel.repo.backup
fi

if [ -f /etc/yum.repos.d/epel-testing.repo ]; then 
  mv -f /etc/yum.repos.d/epel-testing.repo /etc/yum.repos.d/epel-testing.repo.backup
fi

cat > /etc/yum.repos.d/epel.repo << "EOF"
[epel]
name=Extra Packages for Enterprise Linux 6 - $basearch
baseurl=http://mirrors.aliyun.com/epel/6/$basearch
        http://mirrors.aliyuncs.com/epel/6/$basearch
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
failovermethod=priority
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6

[epel-debuginfo]
name=Extra Packages for Enterprise Linux 6 - $basearch - Debug
baseurl=http://mirrors.aliyun.com/epel/6/$basearch/debug
        http://mirrors.aliyuncs.com/epel/6/$basearch/debug
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-debug-6&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0

[epel-source]
name=Extra Packages for Enterprise Linux 6 - $basearch - Source
baseurl=http://mirrors.aliyun.com/epel/6/SRPMS
        http://mirrors.aliyuncs.com/epel/6/SRPMS
#mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-source-6&arch=$basearch
failovermethod=priority
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6
gpgcheck=0
EOF

#Change sysctl
cat > /etc/sysctl.conf << "EOF"
# Kernel sysctl configuration file for Red Hat Linux
net.ipv4.ip_forward = 1
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.default.accept_source_route = 0
kernel.sysrq = 0
kernel.core_uses_pid = 1
net.ipv4.tcp_syncookies = 1
net.bridge.bridge-nf-call-ip6tables = 0
net.bridge.bridge-nf-call-iptables = 0
net.bridge.bridge-nf-call-arptables = 0
kernel.msgmnb = 65536
kernel.msgmax = 65536
kernel.shmmax = 68719476736
kernel.shmall = 4294967296
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.ip_local_port_range = 1025 65000
net.ipv4.tcp_max_syn_backlog = 20480
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_max_tw_buckets = 300000
net.ipv4.tcp_timestamps = 0
net.core.wmem_default = 8388608
net.core.rmem_default = 8388608
net.core.wmem_max = 16777216
net.core.rmem_max = 16777216
net.ipv4.tcp_rmem = 10240 87380 16777216
net.ipv4.tcp_wmem = 10240 87380 16777216
net.core.netdev_max_backlog = 50000
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_max_orphans = 3276800
net.core.somaxconn = 3276800
vm.swappiness = 10
net.ipv6.conf.all.disable_ipv6 = 1 
EOF


#Setting DNS
echo "# Generated by NetworkManager" > /etc/resolv.conf
echo "nameserver 202.96.209.5" >> /etc/resolv.conf
echo "nameserver 202.96.209.133" >> /etc/resolv.conf


#Close selinux
sed -i -e "s/^SELINUX=enforcing/SELINUX=disabled/" /etc/selinux/config 


#Close iptables netfs
chkconfig ip6tables off
chkconfig iptables off
chkconfig netfs off


#Update system
yum makecache
yum -y update
yum install parted ntp wget traceroute telnet openssh-clients bind-utils lsof man mailx vim git svn -y

echo "*/30 * * * * /usr/sbin/ntpdate 192.168.100.61" >> /var/spool/cron/root
chmod 600 /var/spool/cron/root

echo "127.0.0.1   localhost" > /etc/hosts

rm -rf /root/anaconda-ks.cfg
rm -rf /root/install.log
rm -rf /root/install.log.syslog
rm -rf $PWD/$0

reboot
exit 0
