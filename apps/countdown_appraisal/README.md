# 项目考核倒计时

使用 Excel 保存考核任务，并在桌面界面中显示倒计时和到期提醒。

## 运行

```bash
python main.py
```

主要依赖：`PySide6`、`pandas`、`openpyxl`。桌面通知依赖随操作系统而异。

## 目录

- `main.py`：应用入口。
- `data/`：当前业务数据；自动备份不会提交到 Git。
- `resources/`：图标和本地设置。
- `docs/`：打包说明。
