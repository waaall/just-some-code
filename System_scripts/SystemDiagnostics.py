#!/usr/bin/env python3
import os
import subprocess
import time
import logging
from datetime import datetime
import psutil
import docker
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SystemDiagnostics:
    def __init__(self, output_dir="diagnostics_output"):
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.docker_client = docker.from_env()
        os.makedirs(self.output_dir, exist_ok=True)

    def run_command(self, cmd):
        """执行系统命令并返回输出"""
        try:
            result = subprocess.run(cmd, shell=True, check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"命令执行失败: {cmd}\n错误: {e.stderr}")
            return None

    def collect_system_info(self):
        """收集基础系统信息"""
        logger.info("收集系统信息...")
        info = {
            "timestamp": self.timestamp,
            "uptime": self.run_command("uptime"),
            "cpu_info": self.run_command("lscpu"),
            "memory_info": self.run_command("free -h"),
            "disk_info": self.run_command("df -h"),
            "kernel_info": self.run_command("uname -a"),
        }

        # 保存到文件
        with open(f"{self.output_dir}/system_info_{self.timestamp}.txt", "w") as f:
            for key, value in info.items():
                f.write(f"=== {key.upper()} ===\n{value}\n\n")

        return info

    def collect_process_info(self):
        """收集进程信息，特别关注Java和Python进程"""
        logger.info("收集进程信息...")

        # 使用psutil获取详细进程信息
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                if "java" in proc.info['name'].lower() or "python" in proc.info['name'].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # 保存为DataFrame便于分析
        df = pd.DataFrame(processes)
        if not df.empty:
            df.to_csv(f"{self.output_dir}/processes_{self.timestamp}.csv", index=False)

        return df

    def collect_docker_info(self):
        """收集Docker容器信息"""
        logger.info("收集Docker信息...")
        try:
            containers = self.docker_client.containers.list(all=True)
            docker_info = []

            for container in containers:
                docker_info.append({
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "",
                    "labels": container.labels,
                })

                # 获取容器日志
                try:
                    logs = container.logs(tail=1000).decode('utf-8')
                    with open(f"{self.output_dir}/docker_{container.name}_logs_{self.timestamp}.txt", "w") as f:
                        f.write(logs)
                except Exception as e:
                    logger.error(f"无法获取容器 {container.name} 的日志: {str(e)}")

            # 保存Docker容器基本信息
            pd.DataFrame(docker_info).to_csv(f"{self.output_dir}/docker_containers_{self.timestamp}.csv", index=False)
            return docker_info
        except Exception as e:
            logger.error(f"获取Docker信息失败: {str(e)}")
            return None

    def collect_performance_metrics(self, duration=60, interval=5):
        """收集性能指标，运行一段时间"""
        logger.info(f"开始收集性能指标，持续 {duration} 秒，间隔 {interval} 秒...")

        metrics = []
        end_time = time.time() + duration

        while time.time() < end_time:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # 内存使用
            mem = psutil.virtual_memory()

            # 磁盘I/O
            disk_io = psutil.disk_io_counters()

            # 网络I/O
            net_io = psutil.net_io_counters()

            # 数据库连接数 (假设是MySQL)
            try:
                db_connections = int(self.run_command("mysqladmin status | awk '{print $4}'"))
            except Exception as e:
                logger.error(f"获取数据库连接数失败: {str(e)}")
                db_connections = 0

            metrics.append({
                "timestamp": timestamp,
                "cpu_percent": cpu_percent,
                "cpu_per_core": cpu_percent_per_core,
                "mem_percent": mem.percent,
                "mem_used": mem.used,
                "mem_available": mem.available,
                "disk_read": disk_io.read_bytes,
                "disk_write": disk_io.write_bytes,
                "net_sent": net_io.bytes_sent,
                "net_recv": net_io.bytes_recv,
                "db_connections": db_connections,
            })

            time.sleep(interval)

        # 保存性能数据
        df = pd.DataFrame(metrics)
        df.to_csv(f"{self.output_dir}/performance_metrics_{self.timestamp}.csv", index=False)

        # 生成简单的图表
        self.generate_performance_plots(df)

        return df

    def generate_performance_plots(self, df):
        """生成性能图表"""
        logger.info("生成性能图表...")

        if df.empty:
            return

        plt.figure(figsize=(15, 10))

        # CPU使用率图表
        plt.subplot(2, 2, 1)
        plt.plot(df['timestamp'], df['cpu_percent'], label='Total CPU %')
        plt.title('CPU Usage')
        plt.xlabel('Time')
        plt.ylabel('Percentage')
        plt.xticks(rotation=45)
        plt.legend()

        # 内存使用图表
        plt.subplot(2, 2, 2)
        plt.plot(df['timestamp'], df['mem_percent'], label='Memory %')
        plt.title('Memory Usage')
        plt.xlabel('Time')
        plt.ylabel('Percentage')
        plt.xticks(rotation=45)
        plt.legend()

        # 数据库连接数图表
        plt.subplot(2, 2, 3)
        plt.plot(df['timestamp'], df['db_connections'], label='DB Connections')
        plt.title('Database Connections')
        plt.xlabel('Time')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.legend()

        # 磁盘I/O图表
        plt.subplot(2, 2, 4)
        plt.plot(df['timestamp'], df['disk_read'], label='Disk Read (bytes)')
        plt.plot(df['timestamp'], df['disk_write'], label='Disk Write (bytes)')
        plt.title('Disk I/O')
        plt.xlabel('Time')
        plt.ylabel('Bytes')
        plt.xticks(rotation=45)
        plt.legend()

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/performance_plots_{self.timestamp}.png")
        plt.close()

    def analyze_java_threads(self):
        """分析Java线程"""
        logger.info("分析Java线程...")

        # 查找Java进程
        java_procs = [p for p in psutil.process_iter(['pid', 'name']) if "java" in p.info['name'].lower()]

        if not java_procs:
            logger.warning("未找到Java进程")
            return

        for proc in java_procs:
            pid = proc.info['pid']

            # 获取线程转储
            try:
                jstack_output = self.run_command(f"jstack {pid}")
                if jstack_output:
                    with open(f"{self.output_dir}/java_threads_pid{pid}_{self.timestamp}.txt", "w") as f:
                        f.write(jstack_output)

                    # 简单分析线程状态
                    thread_states = defaultdict(int)
                    for line in jstack_output.splitlines():
                        if "java.lang.Thread.State:" in line:
                            state = line.split("java.lang.Thread.State:")[1].strip()
                            thread_states[state] += 1

                    if thread_states:
                        pd.DataFrame.from_dict(thread_states, orient='index', columns=['count']).to_csv(
                            f"{self.output_dir}/java_thread_states_pid{pid}_{self.timestamp}.csv")
            except Exception as e:
                logger.error(f"无法获取Java进程 {pid} 的线程转储: {str(e)}")

    def analyze_database(self):
        """分析数据库性能"""
        logger.info("分析数据库性能...")

        # MySQL慢查询分析
        try:
            slow_queries = self.run_command("mysql -e 'SHOW FULL PROCESSLIST;'")
            if slow_queries:
                with open(f"{self.output_dir}/mysql_processlist_{self.timestamp}.txt", "w") as f:
                    f.write(slow_queries)

            # 获取数据库状态变量
            db_status = self.run_command("mysql -e 'SHOW GLOBAL STATUS;'")
            if db_status:
                with open(f"{self.output_dir}/mysql_status_{self.timestamp}.txt", "w") as f:
                    f.write(db_status)

            # 获取数据库配置
            db_vars = self.run_command("mysql -e 'SHOW GLOBAL VARIABLES;'")
            if db_vars:
                with open(f"{self.output_dir}/mysql_variables_{self.timestamp}.txt", "w") as f:
                    f.write(db_vars)
        except Exception as e:
            logger.error(f"数据库分析失败: {str(e)}")

    def run_full_diagnosis(self):
        """运行完整诊断流程"""
        logger.info("开始完整系统诊断...")

        self.collect_system_info()
        self.collect_process_info()
        self.collect_docker_info()
        self.collect_performance_metrics(duration=120, interval=5)
        self.analyze_java_threads()
        self.analyze_database()

        logger.info(f"诊断完成，结果保存在: {os.path.abspath(self.output_dir)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="系统诊断工具")
    parser.add_argument("-o", "--output", help="输出目录", default="diagnostics_output")
    args = parser.parse_args()

    diagnoser = SystemDiagnostics(args.output)
    diagnoser.run_full_diagnosis()
