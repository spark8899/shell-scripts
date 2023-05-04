# Kickstart file for virtual server (CentOS 6.6 x86_64), Version 0.1
# General Install Section=================================================Begin
install
url --url=http://10.100.0.10/centos6_repo
lang en_US.UTF-8
keyboard us
text
skipx
# General Install Section=================================================End


# Localization Section====================================================Begin
timezone --utc Asia/Shanghai
# Localization Section====================================================End


# Network Configuration===================================================Begin
#network --device eth0 --bootproto dhcp --hostname localhost.idc.pplive.cn --onboot=yes --noipv6
network --onboot yes --device eth0 --mtu=1500 --bootproto static --ip 10.100.0.13 --netmask 255.255.255.0 --gateway 10.100.0.254 --noipv6 --hostname test-0-13.test.dalegames.com
# Network Configuration===================================================End


# Security Section========================================================Begin
rootpw  --iscrypted $6$i1C6aBNpZGZYhRi9$fXZtlY1LKoq0IF0NPeJagVfLIPYX5pIhgvavz/3rJP.1.B/WSE.RJ.x7x3aLu9aCOLPv.7.oiHA5grQI7L26S0
authconfig --enableshadow --passalgo=sha512
firewall --disabled
selinux --disabled
reboot --eject
# Security Section========================================================End


# Disk/Partitioning Section===============================================Begin
zerombr
bootloader --location=mbr --driveorder=vda --append="crashkernel=auto rhgb quiet"
clearpart --all --drives=vda --initlabel
part /boot --fstype=ext4 --asprimary --size=500
part / --fstype=ext4 --asprimary --size=30720
part swap --asprimary --size=4096
part /home --fstype=ext4 --grow --asprimary --size=200
# Disk/Partitioning Section===============================================End


# Package Section=========================================================Begin
%packages --nobase
telnet
wget
vim
lvm2
parted
ntp
traceroute
openssh-clients
lsof
man
bind-utils
mailx
svn
git
sysstat
# Package Section=========================================================End
%end



# Postconfig Section
%post


# Disable Needless Services===============================================Begin
/sbin/chkconfig --level 0123456 auditd off
/sbin/chkconfig --level 0123456 ip6tables off
/sbin/chkconfig --level 0123456 iptables off
/sbin/chkconfig --level 0123456 iscsi off
/sbin/chkconfig --level 0123456 iscsid off
/sbin/chkconfig --level 0123456 lvm2-monitor off
/sbin/chkconfig --level 0123456 mdmonitor off
/sbin/chkconfig --level 0123456 postfix off
/sbin/chkconfig --level 0123456 netfs off
/sbin/chkconfig --level 0123456 udev-post off
# Disable Needless Services===============================================End


# Display Command excute time=============================================Begin
cat >> /etc/bashrc<< "EOF"
export HISTTIMEFORMAT='%Y-%m-%d %H:%M:%S '
EOF
# Display Command excute time=============================================End

 
# Service Type specific options===========================================Begin
/bin/cat > /etc/motd << "EOF"                                          
            ____             ___              __             ______
           / __ \           /   |            / /            / ____/
          / / / /          / /| |           / /            / __/
         / /_/ /          / __  |          / /___         / /___
        /_____/          /_/  |_|         /_____/        /_____/
 
Hostname: test-0-13.test.dalegames.com
PHY Serv: ser4.test.dalegames.com

EOF
echo -e "Date of Deployment: `date +%F`" >> /etc/motd
echo -e "" >> /etc/motd
# Service Type specific options===========================================End


# YUM Configuration=======================================================Begin
rm -rf  /etc/yum.repos.d/*.repo
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
# YUM Configuration=======================================================End


# file notification setting===============================================Begin
cat >> /etc/security/limits.conf << "EOF"
*    -     nofile    1000000
EOF
# file notification setting===============================================End


# Kernel setting==========================================================Begin
cat > /etc/sysctl.conf << "EOF"
# Kernel sysctl configuration file for Red Hat Linux
net.ipv4.ip_forward = 0
net.ipv4.conf.default.rp_filter = 1
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
# Kernel setting==========================================================End


#disable ctrl alt del=====================================================Begin
sed -i -e '/exec/s/exec/#exec/' /etc/init/control-alt-delete.conf
#disable ctrl alt del=====================================================End


#SSH Setting==============================================================Begin
sed -i -e 's/#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/' /etc/ssh/sshd_config
#SSH Setting==============================================================End


#Time update setting======================================================Begin
echo "*/30 * * * * /usr/sbin/ntpdate 192.168.100.61" >> /var/spool/cron/root
#Time update setting======================================================End

#Creating some default dirctoris==========================================Begin
mkdir -p /usr/local/scripts
mkdir -p /home/logs
#Creating some default dirctoris==========================================End


#Adding DNS===============================================================Begin
cat > /etc/resolv.conf << "EOF"
nameserver 202.96.209.5
nameserver 202.96.209.133
EOF
#Adding DNS===============================================================End


#Changing cron job of sysstat=============================================Begin
sed -i '/*\/10/s/*\/10/*/' /etc/cron.d/sysstat
#Changing cron job of sysstat=============================================End


#Changing search domain===================================================Begin
cat > /etc/sysconfig/network << "EOF"
NETWORKING=yes
HOSTNAME=test-0-13.test.dalegames.com
GATEWAY=10.100.0.254
NOZEROCONF=yes
EOF
#Changing search domain===================================================End


#Virtual server console setting===========================================Begin
echo "ttyS0" >> /etc/securetty
echo "S0:12345:respawn:/sbin/agetty ttyS0 115200" >> /etc/inittab
sed -i -e  's/crashkernel=auto/crashkernel=auto\ console=ttyS0,115200/' /boot/grub/grub.conf
#Virtual server console setting===========================================End


#Log Setting==============================================================Begin
cat >> /etc/profile << "EOFFF"

history
USER_IP=`who -u am i 2>/dev/null| awk '{print $NF}'|sed -e 's/[()]//g'`
if [ "$USER_IP" = "" ]
then
USER_IP=`hostname`
fi
if [ ! -d /var/history ]
then
mkdir -p /var/history
chmod 777 /var/history
fi
if [ ! -d /var/history/${LOGNAME} ]
then
mkdir /var/history/${LOGNAME}
chmod 300 /var/history/${LOGNAME}
fi
export HISTSIZE=10000
DT=`date +"%Y%m%d_%H%M%S"`
export HISTFILE="/var/history/${LOGNAME}/${USER_IP}_history.$DT"
chmod 400 /var/history/${LOGNAME}/*history* 2>/dev/null
chattr +i /var/history/${LOGNAME}/*history* 2>/dev/null
EOFFF
#Log Setting==============================================================End


#NETWORK Setting==========================================================Begin
cat > /etc/sysconfig/network-scripts/ifcfg-eth0 << "EOF"
DEVICE=eth0
TYPE=Ethernet
ONBOOT=yes
BOOTPROTO=static
IPADDR=10.100.0.13
PREFIX=24
IPV6INIT=no
EOF
#NETWORK Setting==========================================================End


#Host Setting=============================================================Begin
echo "127.0.0.1   localhost" > /etc/hosts
#Host Setting=============================================================End


#Other clean==============================================================Begin
rm -rf /root/anaconda-ks.cfg
rm -rf /root/install.log
rm -rf /root/install.log.syslog
#Other clean==============================================================End



%end
#Change log.
#Created this kickstart file. spark <spark@dlmes.com>, 2015-01-13, Version: 0.1
