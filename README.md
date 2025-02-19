# WallpaperMaster 壁纸管理器 

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
## 功能特性 

- 🖥️ **智能分辨率适配**：自动检测主显示器物理分辨率（支持4K/1080p/移动端等）
- 🌐 **多源壁纸下载**：集成今日壁纸/随机历史双数据源（Bing壁纸接口）
- 🔄 **自动刷新机制**：支持30分钟至24小时自动更新周期
- 💾 **智能缓存管理**：LRU缓存策略自动清理旧文件（最大保留100个）
- 🛠️ **可视化界面**：实时预览+分辨率手动覆盖功能
- 🚀 **多线程下载**：支持断点续传与失败自动回退

## 环境配置 

```bash
# 安装依赖
pip install -r requirements.txt
```

> 依赖清单：
>
> - Pillow >=9.3.0 (图像处理)
> - pywin32 >=300 (Windows系统集成)
> - requests >=2.31.0 (网络请求)

## 快速启动

```bash
python wallpaper_app.py
```

## 打包部署 

1. 安装PyInstaller：

```bash
pip install pyinstaller
```

1. 生成可执行文件：

```bash
pyinstaller --noconsole --onefile --icon=icon.ico wallpaper_app.py
```

> 生成文件位于 `dist/` 目录

## 项目结构

```markdown
├── src/
│   ├── wallpaper_app.py    # 主程序入口
│   ├── APIConfigManager.py # 配置管理模块
│   └── DisplayDetector.py  # 显示器检测模块
├── requirements.txt        # 依赖清单
├── wallpaper.spec          # PyInstaller打包配置
└── .wallpaper_cache/       # 自动生成的壁纸缓存
```

## 高级配置

在 `api_config.json` 中可自定义：

```json
{
  "refresh_interval": 3600,    // 刷新间隔(秒)
  "resolution": "auto",        // 分辨率策略
  "sources": {                 // 数据源配置
    "today": {
      "templates": {
        "uhd": "https://bing.img.run/uhd.php",
        "1080p": "https://bing.img.run/1920x1080.php"
      }
    }
  }
}
```

## 贡献指南 

欢迎通过 Issue 提交建议或 PR 贡献代码，请遵循：

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起 Pull Request

## 许可证

MIT License © 2025 [lqb]

## 感谢

特别感谢 [关于 - Bing每日壁纸档案库](https://bing.img.run/about.html) 提供的壁纸 API ！！！