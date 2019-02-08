#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/1/29 3:33 PM
# @Author  : w8ay
# @File    : util.py
import ipaddress
import json
import re
from urllib import parse

from application.api.models import properly


def datetime_string_format(datetime):
    '''
    2019-01-29T13:30:56.625478 => 2019-01-29 13:30:56
    :param datetime:
    :return:
    '''
    res = re.match("(\d+-\d+-\d+)\S(\d+:\d+:\d+)", datetime)
    if res:
        return res.group(1) + " " + res.group(2)
    else:
        return ""


def third_info(ip):
    dd = '''<div class="new-accounts">
            <ul class="chats">
               {ul} 
            </ul>
        </div>'''
    items = {
        "Threakbook": {
            "src": "https://x.threatbook.cn/nodev4/domain/" + ip,
            "img": "https://x.threatbook.cn/nodev4/img/favicon.ico@2c7a1cdc",
            "desc": "微步在线威胁情报社区"
        },
        "Certdb": {
            "src": "https://certdb.com/search?q=" + ip,
            "img": "https://certdb.com/ficon/apple-touch-icon.png",
            "desc": "SSL certificates search engine"
        },
        "Findsubdomains": {
            "src": "https://findsubdomains.com/subdomains-of/" + ip,
            "img": "https://findsubdomains.com/ficon/apple-touch-icon.png",
            "desc": "Find subdomains for security assessment penetration test."
        },
        "Dnsdumper": {
            "src": "https://dnsdumpster.com/",
            "img": "https://dnsdumpster.com/static/favicon.ico",
            "desc": "dns recon and research, find and lookup dns records"
        },
        "Censys": {
            "src": "https://censys.io/ipv4?q=" + ip,
            "img": "https://censys.io/static/img/censys-logo.png",
            "desc": "Censys helps organizations, individuals, and researchers find and monitor every server on the Internet to reduce exposure and improve security."
        }
    }
    uul = ''
    for k, v in items.items():
        uul += '''<li class="chat-persons">
                    <a target="_blank" href="{link}">
                    <span class="pro-pic"><img src="{img}" alt="profile image"></span>
                        <div class="user">
                            <p class="u-name">{k}</p>
                            <p class="u-designation">{desc}</p>
                        </div>
                    </a>
                </li>'''.format(k=k, desc=v["desc"], link=v["src"], img=v["img"])
    return dd.format(ul=uul)


def is_proper(arg, arg_type='ip'):
    m = properly.objects.all()
    r = []
    for tem in m:
        name = tem.name
        id = tem.id
        ips = tem.ips
        ips = ips.splitlines()

        domains = tem.domains
        domains = domains.splitlines()

        if arg_type == "ip":
            for _ip in ips:
                if "*" in _ip:
                    tmp_ip = _ip.replace("*", "")
                    if tmp_ip in arg:
                        return name, id
                elif "/" in _ip:
                    try:
                        net = ipaddress.ip_network(_ip)

                    except:
                        net = None

                    if ipaddress.ip_address(arg) in net:
                        r.append((name, id))
                        continue
                else:
                    if arg in _ip:
                        r.append((name, id))
                        continue

        elif arg_type == "domain":
            for _d in domains:
                if "*" in _d:
                    tmp_d = _d.replace("*", "")
                    if tmp_d in arg:
                        r.append((name, id))
                        continue
                else:
                    if _d in arg:
                        r.append((name, id))
                        continue
    return r


def k2e_search(keyword, page=1):
    '''
    通过解析关键词转换为elasticsearch的搜索语法
    :param keyword:
    :return:

    title=“abc” 从标题中搜索
    header=“abc” 从http头搜索
    body=“” 从body搜索
    url = “*.baidu.com” 搜索baidu.com的子域名
    ip = ‘1.1.1.1’ 搜索ip
    port = ‘搜索端口’
    app = ’nginx’ 搜索组件
    country = ‘cn’ 搜索国家
    service = ‘mysql’ 搜索服务
    '''

    # 转义
    keyword = keyword.replace("\\'", "{zwf_yin}", )
    keyword = keyword.replace("\\\"", "{zwf_shuang}")

    feild = {
        "title": "title",
        "header": "headers",
        "body": "body",
        "url": "url",
        "ip": ["target", "ip"],
        "port": "infos.port",
        "app": "app.keyword",
        "country": "location.country_id",
        "service": "infos.name",
        "bug": "bugs"
    }
    special_feild = {
        ""
    }

    # 解析keyword
    parren = '''(({thumil})\s*=\s*["'](.*?)['"])'''.format(thumil='|'.join(feild.keys()))
    m = re.findall(parren, keyword.strip())
    if not m:
        payload = {"query": {
            "bool": {
                "must": [

                ]
            }
        },
            "from": (page - 1) * 20,
            "size": 20,
            "sort": {"published_from": {"order": "desc"}}
        }
        return payload, None
    must_list = []
    for item in m:
        key = item[1]
        value = item[2]

        value = value.replace("{zwf_yin}", "'")
        value = value.replace("{zwf_shuang}", '"')

        if isinstance(feild[key], list):
            keys = feild[key]
            for i in keys:
                must_list.append({
                    "match": {
                        i: value
                    }
                })
        elif isinstance(feild[key], str):
            if key == "country":
                _payload = {"nested": {
                    "path": "location",
                    "query": {
                        "match": {
                            "location.country_id": value.upper()
                        }
                    }
                }
                }
                must_list.append(_payload)
            elif key == "port" or key == "service":
                _payload = {"nested": {
                    "path": "infos",
                    "query": {
                        "match": {
                            feild[key]: value
                        }
                    }
                }
                }
                must_list.append(_payload)
            elif key == "url":
                must_list.append({
                    "wildcard": {
                        "url": value
                    }
                })
            elif key == "bug":
                if value:
                    value = "." + value
                must_list.append({
                    "exists": {
                        "field": "bugs" + value
                    }
                })
            else:
                must_list.append({
                    "match": {
                        feild[key]: value
                    }
                })

    payload = {"query": {
        "bool": {
            "must": [

            ]
        }
    },
        "from": (page - 1) * 20,
        "size": 20,
        "sort": {"published_from": {"order": "desc"}}
    }
    payload["query"]["bool"]["must"] = must_list
    # print(json.dumps(payload))
    return payload, m


def is_ip_address_format(value):
    IP_ADDRESS_REGEX = r"\b(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\b"
    if value and re.match(IP_ADDRESS_REGEX, value):
        return True
    else:
        return False


def is_url_format(value):
    URL_ADDRESS_REGEX = r"(?:(?:https?):\/\/|www\.|ftp\.)(?:\([-a-zA-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-a-zA-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-a-zA-Z0-9+&@#\/%=~_|$?!:,.]*\)|[a-zA-Z0-9+&@#\/%=~_|$])"
    if value and re.match(URL_ADDRESS_REGEX, value):
        return True
    else:
        return False


def format_convert(arg: str):
    if not arg.startswith("http"):
        if is_ip_address_format(arg):
            return arg
        else:
            return "http://" + arg.split("/")[0]
    else:
        return parse.urlparse(arg)[1]


if __name__ == '__main__':
    import re

    text = r'''title="abc" && ip = '1.1.1.1' '''
    # s = search(text)
    # print(s)