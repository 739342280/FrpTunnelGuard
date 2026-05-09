import re
import os
import time
import sys
import socket
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import dns.resolver
import psutil
from PIL import Image, ImageDraw
import pystray

# ------ 程序根目录：自动适配开发环境与 PyInstaller 打包环境 ------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)      # 打包后 exe 所在目录
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 开发环境脚本目录

CONFIG = {
    "domain": "work.doggge.com",
    "work_dir": BASE_DIR,                      # 现在与 exe（或脚本）同目录
    "frpc_exe": "frpc.exe",
    "config_file": "frpc.toml",
    "status_freq": 1.5,
    "dns_freq": 60,
    "heartbeat_freq": 300,
    "log_file": os.path.join(BASE_DIR, "frp_guard.log"),   # 守护日志
    "max_log_lines": 1000,                     # 日志最大保留行数
    "log_view_lines": 30                       # 查看日志时展示的行数
}

class FrpGuard:
    def __init__(self, log_cb, tray_cb):
        self.log_cb = log_cb
        self.tray_cb = tray_cb
        self.current_port = ""
        self.is_running = True
        self.is_active = True
        self.full_path = os.path.join(BASE_DIR, CONFIG["frpc_exe"])

        self.connection_start_time = None
        self.last_heartbeat = time.time()
        self.initial_online_logged = False

        log_dir = os.path.dirname(CONFIG["log_file"])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def write_log(self, message, level="INFO"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{now}] [{level}] {message}\n"
        try:
            with open(CONFIG["log_file"], "a", encoding="utf-8") as f:
                f.write(log_line)
            # 写入后自动修剪日志（保留最近1000行）
            self._trim_log(CONFIG["log_file"], CONFIG["max_log_lines"])
        except Exception:
            pass
        if self.log_cb:
            self.log_cb(log_line.strip())

    def _trim_log(self, filepath, max_lines):
        """将日志文件保留为最近的 max_lines 行"""
        try:
            # 检查文件是否存在，并确保不是空文件
            if not os.path.exists(filepath):
                return
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # 如果行数没超过限制，直接返回
            if len(lines) <= max_lines:
                return
            # 保留最后 max_lines 行
            trimmed = lines[-max_lines:]
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(trimmed)
        except Exception:
            # 裁剪失败不致命，静默处理
            pass

    def get_latency(self):
        if not self.is_active or not self.current_port:
            return 999
        start_time = time.time()
        try:
            with socket.create_connection((CONFIG["domain"], int(self.current_port)), timeout=0.8):
                return int((time.time() - start_time) * 1000)
        except:
            return 999

    def get_color(self, ms):
        if not self.is_active:
            return (100, 100, 100)
        if ms < 50:
            return (0, 255, 0)
        if ms < 100:
            return (0, 0, 255)
        if ms < 200:
            return (255, 165, 0)
        if ms < 500:
            return (255, 0, 0)
        return (40, 40, 40)

    def force_update_tray(self):
        if not self.is_running:
            return
        ms = self.get_latency()
        color = self.get_color(ms)
        text = f"延迟: {ms}ms | 端口: {self.current_port}" if self.is_active else "守护已暂停"
        self.tray_cb(color, text)

    def stop_frpc(self):
        self.write_log("正在停止 frpc 进程...", "WARN")
        for _ in range(2):
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == CONFIG["frpc_exe"]:
                    try:
                        proc.kill()
                        self.write_log(f"已终止进程 PID: {proc.pid}", "WARN")
                    except Exception as e:
                        self.write_log(f"终止进程失败: {e}", "ERROR")
            time.sleep(0.1)
        self.connection_start_time = None
        self.current_port = ""
        self.initial_online_logged = False
        self.write_log("frpc 进程已全部停止", "SUCCESS")

    def start_frpc(self, port):
        if not self.is_active:
            self.write_log("守护已暂停，跳过 frpc 启动", "WARN")
            return
        path = os.path.join(CONFIG["work_dir"], CONFIG["config_file"])
        try:
            needs_write = True
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if f"serverPort = {port}" in content:
                    needs_write = False

            if needs_write:
                new_content = re.sub(r'(?m)^serverPort\s*=.*', f'serverPort = {port}', content)
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(new_content)
                self.write_log(f"配置文件已同步端口: {port}", "SUCCESS")
            else:
                self.write_log(f"配置文件端口已为 {port}，无需更改", "INFO")

            subprocess.Popen(
                [self.full_path, "-c", CONFIG["config_file"]],
                cwd=CONFIG["work_dir"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.current_port = port
            self.connection_start_time = datetime.now()
            self.write_log(f"frpc 已启动，连接至 {CONFIG['domain']}:{port}", "SUCCESS")

            if not self.initial_online_logged:
                time.sleep(1)   # 等待连接建立，获得更准确的延迟
                ms = self.get_latency()
                self.write_log(
                    f"✅ 隧道已就绪 - {CONFIG['domain']}:{port} | 延迟: {ms}ms",
                    "SUCCESS"
                )
                self.initial_online_logged = True
            else:
                ms = self.get_latency()
                self.write_log(
                    f"🔄 端口已切换 - {CONFIG['domain']}:{port} | 延迟: {ms}ms",
                    "WARN"
                )

        except Exception as e:
            self.write_log(f"frpc 启动失败: {e}", "ERROR")

    def sentinel_loop(self):
        while self.is_running:
            self.force_update_tray()
            now = time.time()
            if now - self.last_heartbeat >= CONFIG["heartbeat_freq"]:
                ms = self.get_latency()
                port_info = f"端口: {self.current_port}" if self.current_port else "端口未分配"
                self.write_log(f"守护心跳 - 延迟: {ms}ms | {port_info} | 守护: {'开' if self.is_active else '关'}", "INFO")
                self.last_heartbeat = now
            time.sleep(CONFIG["status_freq"])

    def monitor_loop(self):
        self.write_log("隧道守门员开始监控（每60秒检测DNS）")

        while self.is_running:
            if self.is_active:
                frp_alive = any(p.info['name'] == CONFIG["frpc_exe"] for p in psutil.process_iter(['name']))
                try:
                    res = dns.resolver.Resolver()
                    res.nameservers = ['119.29.29.29']
                    ans = res.resolve(CONFIG["domain"], 'TXT')
                    new_port = re.sub(r'[^0-9]', '', str(ans[0].strings[0]))
                    self.write_log(f"DNS解析成功: {CONFIG['domain']} TXT -> 端口 {new_port}", "INFO")
                    if not frp_alive or new_port != self.current_port:
                        if not frp_alive:
                            self.write_log("检测到 frpc 未运行，触发自愈启动", "WARN")
                        if new_port != self.current_port:
                            self.write_log(f"端口变化: {self.current_port} -> {new_port}，将重启frpc", "WARN")
                        self.start_frpc(new_port)
                except Exception as e:
                    self.write_log(f"DNS解析失败: {e}", "ERROR")
            time.sleep(CONFIG["dns_freq"])

    def get_status_info(self):
        frp_alive = any(p.info['name'] == CONFIG["frpc_exe"] for p in psutil.process_iter(['name']))
        latency = self.get_latency()
        port = self.current_port if self.current_port else "未知"

        if self.connection_start_time and frp_alive:
            delta = datetime.now() - self.connection_start_time
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours}小时{minutes}分{seconds}秒"
        else:
            duration = "未连接"

        return {
            "domain": CONFIG["domain"],
            "port": port,
            "latency": latency,
            "frp_alive": frp_alive,
            "guard_active": self.is_active,
            "duration": duration
        }


# --- 托盘管理器（整合所有功能） ---
class TrayManager:
    def __init__(self, guard):
        self.guard = guard
        self.icon = None
        self.guard.tray_cb = self.update_tray

    def create_img(self, color):
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=color + (255,), outline=(255,255,255,180), width=3)
        draw.ellipse((16, 16, 42, 42), fill=(255, 255, 255, 45))
        return img

    def update_tray(self, color, title):
        if self.icon:
            self.icon.icon = self.create_img(color)
            self.icon.title = title

    def toggle_auto_guard(self, icon, item):
        self.guard.is_active = not self.guard.is_active
        self.update_menu()
        if not self.guard.is_active:
            self.guard.stop_frpc()
            self.guard.force_update_tray()
        else:
            self.guard.write_log("守护已手动恢复，等待下一次DNS检测", "SUCCESS")
            self.guard.force_update_tray()

    def open_rdp(self, icon, item):
        subprocess.Popen("mstsc", shell=True)

    def show_status(self, icon, item):
        info = self.guard.get_status_info()
        msg = (
            f"地址: {info['domain']}:{info['port']}\n"
            f"延迟: {info['latency']} ms\n"
            f"frp 进程: {'运行中' if info['frp_alive'] else '未运行'}\n"
            f"守护开关: {'开启' if info['guard_active'] else '关闭'}\n"
            f"持续时长: {info['duration']}"
        )
        self.icon.notify(msg, "隧道守护状态")

    def show_log_window(self, icon, item):
        """弹出日志窗口，仅显示最近30条日志"""
        def run_log_window():
            window = tk.Tk()
            window.title("隧道守护日志 (最近30条)")
            window.geometry("600x400")
            text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, state='disabled')
            text_area.pack(fill=tk.BOTH, expand=True)

            def refresh_log():
                try:
                    with open(CONFIG["log_file"], "r", encoding="utf-8") as f:
                        all_lines = f.readlines()
                    # 取最后30行；如果不足30行则全部显示
                    recent_lines = all_lines[-CONFIG["log_view_lines"]:]
                    content = "".join(recent_lines) if recent_lines else "（暂无日志）"
                except FileNotFoundError:
                    content = "日志文件未找到"
                except Exception as e:
                    content = f"读取日志失败: {e}"

                text_area.config(state='normal')
                text_area.delete(1.0, tk.END)
                text_area.insert(tk.END, content)
                text_area.config(state='disabled')
                text_area.see(tk.END)

            refresh_log()
            tk.Button(window, text="刷新", command=refresh_log).pack(pady=5)
            window.mainloop()

        threading.Thread(target=run_log_window, daemon=True).start()

    def on_exit(self, icon, item):
        self.guard.is_running = False
        self.guard.stop_frpc()
        icon.stop()

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                "自动守护",
                self.toggle_auto_guard,
                checked=lambda item: self.guard.is_active
            ),
            pystray.MenuItem("打开远程桌面", self.open_rdp),
            pystray.MenuItem("状态信息", self.show_status),
            pystray.MenuItem("查看日志", self.show_log_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.on_exit)
        )

    def update_menu(self):
        if self.icon:
            self.icon.menu = self._build_menu()
            self.icon.update_menu()

    def run(self):
        self.icon = pystray.Icon(
            "FrpGuard",
            icon=self.create_img((128, 128, 128)),
            title="隧道守门员"
        )
        self.icon.menu = self._build_menu()
        self.icon.run()


# --- 程序入口 ---
if __name__ == "__main__":
    guard = FrpGuard(log_cb=print, tray_cb=None)
    tray = TrayManager(guard)

    threading.Thread(target=guard.monitor_loop, daemon=True).start()
    threading.Thread(target=guard.sentinel_loop, daemon=True).start()

    tray.run()