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

# 小红书热点
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

# 知乎热点
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

# 微博热点
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

# 腾讯新闻
def fetch_tencent_news(options):
    # https://news.qq.com
    import json
    from bs4 import BeautifulSoup

    html = get_real_browser_html('https://news.qq.com')

    soup = BeautifulSoup(html, 'html.parser')

    items = []

    featured_rank = 0
    for card in soup.select('.channel-hot-item'):
        article_link = card.select_one('a.article-base-info[href]')
        if not article_link:
            continue

        title_node = card.select_one('.article-title-text')
        title = title_node.get_text(strip=True) if title_node else ''
        if not title:
            continue

        tag_node = card.select_one('.qqcom-article-tag .tag-wrap')
        media_node = card.select_one('.author-info .media-name span')
        time_node = card.select_one('.author-info .time')

        featured_rank += 1
        items.append({
            'section': '热点精选',
            'rank': featured_rank,
            'title': title,
            'url': article_link.get('href', ''),
            'source_name': media_node.get_text(strip=True) if media_node else '',
            'time': time_node.get_text(strip=True) if time_node else '',
            'tag': tag_node.get_text(strip=True) if tag_node else '',
            'source': '腾讯新闻',
        })

    normal_rank = 0
    for card in soup.select('.channel-feed-item'):
        article_link = card.select_one('a.article-title[href]')
        if not article_link:
            continue

        title_node = card.select_one('.article-title-text')
        title = title_node.get_text(strip=True) if title_node else ''
        if not title:
            continue

        media_node = card.select_one('.article-media .media-name span')
        time_node = card.select_one('.article-media .time')
        comment_node = card.select_one('a.article-comment')

        normal_rank += 1
        items.append({
            'section': '普通新闻',
            'rank': normal_rank,
            'title': title,
            'url': article_link.get('href', ''),
            'source_name': media_node.get_text(strip=True) if media_node else '',
            'time': time_node.get_text(strip=True) if time_node else '',
            'comment_count': comment_node.get_text(strip=True) if comment_node else '',
            'source': '腾讯新闻',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))

# 网易新闻
def fetch_163_news(options):
    # https://m.163.com/touch/news
    import json
    from bs4 import BeautifulSoup

    html = get_real_browser_html('https://m.163.com/touch/news')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()
    for art in soup.select('article'):
        parent_a = art.find_parent('a')
        if not parent_a:
            continue
        href = parent_a.get('href', '').strip()
        if not href or href in seen:
            continue
        if href.startswith('/'):
            href = 'https://www.163.com' + href
        seen.add(href)

        h4 = art.select_one('h4')
        title = h4.get_text(strip=True) if h4 else ''
        if not title:
            continue

        source_node = art.select_one('.s-source')
        reply_node = art.select_one('.s-replyCount')

        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': href,
            'source_name': source_node.get_text(strip=True) if source_node else '',
            'reply_count': reply_node.get_text(strip=True) if reply_node else '',
            'source': '网易新闻',
            'section': '要闻',
            'time': 'Real-time',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))

# 搜狐新闻
def fetch_sohu_news(options):
    # https://m.sohu.com/limit/
    import json
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse, urlunparse

    html = get_real_browser_html('https://m.sohu.com/limit/')
    soup = BeautifulSoup(html, 'html.parser')

    section = soup.select_one('section[data-spm="fd-important"]')
    items = []
    seen = set()
    for rank, div in enumerate(section.select('div.f'), start=1):
        a = div.select_one('a[href*="sohu.com/a/"]')
        if not a:
            continue
        href = a.get('href', '')
        # strip query params
        parsed = urlparse(href)
        url = urlunparse(parsed._replace(query='', fragment=''))
        if url in seen:
            continue
        seen.add(url)
        title = a.get_text(strip=True)
        if not title:
            continue
        items.append({
            'rank': rank,
            'title': title,
            'url': url,
            'source': 'sohu_news',
            'section': '要闻',
        })
    print(json.dumps(items, ensure_ascii=False, indent=2))

# 澎湃新闻
def fetch_thepaper(options):
    # https://m.thepaper.cn/
    import json
    from bs4 import BeautifulSoup
    html = get_real_browser_html('https://m.thepaper.cn/')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()

    # 轮播头条
    for item in soup.select('div.adm-swiper-item'):
        a = item.select_one('a[href*="/newsDetail_forward_"]')
        if not a:
            continue
        href = a.get('href', '').split('?')[0]
        if href in seen:
            continue
        title_node = item.select_one('[class*="headline_swpier_title"] span')
        title = title_node.get_text(strip=True) if title_node else ''
        if not title:
            continue
        seen.add(href)
        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': 'https://www.thepaper.cn' + href,
            'source': '澎湃新闻',
            'section': '头条',
        })

    # 主列表
    for wrapper in soup.select('div[class*="wrapper"]'):
        a = wrapper.select_one('a[href*="/newsDetail_forward_"]')
        if not a:
            continue
        href = a.get('href', '').split('?')[0]
        if href in seen:
            continue
        h3 = wrapper.select_one('h3[class*="title"]')
        title = h3.get_text(strip=True) if h3 else ''
        if not title:
            img = wrapper.select_one('img[alt]')
            title = img.get('alt', '').strip() if img else ''
        if not title:
            continue
        seen.add(href)
        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': 'https://www.thepaper.cn' + href,
            'source': '澎湃新闻',
            'section': '要闻',
        })

    print(json.dumps(items, ensure_ascii=False, indent=2))

# Google新闻
def fetch_google_news(options):
    # https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVU5PR2dKRFRpZ0FQAQ?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans
    import json
    from bs4 import BeautifulSoup

    url = 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVU5PR2dKRFRpZ0FQAQ?hl=zh-CN&gl=CN&ceid=CN%3Azh-Hans'
    html = get_real_browser_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    base = 'https://news.google.com/topics/'

    items = []
    seen = set()

    def extract_item(container, section):
        a = None
        for x in container.select('a[href*="./read/"]'):
            if x.get_text(strip=True):
                a = x
                break
        if not a:
            return
        href = a.get('href', '')
        if href.startswith('./'):
            href = base + href[2:]
        if href in seen:
            return
        title = a.get_text(strip=True)
        if not title:
            return
        seen.add(href)
        source_node = container.select_one('.vr1PYe')
        time_node = container.select_one('time')
        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': href,
            'source_name': source_node.get_text(strip=True) if source_node else '',
            'time': time_node.get('datetime', '') if time_node else '',
            'source': 'Google新闻',
            'section': section,
        })

    # 独立卡片
    for card in soup.select('div.IL9Cne'):
        extract_item(card, '要闻')

    # 分组新闻（每组取首条）
    for grp in soup.select('div.W8yrY'):
        extract_item(grp, '要闻')

    print(json.dumps(items, ensure_ascii=False, indent=2))

# 华尔街见闻
# https://wallstreetcn.com/news/global
def fetch_wallstreetcn(options):
    import json
    from bs4 import BeautifulSoup
    html = get_real_browser_html('https://wallstreetcn.com/news/global')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()
    for card in soup.select('div.article-entry.list-item'):
        a = card.select_one('a.article-link[href*="/articles/"]')
        if not a:
            continue
        href = a.get('href', '').split('?')[0]
        if href in seen:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        seen.add(href)
        desc_node = card.select_one('div.content')
        author_node = card.select_one('div.author')
        time_node = card.select_one('time')
        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': href,
            'description': desc_node.get_text(strip=True) if desc_node else '',
            'author': author_node.get_text(strip=True) if author_node else '',
            'time': time_node.get('datetime', '') if time_node else '',
            'source': '华尔街见闻',
            'section': '全球',
        })
    print(json.dumps(items, ensure_ascii=False, indent=2))

# 第一财经
# https://www.yicai.com/news/
def fetch_yicai(options):
    import json
    import re
    from bs4 import BeautifulSoup
    html = get_real_browser_html('https://www.yicai.com/news/')
    soup = BeautifulSoup(html, 'html.parser')

    items = []
    seen = set()
    newslist = soup.select_one('#newslist')
    if not newslist:
        newslist = soup
    for a in newslist.select('a.f-db[href]'):
        href = a.get('href', '')
        if not re.search(r'/news/\d+', href):
            continue
        if not href.startswith('http'):
            href = 'https://www.yicai.com' + href
        href = href.split('?')[0]
        if href in seen:
            continue
        h2 = a.select_one('h2')
        title = h2.get_text(strip=True) if h2 else ''
        if not title:
            continue
        seen.add(href)
        desc_node = a.select_one('p')
        time_node = a.select_one('.rightspan span')
        items.append({
            'rank': len(items) + 1,
            'title': title,
            'url': href,
            'description': desc_node.get_text(strip=True) if desc_node else '',
            'time': time_node.get_text(strip=True) if time_node else '',
            'source': '第一财经',
            'section': '新闻',
        })
    print(json.dumps(items, ensure_ascii=False, indent=2))

def main():
    options = usage()
    if options.source == '':
        print('please provide source', file=sys.stderr)
        sys.exit(-1)
    support_sources = set(['xiaohongshu_hot', 'zhihu_hot', 'weibo_hot', 'tencent_news', '163_news', 'sohu_news', 'thepaper', 'google_news', 'wallstreetcn', 'yicai'])
    if options.source not in support_sources:
        print('unsupported source: %s' % options.source, file=sys.stderr)
        sys.exit(-1)
    exec('fetch_%s(options)' % options.source)

if __name__ == '__main__':
    main()