import time
from threading import Thread
from serial import Serial
from serial.tools import list_ports
from serial.serialutil import SerialException

class Communication(object):
    """串口通信类

    Args:
        `baudrate (int)`: 串口通信波特率
        `timeout (float)`: 串口连接超时时间
        `writemode (bool)`: 串口写模式

    Example:
        ```python
        if __name__ == "__main__":
            com = Communication()
            com.start_Communication(9600, 0.1 , True)
    ```
    """

    def __init__(self, baudrate: int, timeout: float, writemode: bool):
        # 初始化串口和设备列表
        self.__devices = []   # find_comports 找到的设备列表
        self.__device = None  # select_comport 选择的设备
        self.serial = Serial(baudrate=baudrate, timeout=timeout)  # 初始化串口
        self.writemode = writemode  # 是否启用写模式

    def find_comports(self) -> list:
        """查找串口设备，并保存到 `self.devices` 中

        Returns:
            `list`: 设备列表
        """
        ports = list_ports.comports()  # 查找当前连接的所有串口设备
        devices = [info for info in ports]  # 提取设备信息
        self.__devices = devices
        return devices

    def select_comport(self, *, devices=[]) -> bool:
        """从设备列表中选择一个设备

        Args (option):
            `devices`: 设备列表

        Returns:
            `bool`: 成功保存选中的设备则返回True
        """
        if devices == []:
            _devices = self.__devices
            _num_devices = len(self.__devices)
        else:
            _devices = devices
            _num_devices = len(devices)

        if _num_devices == 0:    # 没有设备
            print("未找到设备")
            return False
        elif _num_devices == 1:  # 只有一个设备
            print("仅找到设备: %s" % _devices[0])
            self.__device = _devices[0].device
            return True
        else:                    # 多个设备
            print("已连接的串口设备如下:")
            for i in range(_num_devices):
                print("%d : %s" % (i, _devices[i]))

            _inp_num = input("输入目标端口号 >> ")

            if not _inp_num.isdecimal():  # 检查输入是否为数字
                print("%s 不是一个数字!" % _inp_num)
                return False
            elif int(_inp_num) in range(_num_devices):  # 检查输入是否在设备范围内
                self.__device = _devices[int(_inp_num)].device
                return True
            else:
                print("%s 超出了设备号范围!" % _inp_num)
                return False

    def register_comport(self, *, device=None) -> bool:
        """将设备保存到 `self.serial.port`

        Args (option):
            `device`: 串口设备名称

        Returns:
            `bool`: 成功注册设备则返回True
        """
        if device is None:
            _device = self.__device
        else:
            _device = device

        # 检查设备是否已指定
        if _device is None:
            print("设备尚未指定!")
            return False
        else:
            self.serial.port = _device
            return True

    def open_comport(self, *, device=None) -> bool:
        """打开串口设备

        Args (option):
            `device`: 串口设备名称

        Returns:
            `bool`: 成功打开设备则返回True
        """
        if device is None:
            _b_reg = self.register_comport()
        else:
            _b_reg = self.register_comport(device=device)
        if not _b_reg:
            return False

        _inp_yn = input("打开 %s 吗? [Yes/No] >> " % self.serial.port).lower()  # 确认是否打开
        if _inp_yn in ["y", "yes"]:
            print("正在打开...")
            try:
                self.serial.open()  # 打开串口
            except SerialException:
                print("%s 在输入时已断开连接" % self.serial.port)
                return False
            else:
                return True
        elif _inp_yn in ["n", "no"]:
            print("操作取消")
            return False
        else:
            print("请输入 [Yes/No]，请再试一次.")
            return False

    def close_comport(self) -> bool:
        """关闭串口设备

        Returns:
            `bool`: 成功关闭设备则返回True
        """
        try:
            self.serial.close()
        except AttributeError:
            print("open_comport 尚未被调用!")
            return False
        else:
            print("正在关闭...")
            return True

    def serial_write(self):
        """写数据到串口设备"""
        _format = "%Y/%m/%d %H:%M:%S"

        while self.serial.is_open:
            _t1 = time.strftime(_format, time.localtime())  # 获取当前时间
            try:
                _send_data = input(_t1 + " (TX) >> ")  # 从用户输入获取数据
                self.serial.write(_send_data.encode("utf-8"))  # 写入串口
            except EOFError:
                print("发送文本已取消.")
                self.close_comport()
            except SerialException:
                print("%s 写入时已断开连接" % self.serial.port)
                self.close_comport()
            else:
                time.sleep(1)

    def start_serialwrite(self):
        """在新线程中启动写串口"""
        self.th_swrite = Thread(target=self.serial_write)
        self.th_swrite.start()

    def serial_read(self):
        """从串口设备读取数据"""
        _format = "%Y/%m/%d %H:%M:%S"

        while self.serial.is_open:
            try:
                _recv_data = self.serial.readline()  # 从串口读取一行数据
            except SerialException:
                print("%s 读取时已断开连接" % self.serial.port)
                self.close_comport()
            else:
                if _recv_data != b'':  # 检查数据是否为空
                    _t1 = time.strftime(_format, time.localtime())
                    print(_t1 + " (RX) : " + _recv_data.strip().decode("utf-8"))  # 输出接收的数据
                    time.sleep(1)

    def start_Communication(self) -> bool:
        """启动串口通信"""
        self.find_comports()
        if not self.select_comport():
            print("设备尚未指定!")
            return False
        if not self.open_comport():
            print("无法打开串口设备，请再试一次.")
            return False
        if self.writemode:
            self.start_serialwrite()

        try:
            self.serial_read()
        except KeyboardInterrupt:
            self.close_comport()

        if self.writemode:
            print("请按 Enter 键终止.")
            self.th_swrite.join()

        print("串口已关闭，欢迎下次使用.")
        return True

    def get_found_devices(self) -> list:
        """返回已找到的设备"""
        return self.__devices

    def get_selected_device(self):
        """返回已选择的设备"""
        return self.__device

    def get_write_available(self) -> bool:
        """返回写模式状态"""
        return self.writemode

if __name__ == "__main__":
    com = Communication(baudrate=9600, timeout=0.1, writemode=True)
    com.start_Communication()