## Plan: Complete My News Skill

补全 `/Users/rainforest/work/self/skills/my-news-skill/SKILL.md` 为一个轻量、可直接被 Agent 触发和执行的新闻查询 skill。推荐方案是明确它依赖 Agent 自带的 web_search/网页读取能力，而不是本地 Python 抓取脚本；这样能和当前文件里的前置条件保持一致，也能避免把另一个工程型 skill 的脚本假设硬搬过来。补全重点是：补齐 frontmatter 触发面、标准化执行流程、定义新闻类型到信源的映射与失败回退、统一输出模板、加入严格规则与边界。

**Steps**
1. 审核并重写 frontmatter：收紧 `description`，把触发短语从“新闻类型罗列”改成“使用场景 + 关键词”的发现面，保留中文触发词，避免过长导致噪声匹配。
2. 补齐 skill 顶部说明：明确该 skill 的目标、适用范围、依赖能力（联网、web_search、网页读取/摘要能力），并写清“不依赖本地脚本”的定位。
3. 设计统一执行流程：定义 3 步工作流，顺序为“识别用户意图/新闻类型 → 选取默认信源并检索 → 交叉验证后按统一模板输出”；该步骤阻塞后续所有内容。
4. 完成新闻类型映射表：为实时新闻、综合新闻、热点新闻、财经新闻、科技新闻、国内新闻、国际新闻、娱乐新闻、微博热点、小红书热点、知乎热点、AI 新闻等条目补全“默认来源 + 回退来源 + 检索提示词/排序偏好”；*depends on 3*。
5. 定义统一输出模板：规定每条新闻至少包含标题、来源、发布时间、核心摘要、链接；对“热点榜单类”和“普通新闻类”分别说明差异字段；*parallel with 4 after 3*。
6. 增加严格规则：要求简体中文输出、发布时间必须写明并尽量标准化、不得编造未检索到的信息、优先使用近 24 小时内容、结果不足时显式说明覆盖不足、同一事件去重合并；*depends on 4 and 5*。
7. 增加失败与兜底策略：定义默认源失效、页面不可读、信息冲突、用户未给关键词、用户要求“最新但无可靠时间戳”等场景下的处理方式；*depends on 4 and 6*。
8. 补一个简洁的“触发示例/示例请求”段落，验证 frontmatter 描述与正文规则一致，避免 skill 能被发现但正文不指导执行。
9. 最后做一次一致性校验：检查 frontmatter、正文术语、新闻类型枚举、输出模板字段是否一致，并确认没有引入脚本型承诺或仓库中不存在的依赖。

**Relevant files**
- `/Users/rainforest/work/self/skills/my-news-skill/SKILL.md` — 主要补全对象；需要重写 frontmatter、执行流程、新闻类型映射、输出模板、规则与兜底策略。
- `/Users/rainforest/work/self/skills/news-aggregator-skill/SKILL.md` — 参考其“统一工作流 + 统一模板 + 严格规则”的结构，但不复用其本地脚本假设。
- `/Users/rainforest/work/self/skills/news-aggregator-skill/MISTAKES.md` — 可借鉴时间字段、失败兜底、避免幻觉等经验，转写为 web_search 版规则。

**Verification**
1. 检查 frontmatter 是否是合法 YAML，`name` 与目录名一致，`description` 中包含用户会真实说出的触发短语。
2. 人工走查 4 类查询：`AI 新闻`、`微博热点`、`财经新闻`、`某关键词最新新闻`，确认 SKILL.md 都能给出清晰执行路径与输出要求。
3. 检查每个新闻类型是否都有默认来源和失败回退，不留半截表格。
4. 检查正文中是否出现仓库中并不存在的脚本命令、模板文件或安装依赖；轻量版方案下这些都应避免承诺。

**Decisions**
- 本次范围只包含 `/Users/rainforest/work/self/skills/my-news-skill/SKILL.md` 内容补全，以及 frontmatter/触发词设计。
- 明确不在这轮中规划或承诺 Python 抓取脚本、`instructions/`、`templates.md`、报告落盘目录等工程化配套。
- 结构上参考现有 news skill 的成熟写法，但实现假设改为 Agent 原生联网检索。

**Further Considerations**
1. `小红书热点` 与 `知乎热点` 的可稳定访问性通常弱于新闻站点；建议在 skill 中把它们写成“优先尝试平台热点页，失败时回退到权威聚合报道/搜索结果页”。
2. `综合新闻` 与 `实时新闻` 容易语义重叠；建议在正文里区分为“综合新闻 = 多领域混合摘要”，“实时新闻 = 时效优先、按最新排序”。