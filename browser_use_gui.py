#!/usr/bin/env python3
"""Browser-Use GUI - 图形界面用于配置和运行浏览器自动化任务。"""

import asyncio
import json
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import dotenv


class BrowserUseGUI:
    """Browser-Use的主GUI应用。"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Browser-Use GUI - 浏览器自动化工具")
        self.root.geometry("1050x800")
        self.root.minsize(850, 650)

        # 设置主题颜色
        self.colors = {
            'bg': '#f0f2f5',
            'frame_bg': '#ffffff',
            'primary': '#4a90d9',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'text': '#333333',
        }

        self.root.configure(bg=self.colors['bg'])

        self.task_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.agent = None
        self.is_running = False
        self.browser_detected = False
        self.browser_path = None
        self.browser_type = None

        self._load_env_config()
        self._build_ui()
        self._detect_browser()

    def _load_env_config(self):
        """从.env文件加载配置。"""
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            dotenv.load_dotenv(env_path)

        self.config = {
            'api_key': os.getenv('BROWSER_USE_API_KEY', ''),
            'base_url': os.getenv('BROWSER_USE_BASE_URL', ''),
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'openai_base_url': os.getenv('OPENAI_BASE_URL', ''),
            'google_api_key': os.getenv('GOOGLE_API_KEY', ''),
            'google_base_url': os.getenv('GOOGLE_BASE_URL', ''),
            'local_api_key': os.getenv('LOCAL_API_KEY', 'key'),
            'local_base_url': os.getenv('LOCAL_BASE_URL', 'http://192.168.0.120:1234/v1'),
            'model_name': os.getenv('BU_MODEL_NAME', 'local_gemma_4_26b'),
            'headless': os.getenv('BU_HEADLESS', 'false').lower() == 'true',
            'max_steps': int(os.getenv('BU_MAX_STEPS', '100')),
            'cdp_url': os.getenv('BU_CDP_URL', ''),
        }

    def _save_env_config(self):
        """保存配置到.env文件。"""
        env_path = Path(__file__).parent / '.env'
        env_content = f"""# Browser Use Configuration
BROWSER_USE_LOGGING_LEVEL=info
ANONYMIZED_TELEMETRY=true
BROWSER_USE_VERSION_CHECK=true

# ============================================
# API配置 - 根据需要填写对应的API Key
# ============================================

# Browser-Use Cloud API (推荐)
# 获取地址: https://cloud.browser-use.com/new-api-key
BROWSER_USE_API_KEY={self.config.get('api_key', '')}
# 自定义Base URL (可选，用于代理或本地部署)
BROWSER_USE_BASE_URL={self.config.get('base_url', '')}

# OpenAI API
# 获取地址: https://platform.openai.com/api-keys
OPENAI_API_KEY={self.config.get('openai_api_key', '')}
# 自定义Base URL (可选，用于OneAPI/NewAPI等中转服务)
# 例如: http://localhost:3000/v1 或 https://api.openai-proxy.com/v1
OPENAI_BASE_URL={self.config.get('openai_base_url', '')}

# Google Gemini API
# 获取地址: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY={self.config.get('google_api_key', '')}
# 自定义Base URL (可选)
GOOGLE_BASE_URL={self.config.get('google_base_url', '')}

# 本地大模型 API (LM Studio, Ollama, LocalAI等)
# 默认地址: http://127.0.0.1:1234/v1
LOCAL_API_KEY={self.config.get('local_api_key', '')}
LOCAL_BASE_URL={self.config.get('local_base_url', 'http://127.0.0.1:1234/v1')}

# ============================================
# 模型配置
# ============================================
# 可用模型: bu_latest, bu_1_0, bu_2_0
#          openai_gpt_4o, openai_gpt_4o_mini, openai_gpt_4_1_mini
#          openai_o1, openai_o1_mini, openai_o3, openai_o3_mini
#          openai_gpt_5, openai_gpt_5_mini
#          azure_gpt_4o, azure_gpt_4_1_mini
#          google_gemini_2_5_pro, google_gemini_2_5_flash
BU_MODEL_NAME={self.config.get('model_name', 'bu_latest')}

# ============================================
# 浏览器配置
# ============================================
# 无头模式: true=不显示浏览器窗口, false=显示浏览器窗口
BU_HEADLESS={'true' if self.config.get('headless', False) else 'false'}

# 最大执行步数
BU_MAX_STEPS={self.config.get('max_steps', 100)}

# CDP URL (可选，连接到已运行的浏览器)
BU_CDP_URL={self.config.get('cdp_url', '')}
"""
        env_path.write_text(env_content, encoding='utf-8')

        # 同时更新环境变量
        os.environ['BROWSER_USE_API_KEY'] = self.config.get('api_key', '')
        os.environ['BROWSER_USE_BASE_URL'] = self.config.get('base_url', '')
        os.environ['OPENAI_API_KEY'] = self.config.get('openai_api_key', '')
        os.environ['OPENAI_BASE_URL'] = self.config.get('openai_base_url', '')
        os.environ['GOOGLE_API_KEY'] = self.config.get('google_api_key', '')
        os.environ['GOOGLE_BASE_URL'] = self.config.get('google_base_url', '')
        os.environ['LOCAL_API_KEY'] = self.config.get('local_api_key', '')
        os.environ['LOCAL_BASE_URL'] = self.config.get('local_base_url', 'http://127.0.0.1:1234/v1')
        os.environ['BU_MODEL_NAME'] = self.config.get('model_name', 'bu_latest')
        os.environ['BU_HEADLESS'] = 'true' if self.config.get('headless', False) else 'false'
        os.environ['BU_MAX_STEPS'] = str(self.config.get('max_steps', 100))
        os.environ['BU_CDP_URL'] = self.config.get('cdp_url', '')

    def _detect_browser(self):
        """检测可用的浏览器（内置Chromium、系统Chrome/Edge、Playwright Chromium）。"""
        # 优先级1: 检查内置 browser_chromium 目录
        packaged = self._find_packaged_chromium()
        if packaged:
            self.browser_detected = True
            self.browser_path = packaged
            self.browser_type = "内置 Chromium"
            self._update_browser_status()
            return

        # 优先级2: 检查系统 Chrome
        chrome = self._find_system_chrome()
        if chrome:
            self.browser_detected = True
            self.browser_path = chrome
            self.browser_type = "系统 Chrome"
            self._update_browser_status()
            return

        # 优先级3: 检查系统 Edge
        edge = self._find_system_edge()
        if edge:
            self.browser_detected = True
            self.browser_path = edge
            self.browser_type = "系统 Edge"
            self._update_browser_status()
            return

        # 优先级4: 检查 Playwright Chromium
        playwright = self._find_playwright_chromium()
        if playwright:
            self.browser_detected = True
            self.browser_path = playwright
            self.browser_type = "Playwright Chromium"
            self._update_browser_status()
            return

        # 未检测到浏览器
        self.browser_detected = False
        self.browser_path = None
        self.browser_type = None
        self._update_browser_status()

    def _find_packaged_chromium(self) -> Optional[str]:
        """查找内置 Chromium 浏览器。"""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent / '_internal' / 'browser_chromium'
        else:
            base_dir = Path(__file__).parent / 'browser_chromium'

        if not base_dir.exists():
            return None

        if sys.platform == 'win32':
            patterns = [
                base_dir / 'chrome-win' / 'chrome.exe',
                base_dir / 'chrome-win64' / 'chrome.exe',
            ]
            for path in patterns:
                if path.exists():
                    return str(path)
            # 尝试匹配版本号
            for pattern in ['chrome-win-*', 'chrome-win64-*']:
                for match in base_dir.glob(pattern):
                    exe = match / 'chrome.exe'
                    if exe.exists():
                        return str(exe)

        elif sys.platform == 'darwin':
            patterns = [
                base_dir / 'chrome-mac' / 'Chromium.app' / 'Contents' / 'MacOS' / 'Chromium',
            ]
            for path in patterns:
                if path.exists():
                    return str(path)

        elif sys.platform == 'linux':
            patterns = [
                base_dir / 'chrome-linux' / 'chrome',
                base_dir / 'chrome-linux64' / 'chrome',
            ]
            for path in patterns:
                if path.exists():
                    return str(path)

        return None

    def _find_system_chrome(self) -> Optional[str]:
        """查找系统已安装的 Chrome 浏览器。"""
        import glob

        if sys.platform == 'win32':
            paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'Application' / 'chrome.exe'),
            ]
            # 动态查找最新版本号
            app_dir = Path(r'C:\Program Files\Google\Chrome\Application')
            if app_dir.exists():
                for d in app_dir.iterdir():
                    if d.is_dir() and d.name.replace('.', '').isdigit():
                        exe = d / 'chrome.exe'
                        if exe.exists():
                            return str(exe)

            for p in paths:
                if Path(p).exists():
                    return p

        elif sys.platform == 'darwin':
            chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            if Path(chrome_path).exists():
                return chrome_path

        elif sys.platform == 'linux':
            for p in ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/local/bin/google-chrome']:
                if Path(p).exists():
                    return p

        return None

    def _find_system_edge(self) -> Optional[str]:
        """查找系统已安装的 Edge 浏览器。"""
        if sys.platform == 'win32':
            paths = [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe'),
            ]
            # 动态查找最新版本号
            app_dir = Path(r'C:\Program Files (x86)\Microsoft\Edge\Application')
            if app_dir.exists():
                for d in app_dir.iterdir():
                    if d.is_dir() and d.name.replace('.', '').isdigit():
                        exe = d / 'msedge.exe'
                        if exe.exists():
                            return str(exe)

            for p in paths:
                if Path(p).exists():
                    return p

        return None

    def _find_playwright_chromium(self) -> Optional[str]:
        """查找 Playwright 安装的 Chromium。"""
        playwright_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
        if not playwright_path:
            if sys.platform == 'win32':
                playwright_path = str(Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright')
            elif sys.platform == 'darwin':
                playwright_path = str(Path.home() / 'Library' / 'Caches' / 'ms-playwright')
            else:
                playwright_path = str(Path.home() / '.cache' / 'ms-playwright')

        base = Path(playwright_path).expanduser()
        if not base.exists():
            return None

        if sys.platform == 'win32':
            for d in base.iterdir():
                if d.is_dir() and d.name.startswith('chromium-') and not d.name.endswith('headless_shell'):
                    exe = d / 'chrome-win' / 'chrome.exe'
                    if exe.exists():
                        return str(exe)

        elif sys.platform == 'darwin':
            for d in base.iterdir():
                if d.is_dir() and d.name.startswith('chromium-'):
                    exe = d / 'chrome-mac' / 'Chromium.app' / 'Contents' / 'MacOS' / 'Chromium'
                    if exe.exists():
                        return str(exe)

        elif sys.platform == 'linux':
            for d in base.iterdir():
                if d.is_dir() and d.name.startswith('chromium-'):
                    exe = d / 'chrome-linux' / 'chrome'
                    if exe.exists():
                        return str(exe)

        return None

    def _update_browser_status(self):
        """更新浏览器状态显示。"""
        if hasattr(self, 'browser_status_label'):
            if self.browser_detected:
                self.browser_status_label.config(
                    text=f"✓ {self.browser_type} (路径: {self.browser_path})",
                    foreground=self.colors['success']
                )
                self.install_chromium_btn.config(state=tk.DISABLED)
            else:
                self.browser_status_label.config(
                    text="✗ 未检测到浏览器，请安装 Chrome 或点击右侧按钮安装 Chromium",
                    foreground=self.colors['error']
                )
                self.install_chromium_btn.config(state=tk.NORMAL)

    def _build_ui(self):
        """构建用户界面。"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 配置选项卡
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="⚙ 配置")
        self._build_config_tab()

        # 任务选项卡
        self.task_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.task_tab, text="🚀 任务执行")
        self._build_task_tab()

        # 状态栏
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(self.status_frame, text="就绪", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))

    def _build_config_tab(self):
        """构建配置选项卡。"""
        # 浏览器状态区域
        browser_frame = ttk.LabelFrame(self.config_tab, text="浏览器状态", padding="10")
        browser_frame.pack(fill=tk.X, padx=10, pady=5)

        self.browser_status_label = ttk.Label(browser_frame, text="检查中...", foreground=self.colors['warning'])
        self.browser_status_label.pack(side=tk.LEFT, padx=(0, 10))

        self.install_chromium_btn = ttk.Button(
            browser_frame,
            text="安装 Chromium",
            command=self._on_install_chromium
        )
        self.install_chromium_btn.pack(side=tk.LEFT)

        # API配置区域
        api_frame = ttk.LabelFrame(self.config_tab, text="API配置", padding="10")
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        # Browser-Use API
        ttk.Label(api_frame, text="Browser-Use API Key:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.api_key_var = tk.StringVar(value=self.config['api_key'])
        ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show='*').grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(api_frame, text="Browser-Use Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.base_url_var = tk.StringVar(value=self.config['base_url'])
        ttk.Entry(api_frame, textvariable=self.base_url_var, width=50).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # OpenAI API
        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.openai_api_key_var = tk.StringVar(value=self.config['openai_api_key'])
        ttk.Entry(api_frame, textvariable=self.openai_api_key_var, width=50, show='*').grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(api_frame, text="OpenAI Base URL:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.openai_base_url_var = tk.StringVar(value=self.config['openai_base_url'])
        ttk.Entry(api_frame, textvariable=self.openai_base_url_var, width=50).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

        # Google API
        ttk.Label(api_frame, text="Google API Key:").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        self.google_api_key_var = tk.StringVar(value=self.config['google_api_key'])
        ttk.Entry(api_frame, textvariable=self.google_api_key_var, width=50, show='*').grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(api_frame, text="Google Base URL:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
        self.google_base_url_var = tk.StringVar(value=self.config['google_base_url'])
        ttk.Entry(api_frame, textvariable=self.google_base_url_var, width=50).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)

        # 本地大模型 API
        ttk.Label(api_frame, text="本地API Key:").grid(row=6, column=0, sticky=tk.W, pady=5, padx=5)
        self.local_api_key_var = tk.StringVar(value=self.config['local_api_key'])
        ttk.Entry(api_frame, textvariable=self.local_api_key_var, width=50, show='*').grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(api_frame, text="本地Base URL:").grid(row=7, column=0, sticky=tk.W, pady=5, padx=5)
        self.local_base_url_var = tk.StringVar(value=self.config['local_base_url'])
        ttk.Entry(api_frame, textvariable=self.local_base_url_var, width=50).grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(api_frame, text="LM Studio/Ollama等本地模型服务地址", foreground='gray').grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=5)

        # 模型配置区域
        model_frame = ttk.LabelFrame(self.config_tab, text="模型配置", padding="10")
        model_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(model_frame, text="模型名称:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.model_name_var = tk.StringVar(value=self.config['model_name'])
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_name_var,
            width=47,
            values=[
                'bu_latest', 'bu_1_0', 'bu_2_0',
                'openai_gpt_4o', 'openai_gpt_4o_mini', 'openai_gpt_4_1_mini',
                'openai_o1', 'openai_o1_mini', 'openai_o3', 'openai_o3_mini',
                'openai_gpt_5', 'openai_gpt_5_mini',
                'azure_gpt_4o', 'azure_gpt_4_1_mini',
                'google_gemini_2_5_pro', 'google_gemini_2_5_flash',
                'local_qwen3_6_35b', 'local_qwen3_6_27b', 'local_nemotron_3_nano_omni', 'local_gemma_4_26b',
            ]
        )
        model_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(model_frame, text="最大步数:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.max_steps_var = tk.StringVar(value=str(self.config['max_steps']))
        ttk.Entry(model_frame, textvariable=self.max_steps_var, width=50).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        self.headless_var = tk.BooleanVar(value=self.config['headless'])
        ttk.Checkbutton(model_frame, text="无头模式（不显示浏览器窗口）", variable=self.headless_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5, padx=5)

        # 浏览器配置区域
        browser_config_frame = ttk.LabelFrame(self.config_tab, text="浏览器高级配置", padding="10")
        browser_config_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(browser_config_frame, text="CDP URL (可选):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.cdp_url_var = tk.StringVar(value=self.config['cdp_url'])
        ttk.Entry(browser_config_frame, textvariable=self.cdp_url_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(browser_config_frame, text="连接到已运行的浏览器 (如: http://localhost:9222)", foreground='gray').grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        # 保存和测试按钮
        btn_frame = ttk.Frame(self.config_tab)
        btn_frame.pack(pady=10)

        save_btn = ttk.Button(btn_frame, text="💾 保存配置", command=self._on_save_config)
        save_btn.pack(side=tk.LEFT, padx=5)

        self.test_conn_btn = ttk.Button(btn_frame, text="🔗 测试连接", command=self._on_test_connection)
        self.test_conn_btn.pack(side=tk.LEFT, padx=5)

        # 连接状态标签
        self.conn_status_label = ttk.Label(self.config_tab, text="", foreground=self.colors['success'])
        self.conn_status_label.pack(pady=(0, 5))

    def _build_task_tab(self):
        """构建任务执行选项卡。"""
        # 任务输入区域
        task_frame = ttk.LabelFrame(self.task_tab, text="任务输入", padding="10")
        task_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(task_frame, text="任务描述:").pack(anchor=tk.W)
        self.task_text = scrolledtext.ScrolledText(task_frame, height=5, wrap=tk.WORD, font=('Consolas', 10))
        self.task_text.pack(fill=tk.X, pady=5)

        # 控制按钮
        btn_frame = ttk.Frame(task_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        self.run_btn = ttk.Button(btn_frame, text="▶ 运行任务", command=self._on_run_task)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        test_btn = ttk.Button(btn_frame, text="🧪 本地测试", command=self._on_quick_test)
        test_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止任务", command=self._on_stop_task, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(btn_frame, text="🗑 清空输出", command=self._on_clear_output)
        clear_btn.pack(side=tk.LEFT, padx=5)

        # 输出区域
        output_frame = ttk.LabelFrame(self.task_tab, text="执行输出", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = scrolledtext.ScrolledText(output_frame, height=20, wrap=tk.WORD, state=tk.DISABLED, font=('Consolas', 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签
        self.output_text.tag_config('info', foreground='#4a90d9')
        self.output_text.tag_config('success', foreground='#28a745')
        self.output_text.tag_config('error', foreground='#dc3545')
        self.output_text.tag_config('warning', foreground='#e6a817')

    def _on_install_chromium(self):
        """安装Chromium浏览器。"""
        result = messagebox.askyesno(
            "安装 Chromium",
            "即将安装Chromium浏览器（约200MB）。\n\n此过程可能需要几分钟，请耐心等待。\n是否继续？"
        )
        if not result:
            return

        self.progress.start()
        self.status_label.config(text="正在安装Chromium...")
        self.install_chromium_btn.config(state=tk.DISABLED)

        # 在新线程中安装
        thread = threading.Thread(target=self._install_chromium_thread, daemon=True)
        thread.start()

    def _on_quick_test(self):
        """快速本地测试：访问chiphell第一个帖子。"""
        test_task = "访问 `https://www.chiphell.com/` 并找到首页第一个帖子，读取帖子标题和内容"
        self.task_text.delete('1.0', tk.END)
        self.task_text.insert('1.0', test_task)
        self._on_run_task()

    def _install_chromium_thread(self):
        """在线程中安装Chromium。"""
        try:
            import subprocess
            self._append_output("\n开始安装Chromium浏览器...", 'info')

            result = subprocess.run(
                ['uvx', 'browser-use', 'install'],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                self.chromium_installed = True
                self._append_output("✓ Chromium安装成功！", 'success')
                self.root.after(0, lambda: messagebox.showinfo("成功", "Chromium安装成功！"))
            else:
                self._append_output(f"✗ Chromium安装失败:\n{result.stderr}", 'error')
                self.root.after(0, lambda: messagebox.showerror("错误", f"Chromium安装失败:\n{result.stderr}"))
        except subprocess.TimeoutExpired:
            self._append_output("✗ 安装超时（超过10分钟）", 'error')
            self.root.after(0, lambda: messagebox.showerror("超时", "Chromium安装超时，请检查网络连接"))
        except Exception as e:
            self._append_output(f"✗ 安装异常: {e}", 'error')
            self.root.after(0, lambda: messagebox.showerror("错误", f"安装异常: {e}"))
        finally:
            self.root.after(0, self._on_install_complete)

    def _on_install_complete(self):
        """安装完成后的UI更新。"""
        self.progress.stop()
        self.status_label.config(text="就绪")
        self._update_chromium_status()

    def _on_save_config(self):
        """保存配置。"""
        self.config.update({
            'api_key': self.api_key_var.get().strip(),
            'base_url': self.base_url_var.get().strip(),
            'openai_api_key': self.openai_api_key_var.get().strip(),
            'openai_base_url': self.openai_base_url_var.get().strip(),
            'google_api_key': self.google_api_key_var.get().strip(),
            'google_base_url': self.google_base_url_var.get().strip(),
            'local_api_key': self.local_api_key_var.get().strip(),
            'local_base_url': self.local_base_url_var.get().strip(),
            'model_name': self.model_name_var.get().strip(),
            'max_steps': int(self.max_steps_var.get()),
            'headless': self.headless_var.get(),
            'cdp_url': self.cdp_url_var.get().strip(),
        })

        try:
            self._save_env_config()
            self._append_output("✓ 配置已保存到.env文件", 'success')
            messagebox.showinfo("成功", "配置已保存到.env文件")
        except Exception as e:
            self._append_output(f"✗ 保存配置失败: {e}", 'error')
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _on_run_task(self):
        """运行任务。"""
        task = self.task_text.get('1.0', tk.END).strip()
        if not task:
            messagebox.showwarning("警告", "请输入任务描述")
            return

        if not self.config.get('api_key') and not self.config.get('openai_api_key') and not self.config.get('google_api_key'):
            messagebox.showwarning("警告", "请至少配置一个API Key（Browser-Use、OpenAI或Google）")
            self.notebook.select(0)  # 切换到配置选项卡
            return

        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        self.status_label.config(text="任务运行中...")

        # 在新线程中运行任务
        self.task_thread = threading.Thread(target=self._run_task_async, args=(task,), daemon=True)
        self.task_thread.start()

    def _run_task_async(self, task: str):
        """在后台线程中运行异步任务。"""
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self._append_output(f"\n{'=' * 60}", 'info')
            self._append_output(f"开始任务: {task}", 'info')
            self._append_output(f"模型: {self.config['model_name']}", 'info')
            self._append_output(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'info')
            self._append_output(f"{'=' * 60}\n", 'info')

            # 动态导入以避免启动时加载
            from browser_use import Agent, Browser
            from browser_use.llm import get_llm_by_name

            # 创建LLM实例
            model_name = self.config['model_name']
            llm = get_llm_by_name(model_name)

            # 创建浏览器
            cdp_url = self.cdp_url_var.get().strip()
            
            if cdp_url:
                # 如果指定了 CDP URL，使用远程浏览器
                browser = Browser(
                    headless=self.config['headless'],
                    cdp_url=cdp_url,
                )
                self._append_output(f"使用远程浏览器: {cdp_url}", 'info')
            elif self.browser_detected and self.browser_path:
                # 使用检测到的本地浏览器
                browser = Browser(
                    headless=self.config['headless'],
                    executable_path=self.browser_path,
                    minimum_wait_page_load_time=1.0,
                    wait_for_network_idle_page_load_time=1.0,
                    wait_between_actions=0.5,
                    user_data_dir=None,  # 使用临时配置文件，避免与已运行的Chrome冲突
                    args=[
                        '--no-first-run',
                        '--no-default-browser-check',
                    ],
                )
                self._append_output(f"使用本地浏览器: {self.browser_type}", 'info')
                self._append_output(f"浏览器路径: {self.browser_path}", 'info')
            else:
                # 使用默认配置（让 browser-use 自动查找）
                browser = Browser(
                    headless=self.config['headless'],
                    minimum_wait_page_load_time=1.0,
                    wait_for_network_idle_page_load_time=1.0,
                )
                self._append_output("使用默认浏览器配置", 'info')

            self._append_output("浏览器初始化完成", 'info')

            # 创建agent
            self.agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
            )

            self._append_output("Agent创建完成，开始执行任务...\n", 'info')

            # 运行任务
            result = self.loop.run_until_complete(self.agent.run(max_steps=self.config['max_steps']))

            # 处理结果
            self._append_output(f"\n{'=' * 60}", 'success')
            self._append_output("✓ 任务完成！", 'success')
            self._append_output(f"{'=' * 60}\n", 'success')

            # 显示结果
            if hasattr(result, 'final_result') and result.final_result():
                self._append_output("最终结果:", 'success')
                self._append_output(f"{result.final_result()}\n", 'success')

            if hasattr(result, 'errors') and result.errors():
                errors = [e for e in result.errors() if e]
                if errors:
                    self._append_output("\n执行过程中的错误:", 'warning')
                    for error in errors:
                        self._append_output(f"  - {error}\n", 'warning')

            self._append_output(f"访问的URL数: {len(result.urls())}", 'info')
            self._append_output(f"总步骤数: {result.number_of_steps()}", 'info')
            if hasattr(result, 'total_duration_seconds'):
                self._append_output(f"总耗时: {result.total_duration_seconds():.2f}秒", 'info')

        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}\n{traceback.format_exc()}"
            self._append_output(f"\n{'=' * 60}", 'error')
            self._append_output(error_msg, 'error')
            self._append_output(f"{'=' * 60}\n", 'error')
            self.root.after(0, lambda: messagebox.showerror("错误", f"任务执行失败:\n{str(e)}"))
        finally:
            self.is_running = False
            self.root.after(0, self._on_task_complete)

    def _on_test_connection(self):
        """测试大模型连接。"""
        model_name = self.model_name_var.get().strip()
        if not model_name:
            messagebox.showwarning("警告", "请先选择模型")
            return

        # 先保存当前配置
        self.config.update({
            'api_key': self.api_key_var.get().strip(),
            'base_url': self.base_url_var.get().strip(),
            'openai_api_key': self.openai_api_key_var.get().strip(),
            'openai_base_url': self.openai_base_url_var.get().strip(),
            'google_api_key': self.google_api_key_var.get().strip(),
            'google_base_url': self.google_base_url_var.get().strip(),
            'local_api_key': self.local_api_key_var.get().strip(),
            'local_base_url': self.local_base_url_var.get().strip(),
            'model_name': model_name,
            'max_steps': int(self.max_steps_var.get()),
            'headless': self.headless_var.get(),
            'cdp_url': self.cdp_url_var.get().strip(),
        })
        self._save_env_config()

        # 禁用按钮并显示进度
        self.test_conn_btn.config(state=tk.DISABLED, text="测试中...")
        self.conn_status_label.config(text="正在测试连接...", foreground=self.colors['warning'])

        # 在新线程中测试
        thread = threading.Thread(target=self._test_connection_thread, args=(model_name,), daemon=True)
        thread.start()

    def _test_connection_thread(self, model_name: str):
        """在线程中测试连接。"""
        try:
            self._append_output(f"\n{'=' * 60}", 'info')
            self._append_output(f"测试连接 - 模型: {model_name}", 'info')
            self._append_output(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'info')
            self._append_output(f"{'=' * 60}", 'info')

            # 动态导入
            from browser_use.llm import get_llm_by_name
            from browser_use.llm.base import BaseChatModel

            # 创建LLM实例
            llm = get_llm_by_name(model_name)

            # 显示配置信息
            if hasattr(llm, 'base_url') and llm.base_url:
                self._append_output(f"Base URL: {llm.base_url}", 'info')
            if hasattr(llm, 'model') and llm.model:
                self._append_output(f"Model: {llm.model}", 'info')

            # 测试连接 - 发送一个简单的消息
            self._append_output("\n发送测试请求...", 'info')

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 调用LLM
            from browser_use.llm.messages import UserMessage
            messages = [
                UserMessage(content='Say "Connection successful" in one sentence.')
            ]

            response = loop.run_until_complete(
                llm.ainvoke(
                    messages=messages
                )
            )

            # 检查响应
            if response:
                content = response.completion if hasattr(response, 'completion') else str(response)
                self._append_output(f"\n✓ 连接成功！", 'success')
                self._append_output(f"响应: {content}", 'success')

                self.root.after(0, lambda: self.conn_status_label.config(
                    text=f"✓ {model_name} 连接成功",
                    foreground=self.colors['success']
                ))
                self.root.after(0, lambda: messagebox.showinfo("成功", f"模型 {model_name} 连接测试成功！"))
            else:
                self._append_output(f"\n✗ 连接失败: 无效的响应", 'error')
                self.root.after(0, lambda: self.conn_status_label.config(
                    text=f"✗ {model_name} 连接失败",
                    foreground=self.colors['error']
                ))
                self.root.after(0, lambda: messagebox.showerror("错误", "连接测试失败：响应无效"))

        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            self._append_output(f"\n✗ {error_msg}", 'error')
            self._append_output(f"详细错误:\n{traceback.format_exc()}", 'error')
            self._append_output(f"{'=' * 60}\n", 'error')

            error_display = str(e)[:200]
            self.root.after(0, lambda: self.conn_status_label.config(
                text=f"✗ 连接失败: {error_display[:50]}...",
                foreground=self.colors['error']
            ))
            self.root.after(0, lambda: messagebox.showerror("连接失败", f"{error_msg}\n\n详细错误请查看输出窗口"))
        finally:
            self.root.after(0, self._on_test_complete)

    def _on_test_complete(self):
        """测试完成后的UI更新。"""
        self.test_conn_btn.config(state=tk.NORMAL, text="🔗 测试连接")

    def _on_stop_task(self):
        """停止任务。"""
        if self.agent and self.is_running:
            try:
                # 设置agent停止标志
                if hasattr(self.agent, 'stop'):
                    self.agent.stop()
                self._append_output("\n⚠ 任务已请求停止...", 'warning')
            except Exception as e:
                self._append_output(f"停止任务时出错: {e}", 'error')

    def _on_task_complete(self):
        """任务完成后的UI更新。"""
        self.is_running = False
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.status_label.config(text="就绪")

    def _on_clear_output(self):
        """清空输出。"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _append_output(self, text: str, tag: str = 'info'):
        """追加输出到文本框。"""
        def _append():
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, text, tag)
            self.output_text.insert(tk.END, "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.output_text.update()

        self.root.after(0, _append)

    def run(self):
        """运行GUI应用。"""
        self.root.mainloop()


def main():
    """主入口函数。"""
    app = BrowserUseGUI()
    app.run()


if __name__ == '__main__':
    main()
