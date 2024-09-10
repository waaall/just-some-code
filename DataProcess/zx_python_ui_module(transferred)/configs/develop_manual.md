# 0 前言
可以先阅读user_manual以便快速了解此软件。

## 0.0 我的愿景
我很喜欢开源社区的氛围，尤其是从历史上来看，Unix到Linux，从git到github，我觉得没有计算机能发展之快就是不同于传统领域的开源精神。本项目的所有代码也都是基于开源的python和各种第三方库，所以我希望它能成为一款跨多领域的模块化的批量数据处理软件。

## 0.1 软件设计理念

我为此软件的模块化做了一些力所能及的努力，希望能帮助他在开源社区成长。包括但不限于：
- 每个功能的逻辑代码可以完全独立于UI代码作为脚本使用。
- 每个页面都可以单独运行显示，用于界面的微调。
- 尽可能简化功能界面和逻辑界面的绑定，且集成在main.py
- 实现了添加页面的“原子操作”。
- 实现了添加常用逻辑代码绑定的“原子操作”。


# 1 设计思路

## 1.0 架构

```python
this-project/
│
├── libs/
│
├── configs/
│   ├── develop_manual.md
│   ├── user_manual.md
│   └── settings.json
│
├── modules/
│   ├── __init__.py
│   ├── app_settings.py
│   ├── files_basic.py
│   ├── merge_colors.py
│   ├── split_colors.py
│   ├── dicom_to_imgs.py
│   └── serial_com.py
│
├── widgets/
│   ├── __init__.py
│   ├── dock_widget.py
│   ├── setting_page.py
│   ├── file_page.py
│   ├── help_page.py
│   ├── plotting_page.py
│   └── images_page.py
│
├── main_window.py
├── main.py
├── requirements.txt
└── install.py
```

其中lib是可能依赖的动态库；configs内部为配置文件（显而易见）；modules内为逻辑代码部分；widgets内为UI页面的代码；main_window.py是主窗口的显示和初始化widgets内的页面类；main.py初始化main_window，绑定modules内的逻辑类。

## 1.1 从哪里讲起
一个程序都是从main开始，但是这是执行的开始，而不是设计的开始。我尝试从我设计此软件的思路讲，不知道效果会不会好一些。

## 1.2 批量处理的脚本

