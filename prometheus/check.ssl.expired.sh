#!/usr/bin/env bash
#Crontab
# */30 * * * * if /etc/node_exporter/scripts/check.ssl.expired.sh > /etc/node_exporter/ssl_expired.prom.$$; then mv /etc/node_exporter/ssl_expired.prom.$$ /etc/node_exporter/ssl_expired.prom; else rm /etc/node_exporter/ssl_expired.prom.$$;fi

check_list="www.google.com:www.google.com google.io:google.io"

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
