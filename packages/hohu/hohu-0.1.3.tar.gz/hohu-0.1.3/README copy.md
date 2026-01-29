# 📦 HoHu CLI

**HoHu CLI** 是一款为 `hohu-admin` 生态量身打造的现代化命令行工具。它集成了项目脚手架生成、自动化环境初始化和多语言切换功能，旨在提升全栈开发者的生产力。

---

## ✨ 特性

* 🚀 **极速启动**：基于 `uv` 开发，响应速度极快。
* 🛠️ **智能初始化**：后端自动执行 `uv sync`，前端及 APP 自动执行 `pnpm install`。
* 📂 **上下文感知**：通过项目级 `.hohu` 配置，在项目内任何路径执行 `init` 均可识别。
* 🌍 **多语言支持**：完美支持中英文切换，自动跟随系统语言。
* 🎨 **精美交互**：基于 `Rich` 和 `Questionary` 打造，提供极致的视觉与交互体验。

---

## 🏗️ 项目架构流

## 📥 安装

使用 `uv` (推荐) 或 `pip` 进行全局安装：

```bash
# 使用 uv
uv tool install hohu

# 或使用 pip
pip install hohu

```

---

## 🚀 快速开始

### 1. 创建新项目

你可以直接运行 `create`。如果不提供名称，将默认创建名为 `hohu-admin` 的文件夹。

```bash
hohu admin create my-project

```

系统会提示你选择需要安装的组件（后端、前端、APP）。

### 2. 初始化环境

进入项目目录后，直接运行 `init`。工具会自动识别项目配置并安装所有依赖。

```bash
cd my-project
hohu admin init

```

### 3. 切换语言

随时随地切换你偏好的交互语言：

```bash
hohu lang

```

---

## 🚀 开发调试 (`hohu admin dev`)

`hohu admin dev` 是全栈开发的灵魂命令。它能够一键启动后端、前端及 APP 环境，并将所有实时日志流合并输出，通过彩色标签进行分流显示。

### 1. 基础启动

在项目根目录下执行，默认启动所有已安装的组件：

```bash
hohu admin dev

```

### 2. 多端目标选择 (`--app-target`)

针对 APP 组件，你可以通过 `-t` 参数指定运行环境：

* **H5 预览** (默认): `hohu admin dev -t h5`
* **微信小程序**: `hohu admin dev -t mp`
* **原生 App**: `hohu admin dev -t app`

### 3. 组件过滤 (Only / Skip)

当你只想专注于某个端的开发时，可以使用过滤功能。

* **仅运行后端**:
```bash
hohu admin dev --only backend
```
或者
```bash
hohu admin dev -o be
```


* **运行前后端，跳过 APP**:
```bash
hohu admin dev --skip App
```
```bash
hohu admin dev -s app
```
启动前端和后端
```bash
hohu dev -o be -o fe
```

* **同时指定多个组件**:
```bash
hohu admin dev -o Backend -o Frontend

```



---

### 🛠️ 命令参数详解

| 参数 | 短指令 | 说明 | 默认值 |
| --- | --- | --- | --- |
| `--app-target` | `-t` | APP 端运行环境: `h5`, `mp`, `app` | `h5` |
| `--only` | `-o` | **仅启动**指定的组件。可多次使用以指定多个。 | 无 (全启动) |
| `--skip` | `-s` | **跳过**指定的组件。可多次使用。 | 无 |
| `--help` |  | 查看此命令的详细帮助 |  |

---

### 🎨 日志交互说明

* **彩色前缀**：
* `[Backend]` - [green]绿色[/green] (FastAPI 进程)
* `[Frontend]` - [cyan]青色[/cyan] (Vite/pnpm 进程)
* `[App]` - [yellow]黄色[/yellow] (Uni-app 进程)


* **智能退出**：按下 `Ctrl + C`，`hohu` 将自动发送 `SIGTERM` 信号关闭所有关联的开发服务器，避免端口占用和僵尸进程。

---

### 💡 最佳实践建议

1. **前后端联调**：
建议使用默认的 `hohu admin dev`。当后端抛出 `500` 错误或前端发起 `404` 请求时，你会看到两条日志在屏幕上几乎同时跳出，极大缩短了排查路径。
2. **纯接口开发**：
如果你在编写 API，不需要开启庞大的前端环境，请使用 `hohu admin dev -o Backend`。它依然会通过 `fastapi dev` 提供热重载功能。
3. **小程序开发**：
使用 `hohu admin dev -t mp`。它会自动运行 `pnpm dev:mp`，你只需在微信开发者工具中导入编译生成的 `dist/dev/mp-weixin` 目录即可。

## 🛠️ 命令详解

| 命令 | 描述 |
| --- | --- |
| `hohu admin create [NAME]` | 创建项目目录并克隆选定的仓库模板 |
| `hohu admin init` | 自动化安装子项目的依赖 (uv/pnpm) |
| `hohu admin dev` | 运行项目 |
| `hohu lang`,`hohu system lang`| 切换 CLI 显示语言 (zh/en/auto) |
| `hohu info`,`hohu system info`| 查看 CLI 当前详细配置信息 |
| `hohu --version`,`-v` | 显示当前版本号 |
| `hohu --help` | 查看帮助信息 |

---

## 📂 推荐目录结构

执行 `hohu admin create` 后的项目结构：

```text
my-project/
├── .hohu/            # HoHu 项目追踪配置
├── hohu-admin/       # 后端项目 (FastAPI/uv)
├── hohu-admin-web/   # 前端项目 (Vue3/pnpm)
└── hohu-admin-app/   # APP 项目 (Uni-app/pnpm)

```

---

## 🤝 贡献指南

我们非常欢迎 Issue 和 Pull Request！

1. Fork 本仓库。
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 开启一个 Pull Request。

---

## 📄 开源协议

本项目采用 [MIT](https://www.google.com/search?q=LICENSE) 协议。

---

### 💡 开发者备注

如果你在发布到 PyPI 时遇到资源文件（JSON）丢失的问题，请确保你的 `pyproject.toml` 包含以下配置：

```toml
[tool.hatch.build]
artifacts = ["hohu/locales/*.json"]

```
