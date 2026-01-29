# Linux Profiler MCP 发布指南

本指南详细说明如何将 `linux-profiler-tool` 发布到不同的 MCP 社区平台。

---

## 📋 发布前准备

### 1. 确认项目就绪

- ✅ 版本号统一到 v1.1.0
- ✅ 所有文档更新完成
- ✅ 代码质量检查通过
- ✅ 功能测试完成

### 2. 替换占位符（可选）

如果您已经有 GitHub 仓库，请替换以下文件中的占位符：

**文件清单：**
- `pyproject.toml` - 第 11-14 行
- `CHANGELOG.md` - 最后几行

**替换内容：**
```bash
# 替换 yourusername 为您的 GitHub 用户名
https://github.com/yourusername/linux-profiler-tool
↓
https://github.com/YOUR_ACTUAL_USERNAME/linux-profiler-tool
```

---

## 🚀 发布方式一：MCP 官方 Registry（推荐）

### 适用场景
- 全球开发者可见
- 集成到 MCP 官方生态
- 支持多种客户端（Claude Desktop、Cline、Cursor 等）

### 发布步骤

#### 步骤 1：准备 GitHub 仓库

```bash
# 1. 提交所有更改
git add .
git commit -m "Release v1.1.0: Process profiling and quality improvements"

# 2. 创建版本标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 3. 推送到 GitHub
git push origin main --tags
```

#### 步骤 2：访问 MCP Registry

MCP 官方 Registry 仓库：
- **GitHub**: https://github.com/modelcontextprotocol/registry
- **文档**: https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx

#### 步骤 3：使用 CLI 工具发布

```bash
# 1. Clone registry 仓库
git clone https://github.com/modelcontextprotocol/registry.git
cd registry

# 2. 构建 publisher 工具
make publisher

# 3. 使用工具发布（需要 GitHub 认证）
./bin/mcp-publisher publish \
  --namespace io.github.YOUR_USERNAME \
  --name linux-profiler \
  --version 1.1.0 \
  --repository https://github.com/YOUR_USERNAME/linux-profiler-tool
```

#### 步骤 4：验证发布

发布后，您的服务器将出现在：
- **官方网站**: https://modelcontextprotocol.io
- **Registry API**: https://registry.modelcontextprotocol.io

### 认证方式选择

**方式 A：GitHub OAuth（推荐个人开发者）**
- 使用 GitHub 账号登录
- 自动验证 `io.github.YOUR_USERNAME` 命名空间

**方式 B：GitHub Actions OIDC（推荐 CI/CD）**
- 在 GitHub Actions 中自动发布
- 需要配置 OIDC 权限

**方式 C：自定义域名验证**
- 如果您有自己的域名（如 `example.com`）
- 通过 DNS TXT 记录或 HTTP 挑战验证所有权
- 可以使用 `com.example.linux-profiler` 命名空间

---

## 🇨🇳 发布方式二：魔搭社区（ModelScope）MCP 广场

### 适用场景
- 专注中文开发者
- 国内访问速度快
- 与阿里云生态集成

### 当前状态

魔搭 MCP 广场于 2025年4月15日正式上线，目前有 **近1500款** MCP 服务器。

### 发布途径

#### 途径 1：通过魔搭社区网站（首选）

1. **访问 MCP 广场**
   - 网址：https://modelscope.cn/mcp
   - 登录魔搭社区账号

2. **寻找提交入口**
   在页面中查找以下按钮：
   - "发布" / "Upload" / "上传服务器"
   - "贡献 MCP" / "接入您的服务器"

3. **填写服务器信息**
   - 服务器名称：`Linux Profiler`
   - 命名空间：`io.github.YOUR_USERNAME.linux-profiler`
   - 描述：Linux Performance Profiler with MCP Protocol Support
   - 仓库地址：https://github.com/YOUR_USERNAME/linux-profiler-tool
   - 分类：开发者工具 / 系统监控
   - 标签：`linux`, `performance`, `profiling`, `monitoring`

4. **提供配置示例**
   上传 `mcp_config.json` 作为配置示例

#### 途径 2：通过魔搭社区钉钉群

1. **加入开发者联盟群**
   - 搜索钉钉群："魔搭ModelScope开发者联盟群"
   - 或访问：https://developer.aliyun.com/ask/ 查找入口

2. **联系产品负责人**
   - MCP 产品负责人：黎枫
   - 说明您想提交 MCP 服务器

3. **提供项目信息**
   ```
   项目名称：Linux Profiler MCP
   GitHub：https://github.com/YOUR_USERNAME/linux-profiler-tool
   功能简介：Linux 系统性能监控与进程剖析工具，支持火焰图生成
   ```

#### 途径 3：联系阿里云开发者社区

- 访问：https://developer.aliyun.com/modelscope
- 通过"工单"或"论坛"提交 MCP 服务器接入申请

### 魔搭发布优势

- ✅ 中文文档友好
- ✅ 国内高速访问
- ✅ 与阿里云 PAI、通义千问等产品集成
- ✅ 提供 MCP 实验场调试工具

---

## 📦 发布方式三：PyPI（Python 包仓库）

### 适用场景
- Python 开发者直接通过 `pip install` 安装
- 不限于 MCP 使用场景

### 发布步骤

#### 步骤 1：安装构建工具

```bash
pip install build twine
```

#### 步骤 2：构建分发包

```bash
# 在项目根目录执行
python -m build

# 将生成以下文件：
# dist/linux-profiler-mcp-1.1.0.tar.gz
# dist/linux_profiler_mcp-1.1.0-py3-none-any.whl
```

#### 步骤 3：检查包质量

```bash
twine check dist/*
```

#### 步骤 4：上传到 PyPI

```bash
# 首次上传需要注册 PyPI 账号：https://pypi.org/account/register/

# 上传到测试环境（可选）
twine upload --repository testpypi dist/*

# 正式上传
twine upload dist/*
```

#### 步骤 5：验证安装

```bash
# 其他用户可以通过以下命令安装
pip install linux-profiler-mcp

# 或指定版本
pip install linux-profiler-mcp==1.1.0
```

### PyPI 包信息

发布成功后，您的包将出现在：
- **PyPI 页面**: https://pypi.org/project/linux-profiler-mcp/
- **安装统计**: 可通过 pypistats.org 查看

---

## 🌐 发布方式四：其他 MCP 社区

### 1. AIbase MCP 服务合集

- **网址**: https://www.aibase.com/zh/mcp （示例）
- **特点**: 国内 MCP 服务器聚合平台
- **提交方式**: 通常通过网站提交表单或联系管理员

### 2. GitHub Awesome MCP Servers

许多开发者维护着 MCP 服务器列表，您可以提交 PR：

```bash
# 1. 搜索 GitHub 上的 MCP Servers 列表
https://github.com/search?q=awesome+mcp+servers

# 2. Fork 相关仓库

# 3. 在 README 中添加您的服务器
## Linux Performance Monitoring
- **[Linux Profiler](https://github.com/YOUR_USERNAME/linux-profiler-tool)** - 
  System performance monitoring and process profiling with flame graphs

# 4. 提交 Pull Request
```

### 3. Reddit / Hacker News 分享

- **Reddit**: r/ClaudeAI, r/programming
- **Hacker News**: https://news.ycombinator.com/
- **标题示例**: "Show HN: Linux Profiler MCP - Performance monitoring tool for AI agents"

---

## 📊 发布后推广建议

### 1. 更新项目文档

在 `README.md` 中添加安装徽章：

```markdown
[![PyPI version](https://badge.fury.io/py/linux-profiler-mcp.svg)](https://pypi.org/project/linux-profiler-mcp/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://modelcontextprotocol.io)
```

### 2. 创建演示视频

- 录制 2-3 分钟的功能演示
- 上传到 YouTube / Bilibili
- 在 README 中嵌入视频

### 3. 撰写博客文章

**中文博客平台：**
- 掘金：https://juejin.cn
- 知乎：https://zhuanlan.zhihu.com
- CSDN：https://blog.csdn.net

**英文博客平台：**
- Medium：https://medium.com
- Dev.to：https://dev.to

**文章标题示例：**
- "如何使用 MCP 为 AI Agent 添加 Linux 系统监控能力"
- "Building a Linux Profiler for Claude Desktop with MCP"

### 4. 社交媒体宣传

- **Twitter/X**: 使用话题 #MCP #ClaudeAI #LinuxMonitoring
- **LinkedIn**: 分享到开发者群组
- **开发者社区**: 阿里云开发者社区、腾讯云+社区

---

## 🔄 版本更新流程

当您发布新版本时（如 v1.2.0）：

### 1. 更新版本号

```bash
# 更新 src/linux_profiler/__init__.py
__version__ = "1.2.0"

# 更新 pyproject.toml
version = "1.2.0"

# 更新 CHANGELOG.md
## [1.2.0] - 2026-XX-XX
### Added
- New feature X
...
```

### 2. 发布到各平台

```bash
# Git Tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin main --tags

# PyPI
python -m build
twine upload dist/*

# MCP Registry (重新发布新版本)
./bin/mcp-publisher publish --namespace io.github.YOUR_USERNAME \
  --name linux-profiler --version 1.2.0
```

---

## 📞 获取帮助

### MCP 官方社区

- **Discord**: https://discord.gg/modelcontextprotocol (示例)
- **GitHub Discussions**: https://github.com/modelcontextprotocol/registry/discussions

### 魔搭社区

- **钉钉群**: 魔搭ModelScope开发者联盟群
- **论坛**: https://developer.aliyun.com/ask/

### 项目维护者

如果您在发布过程中遇到问题，可以：
1. 在 GitHub Issues 提问
2. 查看本项目的 [README.md](README.md) 和 [FEATURES.md](FEATURES.md)

---

## ✅ 发布检查清单

使用此清单确保发布流程完整：

### 发布前
- [ ] 测试所有 MCP 工具功能
- [ ] 更新文档版本号
- [ ] 运行 linter 检查代码质量
- [ ] 本地测试安装 `pip install -e .`

### 发布中
- [ ] 提交代码到 GitHub
- [ ] 创建 Git 标签
- [ ] 发布到 MCP Registry
- [ ] 发布到魔搭社区（可选）
- [ ] 上传到 PyPI（可选）

### 发布后
- [ ] 验证各平台安装可用
- [ ] 更新 README 添加安装徽章
- [ ] 撰写发布公告
- [ ] 在社区分享链接

---

## 🎉 总结

**推荐发布顺序：**

1. **GitHub Release** - 创建仓库和标签（必需）
2. **MCP 官方 Registry** - 全球开发者可见（强烈推荐）
3. **魔搭社区** - 覆盖中文开发者（推荐）
4. **PyPI** - 方便 Python 开发者安装（可选）

**预计时间：**
- GitHub Release: 5 分钟
- MCP Registry: 15-30 分钟（首次需要验证）
- 魔搭社区: 1-3 天（需要审核）
- PyPI: 10 分钟

**下一步行动：**
1. 如果还没有 GitHub 仓库，先创建一个
2. 按照"发布方式一"将项目发布到 MCP 官方 Registry
3. 同时提交到魔搭社区，覆盖国内用户

---

**祝发布顺利！🚀**

如有任何问题，欢迎在 GitHub Issues 提问或查看 [PRE_RELEASE_CHECKLIST.md](PRE_RELEASE_CHECKLIST.md) 获取更多信息。
