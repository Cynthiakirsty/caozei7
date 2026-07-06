# 曹贼运营分析平台

可本地运行的 Streamlit 运营分析平台。上传 Excel 后，可分析充值、提现、投注、RTP、杀率、留存、活动成本、彩金流水、用户分层和流失风险，并通过规则引擎生成运营建议。

## 安装与启动

建议使用 Python 3.10 或更高版本：

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器通常会自动打开 `http://localhost:8501`。首次启动会创建两份演示文件供参考，但不会自动加载或展示数据：

- `data/sample_full_data.xlsx`：全盘日报
- `data/sample_user_data.xlsx`：用户 UID 明细

也可在“双表数据上传”页面分别下载两份中文模板。

## 全盘数据表字段

日期、新增用户数、日活跃玩家数、老玩家日活、充值人数、充值金额、提现金额、充减提、盈余率、有效投注、首充人数、首充金额、首充盈余率、首充提现占比、首充付费率、首充复充率、新增ARPU、新增ARPPU、老用户充值人数、老用户充值金额、老用户付费率、老用户ARPU、老用户ARPPU、老用户提现金额、老用户提现占比、老用户充减提、老用户盈余率、付费率、ARPPU、ARPU、次日留存、3日留存、7日留存、15日留存、30日留存、rtp、杀率、彩金金额、彩金占比。

## 用户明细表字段

用户UID、VIP等级、渠道、注册时间、最后登录时间、首充时间、累计流水、累计充值、累计提现、Cash余额、JCoin余额。

用户 UID 是用户分层与流失预警的唯一主键。两张表不需要按 UID 逐行关联：全盘表负责日期趋势，用户表负责用户画像。

## 指标口径

- 盈余 = 充值 - 提现
- 盈余率 = 盈余 / 充值
- RTP = 返奖 / 投注
- 杀率 =（投注 - 返奖）/ 充值
- 充投比 = 投注 / 充值
- 活动成本占比 = 活动成本 / 充值
- ARPPU = 总充值 / 付费用户数
- 新 ARPU = 新增用户充值 / 新增用户数
- 新 ARPPU = 新增用户充值 / 新增付费用户数
- 老 ARPPU = 老用户充值 / 老付费用户数
- 首充复充率 = 二次及以上充值用户数 / 首充用户数
- 首充盈余率 = 首次充值记录盈余 / 首次充值金额
- 活动 ROI =（活动用户盈余 - 活动成本）/ 活动成本

用户分层采用可解释规则并按优先级赋予唯一主标签；流失风险综合最后登录时间、累计充值、账户余额和首充状态。

## 本地数据

上传的数据仅在本地处理，并分别保存到 SQLite 的 `full_operation_data` 与 `user_detail_data` 表。请勿将业务数据提交到公开代码仓库。

云端部署默认不持久化访客上传的数据。若本地确实需要写入 SQLite，可在启动前设置：

```powershell
$env:PERSIST_UPLOADS="true"
python -m streamlit run app.py
```

## Streamlit Community Cloud 部署

部署步骤见 [DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md)。基础分析无需任何 API Key。

## AI 建议

支持 Hugging Face Router + Novita。创建具有 `Inference Providers` 权限的 Hugging Face Token 后，在页面左侧输入，或在启动前设置：

```powershell
$env:HF_TOKEN="你的Hugging Face Token"
python -m streamlit run app.py
```

默认 HF 模型为 `deepseek-ai/DeepSeek-V4-Flash:novita`。系统只发送匿名聚合指标，不发送 UID 或逐用户记录。实际免费额度、计费和模型可用性由 Hugging Face 与 Novita 决定。

若不想每次输入 Token，可复制 `.streamlit/secrets.toml.example` 为
`.streamlit/secrets.toml`，然后填写 Token：

```toml
HF_TOKEN = "hf_你的Token"
GROQ_API_KEY = ""
OPENAI_API_KEY = ""
```

`secrets.toml` 已加入 `.gitignore`，不会被提交到 Git。不要把该文件或 Token 发给他人。

也支持 Groq 免费 API。先在 `https://console.groq.com/keys` 创建 API Key，然后在页面左侧输入；也可以在启动前设置：

```powershell
$env:GROQ_API_KEY="你的Groq API Key"
python -m streamlit run app.py
```

Groq 默认模型为 `qwen/qwen3-32b`。系统只发送匿名聚合指标，不发送 UID 或逐用户记录。免费额度和模型可用性以 Groq 当前政策为准。

也可以使用免费的本地 Ollama，经营数据不离开电脑：

```powershell
ollama pull qwen3:8b
python -m streamlit run app.py
```

请先从 `https://ollama.com/download/windows` 安装 Ollama。平台会自动检测本地服务和已下载模型。

“运营建议”页面可选使用 OpenAI Responses API。可在页面中临时输入 API Key，或在启动前设置：

```powershell
$env:OPENAI_API_KEY="你的API Key"
python -m streamlit run app.py
```

系统只向模型发送匿名聚合指标、分层人数和风险人数，不发送用户 UID 或逐用户记录。API Key 不会写入项目文件、Excel 或 SQLite。默认模型为 `gpt-5.4-mini`，也可切换至 `gpt-5.5`。
