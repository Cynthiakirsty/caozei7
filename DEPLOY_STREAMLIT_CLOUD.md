# Streamlit Community Cloud 部署

## 1. 上传到 GitHub

在 GitHub 新建一个仓库，例如 `caozei-operation-platform`。不要上传
`.streamlit/secrets.toml`、真实运营 Excel、SQLite 数据库或任何 API Token。

项目根目录必须包含：

- `app.py`
- `requirements.txt`
- `modules/`
- `pages/`
- `.streamlit/config.toml`

## 2. 创建云端应用

1. 登录 <https://share.streamlit.io>。
2. 点击 **Create app**。
3. 选择刚创建的 GitHub 仓库。
4. Branch 选择 `main`。
5. Main file path 填写 `app.py`。
6. Python 版本建议选择 3.12。
7. 点击 **Deploy**。

部署完成后会获得一个 `https://xxx.streamlit.app` 链接。

## 3. 配置可选密钥

基础分析不需要任何密钥。只有使用大模型增强时，才在应用的
**Settings → Secrets** 中按需填写：

```toml
HF_TOKEN = "你的Hugging Face Token"
GROQ_API_KEY = "你的Groq Key"
OPENAI_API_KEY = "你的OpenAI Key"
```

不要把密钥写进 GitHub 文件。

## 4. 数据安全

- 云端默认 `PERSIST_UPLOADS=false`，上传内容仅保存在当前访客会话。
- 不要在公共演示环境上传未脱敏的真实用户数据。
- 若需要持久化数据，应增加登录、用户隔离和独立数据库。
- 如需限制访问，可在 Streamlit Cloud 中将应用设置为私有并邀请指定邮箱。
