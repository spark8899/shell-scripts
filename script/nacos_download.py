#!/bin/python3
import requests, json, zipfile
from pathlib import Path

domain = 'http://nacos_url:8848'
username = 'nacos'
password = 'nacos'
tenant = 'xxx-xxxx-xxx-xxxxxx'

def get_token(domain, username, password):
    url = f"{domain}/nacos/v1/auth/users/login"
    headers = {'Accept': 'application/json;charset=utf-8'}
    data = {'username': username, 'password': password}
    response = requests.post(url, headers=headers, data=data)
    req = response.json()
    return req

def get_config(domain, token, tenant, pageSize=500):
    url = f"{domain}/nacos/v1/cs/configs"
    headers = {'Accept': 'application/json;charset=utf-8'}
    params = {
        "dataId": '',
        "group": '',
        "pageNo": 1,
        "pageSize": pageSize,
        "tenant": tenant,
        "search": "accurate",
        "accessToken": token
    }
    response = requests.get(url, headers=headers, params=params)
    req = response.json()
    return req

def main():
    token = get_token(domain, username, password)['accessToken']
    req = get_config(domain, token, tenant)
    json_object = req['pageItems']
    for i in json_object:
        tmp_directory = Path("tmp")
        group_directory = tmp_directory / i['group']
        group_directory.mkdir(parents=True, exist_ok=True)
        obj_path = group_directory / i['dataId']
        with open(obj_path, "w") as f:
            f.write(i['content'])
    zip_file_path = Path("tmp.zip")
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in tmp_directory.rglob('*'):
            zipf.write(file, arcname=file.relative_to(tmp_directory))
    print("all done.")

if __name__ == '__main__':
    main()
