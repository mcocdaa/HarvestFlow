---
title: docs文件夹规范
description: docs文件夹结构与格式规范
keywords: [docs, index.md, 文档规范]
version: "1.0"
---
# Agent 友好型文档结构与格式规范
docs/rules 文件夹用于记录规则。这个文件用于记录这些文档的规范。

## 目录结构
- 深度≤3级
- 每个目录必须有 `index.md`
- 文件名：`核心关键短语.md`, 文件名必须为英语, 文件内容必须是中文的。

## 单文件要求
- 纯 Markdown 格式，单文件<500行
- 头部固定6行：
  ```yaml
  ---
  title: 标题
  version: 1.0
  keywords: [词1, 词2]
  description: 20字内摘要
  ---
  ```

## 文件索引
`index.md` 格式：
```md
# 目录名
## 文件列表
- [文件名1](文件名1.md)：摘要
- [文件名2](文件名2.md)：摘要

## 子目录
- [子目录名1](子目录名1/index.md)
- [子目录名2](子目录名2/index.md)
```

## 示例
```
知识库/
├── index.md
├── A/
│   ├── index.md
│   └── A.md
└── B/
    ├── index.md
    └── B.md
```
