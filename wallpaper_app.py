import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import ctypes
from ctypes import wintypes
import os
import json
import logging
import threading
import random
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# 初始化滚动日志（最大5MB，保留3个备份）
logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            'wallpaper.log',
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
    ],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class APIConfigManager:
    """API配置管理器（新增刷新频率配置）"""
    CONFIG_FILE = "api_config.json"
    
    DEFAULT_CONFIG = {
        "current_source": "today",
        "current_wallpaper": "",
        "resolution": "",
        "refresh_interval": 3600,  # 默认1小时
        "sources": {
            "today": {
                "name": "今日壁纸",
                "templates": {
                    "uhd": "https://bing.img.run/uhd.php",
                    "1080p": "https://bing.img.run/1920x1080.php",
                    "768p": "https://bing.img.run/1366x768.php",
                    "mobile": "https://bing.img.run/m.php"
                }
            },
            "random": {
                "name": "随机历史",
                "templates": {
                    "uhd": "https://bing.img.run/rand_uhd.php",
                    "1080p": "https://bing.img.run/rand.php",
                    "768p": "https://bing.img.run/rand_1366x768.php",
                    "mobile": "https://bing.img.run/rand_m.php"
                }
            }
        }
    }

    INTERVAL_OPTIONS = [
        ("30分钟", 1800),
        ("1小时", 3600),
        ("6小时", 21600),
        ("1天", 86400),
        ("手动", 0)
    ]

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 兼容旧版本配置
                if "refresh_interval" not in config:
                    config["refresh_interval"] = self.DEFAULT_CONFIG["refresh_interval"]
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_CONFIG

    def save_config(self):
        """保存配置文件"""
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get_source_options(self):
        """获取数据源选项列表（键值对）"""
        return [(key, self.config["sources"][key]["name"]) for key in self.config["sources"]]

class DisplayDetector:
    def __init__(self):
        # Windows API 类型定义
        self.MONITORINFOF_PRIMARY = 0x1
        self.SM_CXSCREEN = 0
        self.SM_CYSCREEN = 1

    def get_primary_resolution(self):
        """精确获取主显示器物理分辨率（修复版本）"""
        try:
            # 定义Windows结构体
            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long)
                ]

            class MONITORINFOEXW(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", RECT),
                    ("rcWork", RECT),
                    ("dwFlags", wintypes.DWORD),
                    ("szDevice", wintypes.WCHAR * 32)
                ]

            # 回调函数捕获主显示器
            primary_rect = None
            def monitor_enum_proc(hmonitor, hdc, lprect, lparam):
                nonlocal primary_rect
                info = MONITORINFOEXW()
                info.cbSize = ctypes.sizeof(MONITORINFOEXW)
                if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                    if info.dwFlags & self.MONITORINFOF_PRIMARY:
                        primary_rect = info.rcMonitor
                return 1

            # 执行显示器枚举
            callback = ctypes.WINFUNCTYPE(
                ctypes.c_int, 
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(RECT),
                wintypes.LPARAM
            )(monitor_enum_proc)
            
            ctypes.windll.user32.EnumDisplayMonitors(
                None, None, callback, 0
            )

            if primary_rect:
                width = primary_rect.right - primary_rect.left
                height = primary_rect.bottom - primary_rect.top
                logging.info(f"主显示器真实分辨率：{width}x{height}")
                return width, height

            # 回退到系统指标（应返回主显示器分辨率）
            width = ctypes.windll.user32.GetSystemMetrics(self.SM_CXSCREEN)
            height = ctypes.windll.user32.GetSystemMetrics(self.SM_CYSCREEN)
            logging.warning("使用系统指标回退方案")
            return width, height

        except Exception as e:
            logging.error(f"分辨率检测失败: {str(e)}")
            # 最终回退到1080p
            return 1920, 1080
        
    def get_primary_monitor_resolution(self):
        try:
            hmonitor = ctypes.windll.user32.MonitorFromWindow(0, 1)  # 获取主显示器的句柄
            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
            
            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT),
                            ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]
            
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                width = info.rcMonitor.right - info.rcMonitor.left
                height = info.rcMonitor.bottom - info.rcMonitor.top
                return width, height

            return 1920, 1080  # 失败则返回 1080p
        except Exception as e:
            logging.error(f"分辨率检测失败: {str(e)}")
            # 最终回退到1080p
            return 1920, 1080
        
    def get_primary_monitor_physical_resolution(self):
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", wintypes.WCHAR * 32),
                ("dmSpecVersion", wintypes.WORD),
                ("dmDriverVersion", wintypes.WORD),
                ("dmSize", wintypes.WORD),
                ("dmDriverExtra", wintypes.WORD),
                ("dmFields", wintypes.DWORD),
                ("dmPositionX", ctypes.c_long),  # 这里用 ctypes.c_long
                ("dmPositionY", ctypes.c_long),
                ("dmDisplayOrientation", wintypes.DWORD),
                ("dmColor", wintypes.DWORD),
                ("dmDuplex", wintypes.DWORD),
                ("dmYResolution", wintypes.DWORD),
                ("dmTTOption", wintypes.DWORD),
                ("dmCollate", wintypes.DWORD),
                ("dmFormName", wintypes.WCHAR * 32),
                ("dmLogPixels", wintypes.WORD),
                ("dmBitsPerPel", wintypes.DWORD),
                ("dmPelsWidth", wintypes.DWORD),
                ("dmPelsHeight", wintypes.DWORD),
                ("dmDisplayFlags", wintypes.DWORD),
                ("dmDisplayFrequency", wintypes.DWORD)
            ]

        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        
        if ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
            return devmode.dmPelsWidth, devmode.dmPelsHeight

        return 1920, 1080  # 失败则返回 1080p

class WallpaperManager:
    def __init__(self):
        self.api_config = APIConfigManager()
        self.cache_dir = os.path.join(os.path.expanduser("~"), ".wallpaper_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.current_wallpaper = self.api_config.config.get("current_wallpaper", None)
        self.detector = DisplayDetector()
        self.resolution_map = {
            (3840, 2160): "uhd",
            (1920, 1080): "1080p",
            (1366, 768): "768p",
            (1080, 1920): "mobile"
        }
        
    def get_screen_resolution(self):
        """精确获取主显示器物理分辨率"""
        try:
            # 获取实际物理分辨率
            width, height = self.detector.get_primary_resolution()
            logging.info(f"当前主显示器：{width}x{height}")

            logging.info(f"检测到物理分辨率：{width}x{height}")
            resolution_presets = {
                "uhd": (3840, 2160),
                "1080p": (1920, 1080),
                "768p": (1366, 768),
                "mobile": (1080, 1920)
            }

            # 候选方案存储
            candidates = []

            # 第一阶段：寻找完全匹配
            for preset_name, (w, h) in resolution_presets.items():
                if w == width and h == height:
                    logging.info(f"找到精确匹配：{preset_name}")
                    return preset_name
                candidates.append((preset_name, w, h))

            # 第二阶段：寻找更大尺寸的最近匹配
            larger_candidates = [c for c in candidates if c[1] >= width and c[2] >= height]
            if larger_candidates:
                # 按面积差排序（优先最小浪费）
                larger_candidates.sort(key=lambda x: (x[1]*x[2] - width*height))
                selected = larger_candidates[0][0]
                logging.info(f"选择更大尺寸：{selected}")
                return selected

            # 第三阶段：选择最高分辨率
            logging.info("无合适尺寸，使用最高分辨率")
            return "uhd"

        except Exception as e:
            logging.error(f"分辨率检测异常：{str(e)}")
            return "uhd"  # 异常时默认返回最高分辨率

    def generate_api_url(self, resolution_type=None):
        """生成API请求URL"""
        source = self.api_config.config["current_source"]
        templates = self.api_config.config["sources"][source]["templates"]
        
        if not resolution_type:
            resolution_type = self.get_screen_resolution()
        logging.info(f"下载分辨率：{resolution_type}")
        return templates.get(resolution_type, templates["1080p"])

    def download_wallpaper(self, url, save_path):
        """下载壁纸（带缓存备用功能）"""
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=15, verify=False)
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                    
                self.current_wallpaper = save_path
                self.clean_cache()  # 下载成功后清理旧缓存
                return True
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP错误（尝试 {attempt+1}/3）: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logging.error(f"下载失败（尝试 {attempt+1}/3）: {str(e)}")
        
        # 所有尝试失败后使用缓存
        return self.use_cached_wallpaper()

    def use_cached_wallpaper(self):
        """使用缓存中的随机壁纸"""
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith('.jpg')]
            if not files:
                return False
            
            selected = random.choice(files)
            self.current_wallpaper = os.path.join(self.cache_dir, selected)
            logging.info(f"使用缓存壁纸: {self.current_wallpaper}")
            return True
        except Exception as e:
            logging.error(f"获取缓存壁纸失败: {str(e)}")
            return False

    def clean_cache(self, max_files=100):
        """自动清理旧缓存文件（保留当前壁纸）"""
        try:
            files = [os.path.join(self.cache_dir, f) for f in os.listdir(self.cache_dir)]
            # 按修改时间排序（旧文件在前）
            files.sort(key=lambda x: os.path.getmtime(x))
            
            # 保留当前壁纸不被删除
            if self.current_wallpaper and self.current_wallpaper in files:
                files.remove(self.current_wallpaper)
            
            # 保留最多max_files-1个旧文件（加上当前壁纸共max_files）
            while len(files) > max_files - 1:
                old_file = files.pop(0)
                os.remove(old_file)
                logging.info(f"已清理旧缓存: {old_file}")
                
        except Exception as e:
            logging.error(f"清理缓存失败: {str(e)}")

class WallpaperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("智能壁纸管理器 v3.1")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.wm = WallpaperManager()
        self.current_image = None
        self.download_thread = None
        self.auto_refresh_id = None
        
        self.create_controls()
        self.create_preview()
        self.create_status_bar()
        self.update_ui_state(False)
        self._bind_events()
        self.schedule_auto_refresh()

    def create_controls(self):
        """创建控制面板（新增刷新频率选项）"""
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, fill=tk.X)
        
        # 数据源选择
        ttk.Label(control_frame, text="数据源:").grid(row=0, column=0, padx=5)
        self.source_var = tk.StringVar()
        self.source_combobox = ttk.Combobox(
            control_frame,
            textvariable=self.source_var,
            state="readonly"
        )
        sources = self.wm.api_config.get_source_options()
        source_names = [name for _, name in sources]
        self.source_combobox['values'] = source_names
        current_key = self.wm.api_config.config["current_source"]
        current_name = next(name for key, name in sources if key == current_key)
        self.source_var.set(current_name)
        self.source_combobox.grid(row=0, column=1, padx=5)
        
        # 分辨率选择
        ttk.Label(control_frame, text="分辨率:").grid(row=0, column=2, padx=5)
        self.res_var = tk.StringVar()
        res_options = ["auto", "uhd", "1080p", "768p", "mobile"]
        index = 0
        if self.wm.api_config.config.get("resolution", None) is not None:
            for i,res in enumerate(res_options):
                if res == self.wm.api_config.config["resolution"]:
                    index = i
                    break
        self.res_combobox = ttk.Combobox(
            control_frame,
            textvariable=self.res_var,
            values=res_options,
            state="readonly"
        )
        self.res_combobox.current(index)
        self.res_combobox.grid(row=0, column=3, padx=5)
        
        # 刷新频率
        ttk.Label(control_frame, text="刷新频率:").grid(row=0, column=4, padx=5)
        self.interval_var = tk.StringVar()
        interval_names = [name for name, _ in APIConfigManager.INTERVAL_OPTIONS]
        self.interval_combobox = ttk.Combobox(
            control_frame,
            textvariable=self.interval_var,
            values=interval_names,
            state="readonly"
        )
        current_interval = self.wm.api_config.config["refresh_interval"]
        current_name = next(name for name, value in APIConfigManager.INTERVAL_OPTIONS if value == current_interval)
        self.interval_var.set(current_name)
        self.interval_combobox.grid(row=0, column=5, padx=5)
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(control_frame, text="立即刷新", command=self.start_download_thread)
        self.refresh_btn.grid(row=0, column=6, padx=5)

    def create_preview(self):
        """创建自适应预览区域"""
        self.preview_frame = ttk.Frame(self)
        self.preview_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.preview_label = ttk.Label(self.preview_frame)
        self.preview_label.pack(expand=True, fill=tk.BOTH)
        
        if self.wm.current_wallpaper is not None:
            self.show_preview(self.wm.current_wallpaper)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _bind_events(self):
        """绑定配置变更事件"""
        self.source_var.trace_add('write', lambda *_: self.save_config())
        self.res_var.trace_add('write', lambda *_: self.save_config())
        self.interval_var.trace_add('write', lambda *_: self.save_config())
    
    def save_config(self):
        """自动保存配置"""
        try:
            # 转换数据源名称到键
            selected_name = self.source_var.get()
            sources = self.wm.api_config.get_source_options()
            selected_key = next(key for key, name in sources if name == selected_name)
            
            # 转换刷新频率名称到值
            selected_interval_name = self.interval_var.get()
            selected_interval = next(value for name, value in APIConfigManager.INTERVAL_OPTIONS if name == selected_interval_name)
            
            # 更新配置对象
            self.wm.api_config.config.update({
                "current_source": selected_key,
                "refresh_interval": selected_interval,
                "resolution": self.res_var.get(),
                "current_wallpaper": self.wm.current_wallpaper
            })
            
            # 持久化保存
            self.wm.api_config.save_config()
            logging.info("配置已自动保存")
            
            # 刷新定时任务
            self.schedule_auto_refresh()
            
        except Exception as e:
            logging.error(f"自动保存失败: {str(e)}")
            self.status_var.set("错误: 配置保存失败")

    def schedule_auto_refresh(self):
        """安排自动刷新任务"""
        # 取消现有计划
        if self.auto_refresh_id:
            self.after_cancel(self.auto_refresh_id)
        
        interval = self.wm.api_config.config["refresh_interval"]
        if interval > 0:
            next_time = datetime.now() + timedelta(seconds=interval)
            self.status_var.set(f"下次自动刷新: {next_time.strftime('%H:%M:%S')}")
            self.auto_refresh_id = self.after(interval * 1000, self.auto_refresh)
            logging.info(f"已安排自动刷新，间隔: {interval}秒")

    def auto_refresh(self):
        """执行自动刷新"""
        logging.info("开始自动刷新...")
        self.start_download_thread()
        self.schedule_auto_refresh()  # 重新安排下次刷新

    def start_download_thread(self):
        """启动下载线程"""
        if self.download_thread and self.download_thread.is_alive():
            return
            
        self.update_ui_state(True)
        self.download_thread = threading.Thread(target=self.download_task, daemon=True)
        self.download_thread.start()
        self.check_thread_status()

    def download_task(self):
        """后台下载任务"""
        try:
            res_type = self.res_var.get() if self.res_var.get() != "auto" else None
            url = self.wm.generate_api_url(res_type)
            logging.info(f"开始下载: {url}")
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            save_path = os.path.join(self.wm.cache_dir, f"wallpaper_{timestamp}.jpg")
            
            success = self.wm.download_wallpaper(url, save_path)
            if success:
                self.after(0, self.on_download_success, save_path)
            else:
                self.after(0, self.on_download_failed)
        except Exception as e:
            self.after(0, self.show_error, str(e))

    def check_thread_status(self):
        """监控线程状态"""
        if self.download_thread.is_alive():
            self.after(100, self.check_thread_status)
        else:
            self.update_ui_state(False)

    def on_download_success(self, path):
        """下载成功处理"""
        self.set_wallpaper(path)
        self.show_preview(path)
        self.status_var.set("壁纸更新成功 ✓")
        logging.info(f"成功设置壁纸: {path}")

    def on_download_failed(self):
        """下载失败处理"""
        if self.wm.current_wallpaper:
            self.set_wallpaper(self.wm.current_wallpaper)
            self.show_preview(self.wm.current_wallpaper)
            self.status_var.set("使用缓存壁纸 ✓")
            logging.warning("下载失败，已使用缓存壁纸")
        else:
            self.status_var.set("错误: 无可用壁纸")
            logging.error("所有下载尝试失败且无缓存可用")

    def show_error(self, error):
        """显示错误信息"""
        self.status_var.set(f"错误: {error}")
        logging.error(f"操作失败: {error}")

    def update_ui_state(self, downloading):
        """更新界面状态（操作期间禁用按钮）"""
        state = "disabled" if downloading else "normal"
        # self.apply_btn.config(state=state)
        self.refresh_btn.config(state=state)
        self.status_var.set("正在下载壁纸，请稍候..." if downloading else "就绪")

    def set_wallpaper(self, path):
        """设置壁纸"""
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
            self.save_config()
        except Exception as e:
            logging.error(f"设置壁纸失败: {str(e)}")
            raise

    def show_preview(self, image_path):
        """动态调整预览图（保持宽高比）"""
        try:
            img = Image.open(image_path)
            
            # 获取实际可用空间
            label_width = self.preview_label.winfo_width()
            label_height = self.preview_label.winfo_height()
            
            if label_width < 10 or label_height < 10:  # 初始默认大小
                label_width = 600
                label_height = 400
                
            # 计算最佳缩放比例
            ratio = min(
                label_width / img.width,
                label_height / img.height
            )
            new_size = (int(img.width * ratio), int(img.height * ratio))
            
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            self.current_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.current_image)
        except Exception as e:
            logging.error(f"加载预览图失败: {str(e)}")

    def on_close(self):
        """关闭窗口时清理资源"""
        # 取消自动刷新计划
        if self.auto_refresh_id:
            self.after_cancel(self.auto_refresh_id)
        
        # 等待下载线程结束
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join(timeout=5)
        
        self.destroy()

if __name__ == "__main__":
    try:
        app = WallpaperApp()
        app.mainloop()
    except Exception as e:
        logging.critical(f"程序崩溃: {str(e)}", exc_info=True)
        ctypes.windll.user32.MessageBoxW(0, f"严重错误: {str(e)}", "程序崩溃", 0x10)