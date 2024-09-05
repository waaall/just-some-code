"""
    需要注意的几点: 
        1. 「设置项变量名称」要唯一, 
        2. 参数path[-1]的名字要与对应接收类的参数名一致
        3. 参数path[-2]的名字要与对应接收类的类名一致
        4. 增加设置**需要在 settings.json 和 AppSettings类中增加 **_Settingmap
"""
import os, json
from PySide6.QtCore import QObject, Signal
##=========================================================
##=======               软件设置参数类              =========
##=========================================================
class AppSettings(QObject):
    changed_signal = Signal(str, str, object)
    def __init__(self):
        super().__init__()
        """
            定义「设置项变量名称」到设置路径的映射, 附加选项在value第一项(如果有)
            **_Settingmap 命名要与json key 和 value的path[0]一致
        """
        self.General_Settingmap = {
            "language":         (["English", "French", "Spanish"], "General", "language"),
            "autosave":         ("General", "autosave")
        }
        self.Network_Settingmap = {
            "serial_baud_rate": ([800, 1200, 2400, 4800, 9600, 14400, 19200, 38400], "Network", "Serial", "baud_rate"),
            "serial_data_bits": ([4, 8], "Network", "Serial", "data_bits"),
            "serial_stop_bits": ([1, 2, 4], "Network", "Serial", "stop_bits"),
            "serial_parity":    (["None", "Even", "Odd"], "Network", "Serial", "parity"),
            "use_proxy":        ("Network", "Internet", "use_proxy"),
            "proxy_address":    ("Network", "Internet", "proxy_address"),
            "proxy_port":       ("Network", "Internet", "proxy_port")
        }
        self.Display_Settingmap = {
            "resolution":       (["1920x1080", "1280x720", "800x600"], "Display", "Apparence", "resolution"),
            "fullscreen":       ("Display", "Apparence", "fullscreen"),
            "theme":            (["Light", "Dark"], "Display", "Apparence", "theme"),
            "motion_on":        ("Display", "Motion", "motion_on")
        }
        self.Batch_Files_Settingmap = {
            "dicom_log_folder_name": ("Batch_Files", "DicomToImage", "log_folder_name"),
            "dicom_fps":        ([10, 20, 30], "Batch_Files", "DicomToImage", "fps"),
            "dicom_frame_dpi":  ([100, 200, 400, 800], "Batch_Files", "DicomToImage", "frame_dpi"),
            "dicom_out_dir_suffix": ("Batch_Files", "DicomToImage", "out_dir_suffix"),
            "mergecolor_log_folder_name": ("Batch_Files", "MergeColors", "log_folder_name"),
            "mergecolor_out_dir_suffix": ("Batch_Files", "MergeColors", "out_dir_suffix"),
        }
        # 加载设置到成员变量
        self._load_settings()

    # 加载设置到成员变量
    def _load_settings(self):
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 构建 settings.json 的完整路径, 并打开文件加载json数据
        self.settings_file = os.path.join(base_dir, 'configs', 'settings.json')
        with open(self.settings_file, 'r') as file:
            self.__settings_json = json.load(file)
        
        # 提取第一级键作为main_categories
        self.__main_categories = list(self.__settings_json.keys())

        # 将设置的json数据加载到具体的变量中
        for category in self.__main_categories:
            setting_map = self.get_setting_map(category)
            for name, options_path in setting_map.items():
                _, path = self.extract_options_path(options_path)
                value = self.get_value_from_path(path)
                setattr(self, name, value)
    
    # 根据 category_name 动态获取对应的 Settingmap
    def get_setting_map(self, category_name):
        setting_map_name = f"{category_name}_Settingmap"
        return getattr(self, setting_map_name, {})

    # 从 options_path 中提取 path 和 options
    def extract_options_path(self, options_path):
        if isinstance(options_path[0], list):
            options = options_path[0]
            path = options_path[1:]
        else:
            options = None
            path = options_path
        return options, path

    def get_main_categories(self):       
        return self.__main_categories

    def get_value_from_path(self, path):
        d = self.__settings_json
        for key in path:
            d = d.get(key, {})
        return d

    # 保存设置到文件
    def save_settings(self, name, value):
        # 遍历几个setting_map找到name,解析出path就break
        for category in self.__main_categories:
            setting_map = self.get_setting_map(category)
            options_path = setting_map.get(name)
            if options_path:
                _, path = self.extract_options_path(options_path)
                break
        if path:
            d = self.__settings_json
            for key in path[:-1]:
                d = d.get(key, {})
            d[path[-1]] = value
            print(f"From AppSettings:\n\tUpdating setting: {path} = {value}\n")
        else:
            print(f"From AppSettings:\n\tSetting '{name}' not found\n")
            return False
        
        # 发送信号(类名,参数名和值), 通知设置修改
        self.changed_signal.emit(path[-2], path[-1], value)
        try:
            with open(self.settings_file, 'w') as file:
                json.dump(self.__settings_json, file, indent=4)
                return True
        except:
            print(f"From AppSettings:\n\tError to save {name}-{value}\n")
            return False

