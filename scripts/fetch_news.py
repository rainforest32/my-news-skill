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

def fetch_zhihu_hot(options):
    # https://rebang.today/?tab=zhihu
    import json
    import re
    from bs4 import BeautifulSoup

    html = get_real_browser_html('https://rebang.today/?tab=zhihu')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()
    # 空文本锚点的 parent 包含完整行信息: rank|[tag]|title|title|desc|XX万热度
    for a in soup.select('a[href*="zhihu.com/question"]'):
        href = a.get('href', '')
        if href in seen:
            continue
        if a.get_text(strip=True):
            continue  # 跳过带文本的链接，用空链接的 parent 取完整行
        seen.add(href)

        parent = a.parent
        row_text = parent.get_text(separator='|', strip=True) if parent else ''
        parts = [p.strip() for p in row_text.split('|') if p.strip()]
        if not parts:
            continue

        # 热度: 最后一个元素包含 "万热度"
        heat = ''
        if parts and '万热度' in parts[-1]:
            heat = parts[-1]

        # 排名: 第一个数字
        rank_str = parts[0] if parts[0].isdigit() else ''

        # 标签: 第二个元素可能是 "新"/"热"/"荐" 等短标签
        tag = ''
        title_start = 1
        if len(parts) > 1 and len(parts[1]) <= 2 and not parts[1][0].isdigit():
            tag = parts[1]
            title_start = 2

        title = parts[title_start] if len(parts) > title_start else ''

        # 摘要: title 之后、heat 之前的非重复文本
        desc = ''
        if len(parts) > title_start + 2:
            # parts: ...title, title_dup, desc_text, heat
            desc_parts = parts[title_start + 1:-1]
            # 去掉与 title 重复的部分
            desc_parts = [p for p in desc_parts if p != title]
            desc = ' '.join(desc_parts).strip()

        items.append({
            'rank': int(rank_str) if rank_str else len(items) + 1,
            'title': title,
            'url': href,
            'heat': heat,
            'tag': tag,
            'description': desc[:200] if desc else '',
            'source': '知乎热榜',
            'time': 'Real-time',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))

def fetch_weibo_hot(options):
    # https://s.weibo.com/top/summary?cate=realtimehot
    import json
    import re
    from bs4 import BeautifulSoup

    html = get_real_browser_html('https://rebang.today/?tab=weibo')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()
    for a in soup.select('a[href*="s.weibo.com/weibo?q="]'):
        href = a.get('href', '')
        if not href or href in seen:
            continue
        seen.add(href)

        row_text = a.get_text(separator='|', strip=True)
        parts = [part.strip() for part in row_text.split('|') if part.strip()]
        if len(parts) < 3:
            continue

        rank_str = parts[0] if parts[0].isdigit() else ''
        title = parts[1] if len(parts) > 1 else ''
        tag = ''
        heat = ''

        for part in parts[2:]:
            if part.startswith('热度值：'):
                heat = part
            else:
                tag = part

        heat_value = ''
        if heat:
            heat_match = re.search(r'热度值：\s*(\d+)', heat)
            if heat_match:
                heat_value = heat_match.group(1)

        items.append({
            'rank': int(rank_str) if rank_str else len(items) + 1,
            'title': title,
            'url': href,
            'heat': heat,
            'heat_value': heat_value,
            'tag': tag,
            'source': '微博热搜',
            'time': 'Real-time',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))

def main():
    options = usage()
    if options.source == '':
        print('please provide source', file=sys.stderr)
        sys.exit(-1)
    support_sources = set(['xiaohongshu_hot', 'zhihu_hot', 'weibo_hot'])
    if options.source not in support_sources:
        print('unsupported source: %s' % options.source, file=sys.stderr)
        sys.exit(-1)
    exec('fetch_%s(options)' % options.source)

if __name__ == '__main__':
    main()