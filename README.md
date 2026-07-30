# just-some-code

日常工具、小型应用、环境配置和学习代码的集合。

## 目录约定

| 目录 | 内容 |
| --- | --- |
| `apps/` | 有界面、服务端入口或完整项目结构的应用 |
| `tools/` | 解决单一问题、可以直接运行的工具 |
| `system_setup/` | Docker、系统配置、诊断和环境初始化内容 |
| `learning/` | 学习记录、示例代码和个人练习项目 |
| `old_versions/` | 少量必须保留在当前工作区的历史实现 |

一般情况下，旧版本通过 Git 提交和 tag 保存，不再使用 `beta1.py`、`backup.py`
之类的文件副本。

## 应用

- `apps/countdown_appraisal/`：项目考核倒计时桌面应用。
- `apps/fault_tree/`：故障树分析服务。
- `apps/zx_python_ui/`：图像和文件处理桌面工具。

## 工具

- `tools/data/`：校准、测量对比、周期幅值、销售数据汇总和 CSV 处理。
- `tools/files/`：批量重命名、编码修复和 macOS 元数据清理。
- `tools/media/`：视频、图像、字幕和 bitmap 处理。
- `tools/documents/`：Markdown 文档导出。
- `tools/hardware/`：串口通信。
- `tools/development/`：Python 包和 Hugging Face 辅助脚本。

## 使用原则

- 单文件工具直接放在所属类别下；带配置、文档或多个模块的工具使用独立目录。
- 输入样例放入 `examples/`，运行结果放入 `output/`。
- `output/`、`backup/`、缓存和日志不提交到 Git。
- 每个相对完整的工具在自己的目录中维护 README 和依赖说明。
