import pp_primp
from curl_cffi import Session



chrome_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "ddd": "?1",
    "sec-fetch-dest": "document",
    "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-HK;q=0.7",
    "priority": "u=0, i",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/145.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "te": "trailers"
}
safari_headers = {
    "sec-fetch-dest": "document",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "sec-fetch-site": "none",
    "sec-fetch-mode": "navigate",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "priority": "u=0, i",
    "Accept-Encoding": "gzip, deflate, br",
    "custom-safari-header": "test-value",  # 自定义header
}
cookies = {
    'sdfas':'ddd',
    'swqrttwe':'ddd'
}
session = pp_primp.Client(impersonate='chrome_143',impersonate_os='windows')
# res = session.get('https://tls.peet.ws/api/all',verify=False,headers=safari_headers,cookies=cookies)


# res = session.get('https://47.113.101.23:4442/')


# res = session.get('https://fanpa.weneedstudy.cn:8443/complexTest')
res = session.get('https://tls.browserleaks.com/')
# res = session.get('https://tls.tsvmp.com:38080/cbbiyhh',verify=False,headers=safari_headers,cookies=cookies)
# res = session.get('https://tls.jsvmp.top:38080',split_cookie=True)


# session = Session(headers=chrome_headers)
# session.impersonate='chrome136'
# session.verify=False
# res = session.get('https://47.113.101.23:4442/')

print(res.text)


