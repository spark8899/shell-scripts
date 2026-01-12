#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pip3 install requests
# */10 * * * * if /etc/node_exporter/scripts/check.website.py > /etc/node_exporter/website_up.prom.$$; then mv /etc/node_exporter/website_up.prom.$$ /etc/node_exporter/website_up.prom; else rm /etc/node_exporter/website_up.prom.$$;fi

import requests, sys

def check_website(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return 0
        else:
            return response.status_code
    except requests.RequestException as e:
        print(f"Error checking {url}: {e}", sys.stderr)
        return 0

def main():
    websites = [
        "www-google-com:https://www.google.com",
        "www-aws-com:https://www.aws.com"
    ]
    for website in websites:
        name, url = website.split(":", 1)
        result = check_website(url)
        print(f'website_up{{name="{name}", url="{url}"}} {result}')

if __name__ == "__main__":
    main()
