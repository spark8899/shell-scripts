#!/bin/bash

# Check root and args
if [[ $EUID -ne 0 ]]; then echo "Error: Run as root"; exit 1; fi
if [[ -z "$1" ]]; then echo "Usage: $0 <hostname>"; exit 1; fi

NEW_HOSTNAME=$1

echo ">> 1. Setting Hostname..."
hostnamectl set-hostname "$NEW_HOSTNAME"
sed -i "s/127.0.0.1.*localhost/127.0.0.1 localhost $NEW_HOSTNAME/g" /etc/hosts

echo ">> 2. Disabling APT Auto-Updates..."
# Disable the service timers immediately to prevent lock contention
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer
# Update config to ensure it stays disabled
cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APT::Periodic::Unattended-Upgrade "0";
EOF

echo ">> 3. Updating System & Installing Tools..."
apt update && apt upgrade -y
apt install -y net-tools curl htop jq iotop lrzsz lsof tree telnet python3.12-venv

echo ">> 4. Configuring Environment..."
cat >> /etc/profile <<EOF

# Added by init script
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
export HISTTIMEFORMAT="%F %T \`whoami\` "
EOF
source /etc/profile

echo ">> 5. Optimizing Kernel (Sysctl)..."
cp /etc/sysctl.conf /etc/sysctl.conf.bak
cat > /etc/sysctl.conf <<EOF
fs.file-max=1048576
net.core.somaxconn=65535
net.core.netdev_max_backlog=300000
net.core.rmem_default=1342177
net.core.rmem_max=16777216
net.core.wmem_default=1342177
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 1342177 16777216
net.ipv4.tcp_wmem=4096 1342177 16777216
net.ipv4.tcp_fin_timeout=10
net.ipv4.tcp_keepalive_time=1200
net.ipv4.tcp_keepalive_intvl=30
net.ipv4.tcp_keepalive_probes=3
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_tw_reuse=1
net.ipv4.ip_local_port_range=10000 65535
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF
sysctl -p

echo ">> 6. Setting Limits..."
cp /etc/security/limits.conf /etc/security/limits.conf.bak
cat > /etc/security/limits.conf <<EOF
root hard nofile 1048576
root soft nofile 1048576
* hard nofile 1038576
* soft nofile 1038576

root soft nproc -1
root hard nproc -1
* soft nproc -1
* hard nproc -1

root soft stack 512000
root hard stack 512000
* soft stack 512000
* hard stack 512000
EOF

echo ">> Done! Please reboot to finalize changes."
