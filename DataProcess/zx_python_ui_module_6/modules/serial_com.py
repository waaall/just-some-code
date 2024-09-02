import sys
import time
import threading

import serial
from PySide6.QtCore import QObject, Signal,QTimer

class SerialReader(QObject):
    data_signal = Signal(str)
    def __init__(self, port='COM3', baudrate=9600, interval=0.5, callback=None):
        super().__init__()
        self.port = port
        self.interval = interval
        self.callback = callback   # 用于处理数据的回调函数
        self.running = True

        self.ser = serial.Serial(self.port, baudrate, timeout=1)

    def start(self):
        """启动串口读取线程"""
        self.thread = threading.Thread(target=self.read_serial_data)
        self.thread.start()

    def read_serial_data(self):
        """后台线程方法，用于定时读取串口数据并通过回调函数发送"""
        while self.running:
            if self.ser.in_waiting > 0:
                data = self.ser.readline().decode('utf-8').strip()
                if data:
                    try:
                        value = float(data)
                        if self.callback:
                            self.callback(value)  # 通过回调函数发送数据
                    except ValueError:
                        pass  # 忽略非数字数据
            time.sleep(self.interval)  # 等待下一次读取

    def stop(self):
        """停止串口读取线程"""
        self.running = False
        self.thread.join()
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.start(100)  # 每100ms读取一次数据

if __name__ == "__main__":
    def print_data(value):
        print(f"Received data: {value}")

    # 示例使用：在终端打印串口数据
    serial_reader = SerialReader(port='COM3', baudrate=9600, interval=0.5, callback=print_data)
    serial_reader.start()

    try:
        while True:
            time.sleep(1)  # 保持主线程运行
    except KeyboardInterrupt:
        serial_reader.stop()
        print("Serial reader stopped.")