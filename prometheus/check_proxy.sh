#!/bin/bash
#Crontab
# */1 * * * * if /etc/node_exporter/scripts/check.proxy.sh > /etc/node_exporter/proxy_status.prom.$$; then mv /etc/node_exporter/proxy_status.prom.$$ /etc/node_exporter/proxy_status.prom; else rm /etc/node_exporter/proxy_status.prom.$$;fi

SERVICES=(
    "3proxy:3proxy:1080,8080"
    "squid:squid:3128"
)

for entry in "${SERVICES[@]}"; do
    IFS=':' read -r APP_NAME PROC_NAME PORTS <<< "$entry"
    PID=$(pgrep -o -x "$PROC_NAME")
    IFS=',' read -r -a PORT_ARRAY <<< "$PORTS"
    for PORT in "${PORT_ARRAY[@]}"; do
        STATUS=$(ss -tuln | grep -q ":$PORT " && echo 1 || echo 0)
	CURRENT_PID=${PID:-0}
	echo "app{name=\"$APP_NAME\",port=\"$PORT\",PID=\"$CURRENT_PID\"} $STATUS"
    done
done
