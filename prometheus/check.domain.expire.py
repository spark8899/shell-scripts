#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pip3 install python3-whois
# 11 11 * * * if /etc/node_exporter/scripts/check.domain.expire.py > /etc/node_exporter/domain_expire.prom.$$; then mv /etc/node_exporter/domain_expire.prom.$$ /etc/node_exporter/domain_expire.prom; else rm /etc/node_exporter/domain_expire.prom.$$;fi

import whois, time, sys
from datetime import datetime

domain_list = ["google.com", "aws.com"]

def get_domain_expire(domain):
    try:
        w = whois.whois(domain)
        expiry = w.expiration_date
        if isinstance(expiry, list):
            expiry = expiry[0]
        if expiry:
            days_left = (expiry.replace(tzinfo=None) - datetime.now().replace(tzinfo=None)).days
            domain_expiration = expiry.date()
            return [domain_expiration, days_left]
        else:
            print(f"{domain} Unable to obtain expiration time.")
    except Exception as e:
        print(f"{domain} query failed.")
        sys.exit(1)

if __name__ == '__main__':
    for domain in domain_list:
        expire_info = get_domain_expire(domain)
        print("domain_register_expire{domain=\"%s\", expiration=\"%s\"} %s" % (domain, expire_info[0], expire_info[1]))
        time.sleep(2)
