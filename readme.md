# Frp Tunnel Guard (隧道守门员)

一个轻量级的 **frpc 隧道守护程序**，以系统托盘图标运行，实时监控隧道状态并自动恢复。  
当 frpc 进程异常退出或远程端口发生变化时，它会自动重启 frpc，确保远程桌面等代理永远在线。

## ✨ 功能特点

- **纯托盘运行**：无主窗口，后台静默守护，仅通过系统托盘图标显示状态。
- **自动自愈**：定时查询 DNS TXT 记录获取最新端口，若 frpc 未运行或端口变化则自动拉起。
- **动态延迟检测**：实时测量隧道延迟，托盘图标颜色直观反映连接质量（绿/蓝/橙/红/灰）。
- **右键菜单控制**：
  - `自动守护`：一键开关自动维护功能（菜单项带勾选状态）。
  - `打开远程桌面`：快速启动 Windows 远程桌面连接 (mstsc)。
  - `状态信息`：弹出气泡通知显示当前地址、端口、延迟、守护状态和持续时长。
  - `查看日志`：打开窗口展示最近 30 条守护日志，支持刷新。
  - `退出`：彻底关闭隧道并退出程序。
- **日志管理**：守护日志 (`frp_guard.log`) 自动保留最近 **1000 行**，查看窗口只展示最近 **30 行**，避免膨胀。
- **心跳记录**：每 5 分钟写入一条心跳日志，确认程序仍在运行。

## 📥 下载与使用（推荐）

如果你只是**使用**该工具，无需安装 Python 环境。直接从 [GitHub Releases](https://github.com/739342280/FrpTunnelGuard/releases) 或 [Actions](https://github.com/739342280/FrpTunnelGuard/actions) 页面下载已经打包好的 `FrpTunnelGuard.zip`。

1. 解压 `FrpTunnelGuard.zip` 到任意目录。
2. 编辑 `frpc.toml`，填入你自己的服务器地址和 token（见后文配置说明）。
3. 双击 `FrpTunnelGuard.exe` 启动程序。
4. 系统托盘区域会出现一个彩色圆点图标，右键即可操作。

> 💡 压缩包内已包含 `frpc.exe` 和 `frpc.toml` 模板，无需额外下载。

## 🛠 开发环境搭建

如果你需要修改源代码或自行打包，请按以下步骤操作。

### 📦 环境依赖

- **Windows 操作系统**（系统托盘功能依赖 Windows API）
- **Python 3.8+**（推荐 3.11+）
- **frpc 客户端**：将 `frpc.exe` 放入项目根目录

安装 Python 依赖包：

```bash
pip install -r requirements.txt
```

### 🗂 项目结构

```
FrpTunnelGuard/
├── guard.py               # 主程序：托盘守护脚本
├── frpc.exe               # frp 客户端可执行文件（不提交至 Git，需自行准备）
├── frpc.toml.example      # frp 配置文件模板（提交到 Git）
├── frpc.toml              # 你的真实配置文件（已忽略，不会提交）
├── requirements.txt       # Python 依赖列表
├── .gitignore             # Git 忽略规则
├── .github/workflows/     # GitHub Actions 自动打包工作流
└── README.md
```

- `frpc.toml.example` 是配置模板，可供打包或新用户参考。
- 真实 `frpc.toml` 和所有日志文件（`frpc.log`、`frp_guard.log`）都不会被 Git 跟踪。

### ⚙️ 配置说明

#### 1. frpc.toml

解压后你会获得一个 `frpc.toml` 模板，你需要将其中的占位符替换为自己的连接信息。  
示例配置：

```toml
# ================= 基础连接设置 =================
serverAddr = "your-server.com"   # 替换为你的 frp 服务器地址
serverPort = 2469

[auth]
token = "your_token"              # 替换为你的服务器 token

[log]
to = "./frpc.log"
level = "info"
maxDays = 3

[transport]
heartbeatInterval = 30
heartbeatTimeout = 90

# 示例：远程桌面隧道
[[proxies]]
name = "work-pc-rdp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3389
remotePort = 33389                # 服务器端绑定的远程端口，注意不要冲突
```

> ⚠️ 请务必不要将真实 token 提交到 GitHub 仓库。仓库中仅保留 `frpc.toml.example` 作为模板。

#### 2. guard.py 中的 CONFIG

脚本开头的 `CONFIG` 字典包含可自定义的参数（通常无需修改）：

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `domain` | `work.doggge.com` | 用于查询 TXT 记录获取端口的域名 |
| `work_dir` | 脚本所在目录 | frpc 工作目录（无需修改） |
| `frpc_exe` | `frpc.exe` | frpc 可执行文件名 |
| `config_file` | `frpc.toml` | frpc 配置文件 |
| `status_freq` | `1.5` | 托盘图标和状态刷新间隔（秒） |
| `dns_freq` | `60` | DNS TXT 记录查询间隔（秒） |
| `heartbeat_freq` | `300` | 心跳日志间隔（秒） |
| `max_log_lines` | `1000` | 守护日志最大保留行数 |
| `log_view_lines` | `30` | 查看日志窗口显示的最近行数 |

> 🔧 通常你只需要修改 `domain` 为你自己的域名，其他保持默认即可。

## 🚀 从源码运行

1. 确保 `frpc.exe` 和 `frpc.toml`（包含真实配置）已放在项目根目录。
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行脚本：
   ```bash
   python guard.py
   ```
4. 程序会在系统托盘出现，使用右键菜单控制。

## 📦 自动打包（GitHub Actions）

本项目配置了 GitHub Actions，每次推送到 `main` 分支或手动触发时，会自动：
- 下载最新版 frpc.exe（如果仓库中不包含）
- 用 `frpc.toml.example` 生成干净的配置文件
- 使用 PyInstaller 打包为独立的 Windows 文件夹
- 产出 `FrpTunnelGuard.zip` 并上传为 Artifact

你可以在仓库的 **Actions** 页面找到构建结果并下载。

## 🖱 托盘操作说明

- **鼠标悬停**：显示延迟和端口信息。
- **右键菜单**：
  - `自动守护`：点击切换守护状态，勾选表示自动维护开启。
  - `打开远程桌面`：启动 Windows 远程桌面连接。
  - `状态信息`：弹出通知气泡显示当前连接详情。
  - `查看日志`：打开可关闭的窗口，展示最近 30 条守护日志，支持“刷新”。
  - `退出`：停止 frpc 进程并退出程序。

## 📝 日志文件

- **frpc 日志** (`frpc.log`)：由 frpc 自身生成，受 `frpc.toml` 中 `maxDays` 控制，最多保留 3 天。
- **守护日志** (`frp_guard.log`)：记录守护程序的所有操作，包括启动、心跳、端口同步、自愈动作等。自动保留最近 1000 行。

## ⚠️ 注意事项

- 程序运行时不要手动启动或关闭 `frpc.exe`，守护程序会自动管理。
- 如果需要修改 `frpc.toml` 中的端口，请直接修改 DNS TXT 记录，守护程序会在下次 DNS 查询时自动同步。
- 若需开机自启，可将 `FrpTunnelGuard.exe` 的快捷方式放入 Windows 启动文件夹（`shell:startup`）。

## 📜 许可

本项目采用 [Apache License 2.0](LICENSE) 许可证。

- 自行编写的 Python 代码（`guard.py` 及其编译产物）基于 Apache License 2.0 发布。
- 本项目分发的 `frpc.exe` 来自 [fatedier/frp](https://github.com/fatedier/frp)，同样遵循 **Apache License 2.0** 许可，其版权归 frp 原作者所有。

详细信息请参见项目根目录下的 [LICENSE](LICENSE) 与 [NOTICE](NOTICE) 文件。

