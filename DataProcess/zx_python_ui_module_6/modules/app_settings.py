##=========================用到的库==========================
import os
import json

##=========================================================
##=======               软件设置参数类              =========
##=========================================================
class AppSettings:
    def __init__(self):
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 构建 settings.json 的完整路径
        self.settings_file = os.path.join(base_dir, 'configs', 'settings.json')

        with open(self.settings_file, 'r') as file:
            self._settings = json.load(file)

        # 加载设置到成员变量
        self.language = self._settings["General"]["language"]
        self._theme = self._settings["General"]["theme"]  # 只读属性
        self.autosave = self._settings["General"]["autosave"]

        self.use_proxy = self._settings["Network"]["use_proxy"]
        self.proxy_address = self._settings["Network"]["proxy_address"]
        self.proxy_port = self._settings["Network"]["proxy_port"]

        self.resolution = self._settings["Display"]["resolution"]
        self.fullscreen = self._settings["Display"]["fullscreen"]

    @property
    def theme(self):
        return self._theme

    def save_settings(self):
        # 更新内部的 settings 数据
        self._settings["General"]["language"] = self.language
        self._settings["General"]["theme"] = self.theme
        self._settings["General"]["autosave"] = self.autosave

        self._settings["Network"]["use_proxy"] = self.use_proxy
        self._settings["Network"]["proxy_address"] = self.proxy_address
        self._settings["Network"]["proxy_port"] = self.proxy_port

        self._settings["Display"]["resolution"] = self.resolution
        self._settings["Display"]["fullscreen"] = self.fullscreen

        # 保存设置到文件
        with open(self.settings_file, 'w') as file:
            json.dump(self._settings, file, indent=4)