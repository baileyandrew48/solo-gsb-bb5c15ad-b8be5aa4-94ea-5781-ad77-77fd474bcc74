# 公开档案敏感片段遮盖 API

基于 Python + FastAPI 的敏感片段遮盖服务。提交档案原文与候选片段，服务从可重叠的候选中选出**互不重叠**（允许端点相接）的最优组合，依次按以下规则裁决：

1. **最大化权重总和**；
2. 权重并列时，**最大化遮盖字符总数**；
3. 再并列时，**入选 ID 升序列表字典序更小者**胜出。

返回入选 ID、落选 ID，以及用等长 `█`（按 Unicode 码点）遮盖后的正文。

## 启动

单条命令（镜像构建时自动备齐全部依赖，无需任何外部账号）：

```bash
docker compose up --build
```

- **API 地址**：`http://localhost:8000`
- **端口**：`8000`
- 交互式接口文档（Swagger UI）：`http://localhost:8000/docs`
- 健康检查：`GET http://localhost:8000/health`

## 接口说明

### `POST /redact`

**请求体**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `text` | string | 档案原文 |
| `segments` | array | 候选片段列表，可为空 |
| `segments[].id` | string | 片段唯一 ID（非空，全局不可重复） |
| `segments[].weight` | integer | 权重，**正整数** |
| `segments[].start` | integer | 起始位置（含），按 Unicode 码点从 0 计数 |
| `segments[].end` | integer | 结束位置（不含），按 Unicode 码点计数 |

**响应体**

| 字段 | 说明 |
| --- | --- |
| `selected` | 入选片段 ID，升序 |
| `rejected` | 落选片段 ID，升序 |
| `redacted_text` | 入选片段被等长 `█` 遮盖后的正文 |

**示例**

```bash
curl -s -X POST http://localhost:8000/redact \
  -H "Content-Type: application/json" \
  -d '{
        "text": "张三的身份证号是11010119900307xxxx，电话13800001111。",
        "segments": [
          {"id": "id-card", "weight": 10, "start": 8, "end": 26},
          {"id": "phone",  "weight": 8,  "start": 29, "end": 40},
          {"id": "all",    "weight": 15, "start": 8,  "end": 40}
        ]
      }'
```

响应（`id-card` + `phone` 权重合计 18，优于整段 `all` 的 15）：

```json
{
  "selected": ["id-card", "phone"],
  "rejected": ["all"],
  "redacted_text": "张三的身份证号是██████████████████，电话███████████。"
}
```

**校验规则**（违反即返回 `422` 并说明原因）

- 片段 ID 重复；
- 空片段或区间非法（`start >= end`）；
- 区间越界（`end` 超出正文码点长度，或位置为负）；
- 权重非正整数、ID 为空等字段级错误。

## 本地开发（可选）

核心选择算法（`app/selector.py`）无第三方依赖，可直接运行单元测试：

```bash
python3 -m unittest discover tests
```

## 项目结构

```
app/
  main.py       # FastAPI 应用：请求模型、校验、/redact 与 /health 接口
  selector.py   # 带权区间调度 DP（三级裁决）与 █ 遮盖，纯标准库
tests/          # 算法单元测试（标准库 unittest）
Dockerfile      # python:3.12-slim，构建时安装 requirements.txt
docker-compose.yml
requirements.txt
```
