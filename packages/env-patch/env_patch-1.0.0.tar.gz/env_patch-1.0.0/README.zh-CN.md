# env-patch

[![PyPI version](https://badge.fury.io/py/env-patch.svg)](https://badge.fury.io/py/env-patch)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**环境文件生成器，支持模板 + 覆盖机制。**

源自 [UpbrosAI](https://upbros.ai) 团队在跨境电商和 AI 应用开发中的实战经验。

[English](README.md)

## 为什么需要 env-patch？

大多数 dotenv 库在 **运行时** 加载 `.env` 文件。但如果你需要：

- **构建 Docker 镜像** 并内置环境配置？
- **部署到不支持** dotenv 加载的平台？
- **调试配置** 直接查看最终会使用什么值？

**env-patch** 在 **构建时** 将模板和环境配置合并生成单一 `.env` 文件。

## 安装

```bash
# 使用 pip
pip install env-patch

# 使用 uv（推荐）
uv add env-patch

# 使用 pipx（全局安装 CLI）
pipx install env-patch
```

## 快速开始

```bash
# 1. 创建模板
cat > .env.example << 'EOF'
DATABASE_URL=postgres://localhost/myapp
REDIS_URL=redis://localhost:6379
DEBUG=false
EOF

# 2. 创建环境配置
cat > .env.development << 'EOF'
DEBUG=true
EOF

# 3. 生成 .env
env-patch -e development

# 结果：.env 包含模板的 DATABASE_URL、REDIS_URL + 覆盖的 DEBUG=true
```

## 文件层级

```
.env.example              # 模板（git 追踪）
.env.development          # 开发环境配置（git 追踪）
.env.development.local    # 本地覆盖（git 忽略）
.env                      # 输出文件（git 忽略）
```

**优先级（从高到低）：**
1. `.env.{env}.local` - 个人机器特定的覆盖
2. `.env.{env}` - 环境配置
3. `.env.example` - 模板默认值

## 使用方法

### 基本用法

```bash
# 自动检测环境文件（当只有一个时）
env-patch

# 指定环境
env-patch -e development
env-patch -e production
env-patch -e staging
```

### 别名

内置常用环境别名：

```bash
env-patch -e dev    # 等同于: env-patch -e development
env-patch -e prod   # 等同于: env-patch -e production
env-patch -e stage  # 等同于: env-patch -e staging
```

### 自定义环境

```bash
# 使用任意环境名
env-patch -e uai-prod       # 使用 .env.uai-prod
env-patch -e feature-auth   # 使用 .env.feature-auth
```

### 选项

```bash
env-patch -e <env>           # 环境名称
env-patch -t <file>          # 模板文件（默认: .env.example）
env-patch -o <file>          # 输出文件（默认: .env）
env-patch -s                 # 严格模式：未知键报错
env-patch -h                 # 显示帮助
env-patch -v                 # 显示版本
```

## 本地覆盖

创建 `.env.{env}.local` 存放不应提交的机器特定配置：

```bash
# .env.development.local（git 忽略）
DATABASE_URL=postgres://localhost:5433/myapp_local
API_KEY=my-personal-api-key
```

这些值会覆盖模板和环境配置。

## 推荐的 .gitignore

```gitignore
# 输出文件
.env

# 本地覆盖
.env.local
.env.*.local

# 保留这些追踪
!.env.example
```

## CI/CD 集成

```yaml
# GitHub Actions 示例
steps:
  - name: 生成生产环境 .env
    run: |
      pip install env-patch
      env-patch -e production
```

```dockerfile
# Dockerfile 示例
FROM python:3.12
RUN pip install env-patch
COPY .env.example .env.production ./
RUN env-patch -e production
```

## 为什么不用 dotenv-flow？

| 特性 | env-patch | dotenv-flow |
|------|-----------|-------------|
| 执行时机 | 构建时 | 运行时 |
| 输出 | 单一 `.env` 文件 | 仅内存加载 |
| Docker 构建 | 简单直接 | 需要变通方案 |
| 调试可见性 | 直接查看 `.env` | 需要添加日志 |
| 语言 | Python CLI | Node.js 库 |

**需要生成文件用 env-patch，需要运行时加载用 dotenv-flow。**

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

Made with love by [UpbrosAI Team](https://upbros.ai)
