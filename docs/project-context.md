# Open Memory Project Context

Open Memory 是一个个人 AI 记忆系统，目标是让 AI 持续记录、整理和理解用户的生活、项目、学习和想法，最终形成一个越来越理解用户的数字分身。系统重点不是保存所有原始录音，而是自动提炼真正有价值的长期记忆，并逐渐学习用户的偏好、目标、项目历史和决策逻辑。

核心架构采用分层记忆，而不是把所有历史记录直接塞进大模型上下文：

```text
手机采集音频
-> VAD 过滤静音和无效内容
-> Whisper / faster-whisper / WhisperKit 转文字
-> transcript events 时间线
-> 自动分类和动态重要性判断
-> 每日总结
-> 长期记忆压缩
-> 自我反思
-> AI Agent 检索问答
```

模型分工建议：

```text
Whisper / WhisperKit：负责语音转文字
规则 / 小模型：负责初步分类、标签、项目识别、临时重要性评分
Embedding：把文本变成语义向量，用来找“意思相近”的记忆
Qdrant / Chroma：存向量，支持语义检索
大模型：负责每日总结、长期记忆压缩、复杂分析、自我反思和问答
```

重要性不应该一次决定。每条记录刚进入系统时可以有 `initial_importance`，之后根据后续对话、重复提及、项目进展、用户修正和每日总结重新判断，形成 `current_importance`、`importance_reason` 和 `last_reassessed_at`。例如一条原本普通的 ESP32 记录，如果后续多次被提到，就应该被升级为重要项目记忆。

Embedding 可以理解成“语义坐标”。普通搜索只能找相同关键词，embedding 可以找到意思相近的内容。例如用户问“我什么时候说过手机端过滤语音”，系统应该能找到“VAD 要先在 iPhone 上做，避免上传无意义音频”。

短期目标是做成一个开源 vibe coding 项目。用户负责方向、感觉、产品直觉和需求表达，Codex 负责实现、测试、提交和 GitHub 同步。commit 应该保持真实、自然、可读，不为了刷图乱提交，但可以把功能拆成小步，让项目历史更清楚。

当前项目名称是 Open Memory，仓库地址是：

```text
https://github.com/qixuan-xu/open-memory
```

本地路径示例：

```text
~/Desktop/projects/open-memory
```

当前 MVP 已经包含：

- FastAPI 后端
- SQLite 数据库
- 文本事件写入
- 自动分类和重要性评分
- 每日总结
- 长期记忆候选
- 自我反思
- 简单检索问答
- Web dashboard
- Docker / docker-compose
- GitHub Actions CI
- CLI 骨架：`open-memory setup/start/models`
- 模型目录占位：`models/.gitkeep`

模型权重不要放进 Git。Git 里只放代码、配置、下载逻辑和说明。Whisper、Qwen、embedding 模型、音频、SQLite 记忆库、API key、缓存文件都不应该提交。

未来希望支持：

```bash
brew tap qixuan-xu/open-memory
brew install open-memory
open-memory setup
open-memory models install whisper-small
open-memory models install bge-m3
open-memory start
```

Homebrew 只安装程序本体，模型选择和下载交给 CLI。模型安装可以提供 preset：

```text
light: whisper-tiny + rules
balanced: whisper-small + bge-m3
local-ai: whisper-small + bge-m3 + qwen
cloud: whisper-small + bge-m3 + cloud GPT provider
```

v2 可以加入早上和晚上总结：

早上总结：
- 今天要注意什么
- 昨天留下了什么
- 哪些项目该继续
- 哪些问题需要澄清

晚上总结：
- 今天发生了什么
- 做了哪些项目
- 产生了哪些想法
- 哪些内容应该进入长期记忆
- 明天应该跟进什么

近期路线：

1. 继续打磨 dashboard，让它更像一个真正可用的 AI memory cockpit。
2. 接入真实 Whisper / faster-whisper 转录 worker。
3. 加入 embedding 和 Qdrant / Chroma 语义检索。
4. 加入动态重要性重评估。
5. 加入 morning briefing / evening review。
6. 加入记忆删除、修正、保留、合并机制。
7. 加入隐私规则：哪些内容不记，哪些短期保留，哪些可以进长期记忆。
8. 做 iPhone capture app：录音、VAD、上传文本、暂停开关。
9. 做 Homebrew tap 和正式 release。

更短一句话版：

```text
Open Memory 是一个 local-first personal AI memory OS：用手机采集、VAD 过滤、Whisper 转录、小模型整理、embedding 检索、大模型总结和反思，把生活和项目压缩成可查询、可修正、会成长的长期记忆系统。
```
