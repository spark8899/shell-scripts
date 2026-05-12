#!/usr/bin/env bash
#Crontab
# */30 * * * * if /etc/node_exporter/scripts/check_ssl.sh > /etc/node_exporter/ssl.prom.$$; then mv /etc/node_exporter/ssl.prom.$$ /etc/node_exporter/ssl.prom; else rm /etc/node_exporter/ssl.prom.$$;fi

check_list="domain01:serverAddr domain02:serverAddr domain03:serverAddr"

for i in $check_list
do
  domain=$(echo $i | awk -F":" '{print $1}')
  host=$(echo $i | awk -F":" '{print $2}')
  ssl_after=`echo | /usr/bin/openssl s_client -servername $domain -connect $host:443 2>/dev/null | /usr/bin/openssl x509 -noout -dates | tail -1 | awk -F"=" '{print $NF}'`
  data=`date +%s -d "$ssl_after"`
  today=`date +%s`
  expired_day=$((($data - $today)/86400))
  echo domain_ssl_expired{domain=\"$domain\", host=\"$host\"} $expired_day
done
