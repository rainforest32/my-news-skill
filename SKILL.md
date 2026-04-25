---
name: my-news-skill
description: "新闻抓取与摘要技能。Use when user asks for 最新新闻、新闻摘要、今日热点、财经新闻、科技新闻、国内新闻、国际新闻、微博热点、小红书热点、知乎热点、AI 新闻、HuggingFace 论文、Hacker News、GitHub Trending，或某个关键词的最新报道；通过本地 fetch_news.py 脚本抓取真实数据，并输出带标题、来源、发布时间、链接和核心摘要的简体中文结果。"
version: 2.0.0
author: 王小桥
license: MIT
metadata:
  hermes:
    tags: ["新闻查询", "最新新闻", "新闻摘要", "综合新闻", "热点新闻", "财经新闻", "科技新闻", "国内新闻", "国际新闻", "微博热点", "小红书热点", "知乎热点", "AI新闻", "HuggingFace", "HackerNews", "GitHub Trending"]
---

# 新闻查询技能

## 定位
本 skill 完全依赖本地脚本 `scripts/fetch_news.py` 抓取真实实时数据，不使用 Agent 内置联网检索。每次执行时必须先运行脚本获取 JSON，再对结果做摘要整理后输出。

脚本路径：`scripts/fetch_news.py`（相对于本 skill 根目录）
运行方式：`python3 scripts/fetch_news.py --source <source_name>`
工作目录：本 skill 根目录（SKILL.md 所在目录）
输出格式：JSON 数组，每条包含 `title`、`url` 及各信源特有字段。

## 信源总览

### 热点与社交平台
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `xiaohongshu_hot` | 小红书热榜（rebang.today） | title, url, hot |
| `zhihu_hot` | 知乎热榜 | title, url, hot, excerpt |
| `weibo_hot` | 微博热搜 | title, url, hot, category |

### 综合与实时新闻
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `tencent_news` | 腾讯新闻 | title, url, time, source |
| `163_news` | 网易新闻 | title, url, time, source |
| `sohu_news` | 搜狐新闻 | title, url, time, source |
| `thepaper` | 澎湃新闻 | title, url, time, source |
| `google_news` | Google News | title, url, source, time |

### 财经新闻
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `wallstreetcn` | 华尔街见闻 | title, url, time |
| `yicai` | 第一财经 | title, url, time |
| `cls` | 财联社 | title, url, time |
| `stcn` | 证券时报 | title, url, time |

### 科技新闻
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `36kr` | 36氪 | title, url, time, author |
| `tencent_tech` | 腾讯科技 | title, url, time |
| `tmtpost` | 钛媒体 | title, url, time, author, description |
| `geekpark` | 极客公园 | title, url, time, category, author |

### 国际新闻
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `reuters` | 路透社（via Google News RSS） | title, url, source, time |
| `bbc` | BBC World | title, url, description, time |
| `cnn` | CNN World | title, url |
| `apnews` | AP News | title, url, description, time |
| `nytimes` | 纽约时报 World RSS | title, url, description, category, time |

### AI 与开发者资讯
| source_name | 说明 | 关键输出字段 |
|---|---|---|
| `hf_papers` | Hugging Face Papers 今日列表 | title, url, upvotes, submitter |
| `hackernews` | Hacker News 首页 | rank, title, url, points, user, age, comments |
| `github_trending` | GitHub Trending（本周） | name, url, description, language, stars, stars_period |

## 新闻类型 → 推荐信源映射

| 用户请求类型 | 首选信源 | 备用信源 |
|---|---|---|
| 微博热点 | `weibo_hot` | - |
| 小红书热点 | `xiaohongshu_hot` | — |
| 知乎热点 | `zhihu_hot` | — |
| 综合国内新闻 | `tencent_news`, `thepaper`, `google_news` | `163_news`, `sohu_news` |
| 财经新闻 | `wallstreetcn`, `cls`, `yicai` | `stcn` |
| 科技新闻 | `36kr`, `geekpark`, `tmtpost`, `tencent_tech` | - |
| 国际新闻 | `reuters`, `bbc`, `nytimes` | `cnn`, `apnews` |
| AI 论文 | `hf_papers` | `hackernews` |
| AI / 开发者动态 | `hackernews`, `hf_papers`, `github_trending`, `36kr` | - |
| GitHub 热门项目 | `github_trending` | `hackernews` |

## 工作流

### 第一步：识别查询意图
判断用户属于哪一类请求，并从上表选出信源列表。若用户明确指定信源名，直接使用。

### 第二步：运行脚本抓取
对每个信源执行命令（工作目录为本 skill 根目录）：

```bash
python3 scripts/fetch_news.py --source <source_name>
```

- 首选信源的多个候选顺序执行，其中某一个失败时可继续执行，如果所有首选信源失败才切换到备用信源顺序执行。
- 若脚本返回非零退出码或 JSON 为空数组，认为该信源抓取失败，记录失败原因并切换到下一个候选信源。
- 若某信源需要 Playwright（`get_real_browser_html`），那尝试安装相关环境后重试一次。

### 第三步：解析 JSON 并整理
脚本输出为标准 JSON 数组，逐条读取后：
- 去重：标题相似度高（> 80%）的多条合并为一条，合并来源字段。
- 排序：有时间字段时按时间倒序；热榜类按rank升序，如果有热度值也可按照热度值降序。
- 截取：用户未指定数量时默认取前 10 条；用户指定则按指定数量。

### 第四步：输出中文摘要

#### 普通新闻模板
```
#### N. [标题](url)
- 来源：媒体名 / source_name
- 时间：来自 time 字段，或标注"时间未明确"
- 摘要：1–2 句核心内容（从 description/excerpt 字段提取，不足时根据标题推断，禁止编造）
```

#### 热榜类模板
```
#### N. 标题 — 热度 hot值
- 来源：weibo_hot / zhihu_hot / xiaohongshu_hot
- 链接：url
- 摘要：该词条讨论的事件与争议焦点（从 excerpt 字段提取，无则根据标题描述）
```

#### Hacker News 模板
```
#### N. [标题](url)  ↑rank
- 分数：points 分 | 作者：user | 发布：age
- 评论：comments
```

#### HuggingFace Papers 模板
```
#### N. [标题](url)
- 上票：upvotes | 提交者：submitter
- 摘要：根据标题推断研究方向（不编造摘要内容）
```

#### GitHub Trending 模板
```
#### N. [name](url)  language
- 描述：description
- ⭐ stars（stars_period）
```

## 严格规则
1. 所有输出默认使用简体中文，专有名词保留英文原文。
2. 不得编造新闻、链接、热度值、人物观点或事件因果关系。
3. 时间字段优先完整格式 `YYYY-MM-DD HH:MM`；若来源只有"1 小时前"等相对时间，保留原样，不换算。
4. 无法确认时间时，明确标注"时间未明确"，不猜测。
5. 脚本执行失败时告知用户哪个信源失败及原因，并切换备用，不静默跳过。
6. 禁止在未运行脚本的情况下凭记忆或 Agent 自身知识伪造"抓取结果"。

## 兜底策略
1. 脚本超时或 JSON 为空 → 切换同类备用信源，重试一次。
2. Playwright timeout（networkidle 30 s 超时）→ 切换可用的 urllib 信源或告知用户该信源暂不可用。
3. 多信源同一事件冲突 → 采用权威来源，摘要中注明存在版本差异。
4. 用户只说"看看今天有什么新闻" → 默认运行 `tencent_news` + `reuters` + `36kr`，覆盖国内、国际、科技三类。
5. 结果不足 3 条 → 明确说明覆盖不足，展示已有结果，不凑数虚构。

## 示例触发请求
- 帮我看一下今天的 AI 新闻。
- 总结一下最新财经新闻，重点看政策和市场异动。
- 给我一份微博热点摘要。
- 看看今天 HuggingFace 有哪些热门论文。
- 看看 GitHub 本周最热项目。
- 看看今天 Hacker News 最热的 10 条。
- 看看今天国内和国际新闻各有什么大事。
