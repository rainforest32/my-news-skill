#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from optparse import OptionParser
import random
import os
import time
import datetime

if sys.version_info[0] < 3:
    defaultEncoding = 'utf-8'
    if sys.getdefaultencoding != defaultEncoding:
        reload(sys)
        sys.setdefaultencoding(defaultEncoding)

def usage():
    parser = OptionParser()
    parser.add_option('--source', dest = 'source', default = '')
    (options, _) = parser.parse_args()
    return options

def get_real_browser_html(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        # 启动：无头+伪装真实浏览器
        browser = p.chromium.launch(
            headless=True,  # 后台运行，看不到窗口
            slow_mo=500     # 模拟人浏览延迟，更像真人
        )
        # 新建页面，伪装参数
        context = browser.new_context(
            # 真实成人UA
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},  # 真实分辨率
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://www.baidu.com/"
            }
        )
        page = context.new_page()
        
        # 访问网站，等待网络空闲（完全加载渲染）
        page.goto(url, wait_until="networkidle")
        
        # 获取渲染后完整HTML
        html = page.content()
        browser.close()
        return html


def fetch_xiaohongshu_hot(options):
    # https://rebang.today/?tab=xiaohongshu
    import json
    import re
    from bs4 import BeautifulSoup

    html = get_real_browser_html('https://rebang.today/?tab=xiaohongshu')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    rank = 0
    for a in soup.select('a[href*="xiaohongshu.com/search_result"]'):
        href = a.get('href', '')
        # 锚点文本包含标题，可能末尾带"热"字标签
        raw_text = a.get_text(separator=' ', strip=True)
        title = re.sub(r'\s*热\s*$', '', raw_text).strip()
        if not title:
            continue

        # 热度值在锚点的父级兄弟节点中，格式如 "935.1w"
        heat = ''
        parent = a.parent
        if parent:
            siblings_text = parent.get_text(separator='|', strip=True)
            heat_match = re.search(r'([\d.]+w)', siblings_text)
            if heat_match:
                heat = heat_match.group(1)

        is_hot = '热' in a.get_text()
        rank += 1
        items.append({
            'rank': rank,
            'title': title,
            'url': href,
            'heat': heat,
            'is_hot': is_hot,
            'source': '小红书热榜',
            'time': 'Real-time',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))


def main():
    options = usage()
    if options.source == '':
        print('please provide source', file=sys.stderr)
        sys.exit(-1)
    support_sources = set(['xiaohongshu_hot'])
    if options.source not in support_sources:
        print('unsupported source: %s' % options.source, file=sys.stderr)
        sys.exit(-1)

    if options.source == 'xiaohongshu_hot':
        fetch_xiaohongshu_hot(options)

if __name__ == '__main__':
    main()