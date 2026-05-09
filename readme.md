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

## 📦 环境依赖

- **Windows 操作系统**（其他平台需自行适配系统托盘相关调用）
- **Python 3.8+**（推荐 3.11+）
- **frpc 客户端**：`frpc.exe` 与 `frpc.toml` 应与脚本放在同一目录

安装 Python 依赖包（建议在项目目录下执行）：

```bash
pip install psutil dnspython pillow pystray
```

> 📌 `psutil` 用于进程管理，`dnspython` 用于 DNS TXT 查询，`pillow` 用于绘制托盘图标，`pystray` 用于系统托盘交互。

## 🗂 项目结构

```
你的项目文件夹/
├── guard.py          # 主程序：托盘守护脚本
├── frpc.exe          # frp 客户端可执行文件
├── frpc.toml         # frp 客户端配置文件
└── frp_guard.log     # 守护程序日志（自动生成）
```

> 💡 所有文件放在同一目录下即可实现“拎包即用”，无需修改任何绝对路径。

## ⚙️ 配置说明

### 1. frpc.toml

`frpc.toml` 是 frp 客户端的标准配置文件。你需要确保里面的 `serverAddr` 和 `token` 正确，并配置好代理隧道。  
示例配置：

```toml
# ================= 基础连接设置 =================
serverAddr = "your-server.com"
serverPort = 2469

[auth]
token = "your_token"

[log]
to = "./frpc.log"
level = "info"
maxDays = 3

[transport]
heartbeatInterval = 30
heartbeatTimeout = 90

[[proxies]]
name = "work-pc-rdp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 3389
remotePort = 33389
```

> ⚠️ 请将 `serverAddr` 和 `token` 替换为你自己的服务端地址和密钥。

### 2. guard.py 中的 CONFIG

脚本开头的 `CONFIG` 字典包含可自定义的参数：

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

## 🚀 运行方式

1. 确保 `frpc.exe` 和 `frpc.toml` 与 `guard.py` 在同一文件夹。
2. 安装好所有依赖（见上）。
3. 双击运行 `guard.py`，或通过命令行启动：
   ```bash
   python guard.py
   ```
4. 程序没有窗口，任务栏图标也会隐藏，只在系统托盘（通知区域）出现一个彩色圆点图标。

## 🖱 托盘操作说明

- **鼠标悬停**：显示延迟和端口信息。
- **右键菜单**：
  - `自动守护`：点击切换守护状态，勾选表示自动维护开启。
  - `打开远程桌面`：启动 Windows 远程桌面连接。
  - `状态信息`：弹出通知气泡显示当前连接详情。
  - `查看日志`：打开一个可关闭的窗口，展示最近 30 条守护日志，有“刷新”按钮。
  - `退出`：停止 frpc 进程并退出程序。

## 📝 日志文件

- **frpc 日志** (`frpc.log`)：由 frpc 自身生成，受 `frpc.toml` 中 `maxDays` 控制，最多保留 3 天。
- **守护日志** (`frp_guard.log`)：记录守护程序的所有操作，包括启动、心跳、端口同步、自愈动作等。自动保留最近 1000 行。

## ⚠️ 注意事项

- 程序运行时不要手动启动或关闭 `frpc.exe`，守护程序会自动管理。
- 如果需要修改 `frpc.toml` 中的端口，请直接修改 DNS TXT 记录，守护程序会在下次 DNS 查询时自动同步。
- 若需开机自启，可将 `pythonw.exe guard.py` 的快捷方式放入 Windows 启动文件夹（`shell:startup`），实现无控制台窗口开机启动。

## 📄 许可

本项目仅供个人学习与内部网络维护使用。请勿用于非法用途。