# Zretc 作业助手

一个使用 Python + PySide6 构建的桌面应用程序，用于与 Zretc 平台（swu.zretc.net）交互，帮助用户获取和提交作业。

请不要用本程序在DDL结束后提交作业。

## 功能特性

- 获取作业列表并查看详情
- 支持主观题答案填写与提交
- 自动保存配置参数
- 支持复制题目内容

## 环境要求

- Python 3.10+
- PySide6
- requests

## 安装步骤

```bash
pip install PySide6 requests
```

## 使用说明

### 1. 获取必要参数

在使用本程序前，需要从浏览器中获取以下参数：

| 参数 | 获取方式 |
|------|----------|
| **Cookie** | 登录 swu.zretc.net 后，在浏览器开发者工具（F12）的 Network 标签页中查看任意请求的 Request Headers |
| **User-Agent** | 同上，在 Request Headers 中找到 User-Agent 字段 |
| **Zretc-Token** | 同上，在 Request Headers 中找到 Zretc-Token 字段 |
| **instance_id** | 在作业页面的 URL 中获取。作业界面URL为 https://swu.zretc.net/course/student/courses/[instance_id]/homework |

### 2. 操作流程

1. 填写 Cookie、User-Agent、Zretc-Token 和 instance_id
2. 设置开始时间（用于提交时记录）
3. 点击「获取作业」按钮加载作业列表
4. 从下拉菜单选择要完成的作业
5. 在每个题目下方的文本框中填写答案
6. 点击「提交作业」完成提交

### 3. 配置保存

程序会自动保存您填写的配置参数，下次启动时自动加载。

## 项目结构

```
clhwsh/
├── main.py      # GUI 主程序，使用 PySide6 构建界面
├── zretc.py     # API 客户端，封装与 swu.zretc.net 的 HTTP 交互
└── README.md    # 本文档
```

## API 参考

### zretc.py 模块

#### 数据类

##### `ZretcQuestion`

表示一道题目。

| 属性 | 类型 | 说明 |
|------|------|------|
| `question_id` | str | 题目 ID |
| `content` | str | 题目内容（HTML 格式） |
| `score` | int | 题目分值 |

##### `ZretcHomeworkDetail`

表示作业详情。

| 属性 | 类型 | 说明 |
|------|------|------|
| `homework_id` | str | 作业 ID |
| `group_id` | str | 作业组 ID |
| `questions` | list[ZretcQuestion] | 题目列表 |

##### `ZretcHomeworkOverview`

表示作业概览信息。

| 属性 | 类型 | 说明 |
|------|------|------|
| `homework_id` | str | 作业 ID |
| `title` | str | 作业标题 |
| `status` | str | 作业状态（未提交/已提交/错过） |

##### `ZretcHomeworkAnswer`

表示题目答案。

| 属性 | 类型 | 说明 |
|------|------|------|
| `question_id` | str | 题目 ID |
| `subjective_answer` | str | 主观题答案 |

#### `ZretcClient` 类

API 客户端，封装与 swu.zretc.net 的 HTTP 交互。

##### 构造函数

```python
ZretcClient(token: str, cookie: str, user_agent: str)
```

##### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_homeworks_list(instance_id)` | instance_id: str | list[ZretcHomeworkOverview] | 获取指定实例的作业列表 |
| `get_homework_detail(homework_id)` | homework_id: str | ZretcHomeworkDetail \| None | 获取作业详情 |
| `submit_homework(homework_id, group_id, start_time, answers)` | homework_id: str, group_id: str, start_time: int (毫秒), answers: list[ZretcHomeworkAnswer] | bool | 提交作业 |

## 运行程序

```bash
python main.py
```

## 注意事项

- 请确保在提交作业前已填写所有题目的答案
- Cookie 和 Token 可能会过期，如遇请求失败请重新获取
- 本程序仅供学习交流使用
