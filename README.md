# URL2Markdown WebDAV Note Handler

## 项目简介

这是一个基于 Flask 的 Python 应用程序，用于接收笔记内容并通过 WebDAV 协议将其保存到远程存储中。支持从 URL 获取笔记内容并转换为 Markdown 格式，同时可以将笔记文件上传至指定的 WebDAV 路径。

---

## 功能特性

1. **笔记处理**：
   - 支持通过 URL 自动抓取网页内容并转换为 Markdown 格式。
   - 支持手动输入笔记标题、内容和来源。
   - 自动生成时间戳和随机标识符以确保文件名唯一性。

2. **本地保存**：
   - 将笔记内容保存为 Markdown 文件，并添加元数据（如日期、来源等）。

3. **WebDAV 集成**：
   - 支持将生成的 Markdown 文件上传至 WebDAV 存储。
   - 自动创建目标目录（如果不存在）。

4. **RESTful API 接口**：
   - 提供 `/process_note` 接口，用于接收笔记数据并处理。

5. **日志记录**：
   - 记录关键操作的日志信息，便于调试和问题追踪。

---

## 安装与配置

### 环境要求

- Python 3.8 或更高版本
- 安装依赖项：`pip install -r requirements.txt`

### 配置 `.env` 文件

在项目根目录下创建 `.env` 文件，并填写以下内容：

```env
webdav_url=YOUR_WEBDAV_URL
webdav_user=YOUR_WEBDAV_USERNAME
webdav_psw=YOUR_WEBDAV_PASSWORD
save_note_path=obsidian  # 默认保存路径
```

> **注意**：`webdav_url`、`webdav_user` 和 `webdav_psw` 是必需的配置项。如果未正确配置，程序将无法启动。

---

## 使用方法

### 启动服务

运行以下命令启动 Flask 服务器：

```bash
python app.py
```

默认情况下，服务会监听 `0.0.0.0:5000`。

---

### API 接口说明

#### 请求 URL

```
POST /process_note
```

#### 请求参数

| 参数名          | 类型   | 必填 | 描述                                                                 |
|-----------------|--------|------|----------------------------------------------------------------------|
| `note_url`      | string | 否   | 笔记链接（优先级高于 `note_title` 和 `note_content`）。             |
| `note_title`    | string | 否   | 笔记标题（如果未提供，则会生成随机标题）。                          |
| `note_content`  | string | 否   | 笔记内容（字符串类型）。                                            |
| `save_note_path`| string | 否   | 笔记保存路径（默认为 `.env` 中的 `save_note_path`）。               |
| `note_source`   | string | 否   | 笔记来源（默认为 "微信"）。                                         |

#### 返回值

- 成功时返回 JSON 格式的成功信息和文件路径。
- 失败时返回错误信息。

#### 示例请求

```bash
curl -X POST http://localhost:5000/process_note \
-H "Content-Type: application/json" \
-d '{
  "note_url": "https://example.com",
  "note_title": "示例笔记",
  "note_content": "这是笔记的内容。",
  "save_note_path": "notes",
  "note_source": "测试"
}'
```

#### 示例响应

```json
{
  "status": "success",
  "message": "笔记已成功保存至：notes/示例笔记.md"
}
```

---

## 代码结构

```
.
├── app.py                  # 主程序入口
├── .env                    # 环境变量配置文件
├── README.md               # 项目文档
└── requirements.txt        # 依赖项列表
```

---

## 注意事项

1. **URL 抓取**：
   - 如果提供了 `note_url`，程序会尝试通过第三方服务（如 `r.jina.ai`）抓取网页内容并转换为 Markdown 格式。
   - 确保网络连接正常，并且目标 URL 可访问。

2. **文件名冲突**：
   - 如果未提供 `note_title`，程序会生成一个随机的文件名以避免冲突。

3. **错误处理**：
   - 如果 WebDAV 配置不完整或上传失败，程序会记录详细的错误日志。

---

## 常见问题

### 1. 如何检查 WebDAV 配置是否正确？

可以通过以下命令测试 WebDAV 连接：

```python
from webdav4.client import Client

client = Client(
    "https://your-webdav-url",
    auth=("username", "password")
)
print(client.exists("/"))  # 检查根目录是否存在
```

### 2. 如何修改默认保存路径？

在 `.env` 文件中设置 `save_note_path`，例如：

```env
save_note_path=my_notes
```

---

## 贡献指南

欢迎提交 Issue 或 Pull Request！如果您发现任何问题或有改进建议，请随时联系我们。

---

## 许可证

本项目采用 MIT 许可证。详细信息请参阅 [LICENSE](LICENSE) 文件。

---

感谢您的使用！如果有任何疑问，请随时联系开发者。