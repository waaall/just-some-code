#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <chrono>
#include <thread>
#include <iomanip>
#include <ctime>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <dirent.h>

#ifdef __linux__
    #include <sys/sysinfo.h>
#elif __APPLE__
    #include <sys/types.h>
    #include <sys/sysctl.h>
    #include <mach/mach.h>
    #include <mach/vm_statistics.h>
    #include <mach/mach_types.h>
    #include <mach/mach_init.h>
    #include <mach/mach_host.h>
#endif

class SystemMonitor {
private:
    // 获取当前时间
    std::string getCurrentTime() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
        return ss.str();
    }

    // 获取CPU使用率（直接读取/proc/stat，不依赖procps）
    double getCPUUsage() {
#ifdef __linux__
        static unsigned long long lastTotalUser = 0, lastTotalUserLow = 0, lastTotalSys = 0, lastTotalIdle = 0;
        
        std::ifstream file("/proc/stat");
        if (!file.is_open()) {
            return 0.0;
        }
        
        std::string line;
        std::getline(file, line);
        
        std::stringstream ss(line);
        std::string cpu;
        unsigned long long totalUser, totalUserLow, totalSys, totalIdle, total;
        
        ss >> cpu >> totalUser >> totalUserLow >> totalSys >> totalIdle;
        file.close();
        
        if (lastTotalUser == 0) {
            lastTotalUser = totalUser;
            lastTotalUserLow = totalUserLow;
            lastTotalSys = totalSys;
            lastTotalIdle = totalIdle;
            return 0.0;
        }
        
        total = (totalUser - lastTotalUser) + (totalUserLow - lastTotalUserLow) + (totalSys - lastTotalSys);
        double percent = total;
        total += (totalIdle - lastTotalIdle);
        percent /= total;
        percent *= 100;
        
        lastTotalUser = totalUser;
        lastTotalUserLow = totalUserLow;
        lastTotalSys = totalSys;
        lastTotalIdle = totalIdle;
        
        return percent;
#else
        // 对于非Linux系统，返回一个模拟值
        static int counter = 0;
        counter++;
        return 10.0 + (counter % 20); // 模拟10-30%的CPU使用率
#endif
    }

    // 获取内存使用情况（直接读取/proc/meminfo，不依赖procps）
    void getMemoryUsage(double& usedPercent, long& totalMem, long& freeMem) {
#ifdef __linux__
        std::ifstream meminfo("/proc/meminfo");
        if (!meminfo.is_open()) {
            totalMem = 8192; // 默认8GB
            freeMem = 4096;  // 默认4GB可用
            usedPercent = 50.0;
            return;
        }
        
        std::string line;
        long memTotal = 0, memFree = 0, memAvailable = 0;
        
        while (std::getline(meminfo, line)) {
            std::stringstream ss(line);
            std::string key;
            long value;
            
            ss >> key >> value;
            
            if (key == "MemTotal:") {
                memTotal = value;
            } else if (key == "MemFree:") {
                memFree = value;
            } else if (key == "MemAvailable:") {
                memAvailable = value;
            }
        }
        meminfo.close();
        
        totalMem = memTotal / 1024; // 转换为MB
        freeMem = (memAvailable > 0 ? memAvailable : memFree) / 1024; // 使用MemAvailable更准确
        long usedMem = totalMem - freeMem;
        usedPercent = (double)usedMem / totalMem * 100.0;
        
#elif __APPLE__
        // macOS实现
        int mib[2];
        int64_t physical_memory;
        size_t length;

        // 获取物理内存总量
        mib[0] = CTL_HW;
        mib[1] = HW_MEMSIZE;
        length = sizeof(int64_t);
        sysctl(mib, 2, &physical_memory, &length, NULL, 0);
        
        totalMem = physical_memory / (1024 * 1024); // MB

        // 获取可用内存
        vm_size_t page_size;
        vm_statistics64_data_t vm_stat;
        mach_msg_type_number_t host_size = sizeof(vm_statistics64_data_t) / sizeof(natural_t);
        
        host_page_size(mach_host_self(), &page_size);
        host_statistics64(mach_host_self(), HOST_VM_INFO64, (host_info64_t)&vm_stat, &host_size);
        
        freeMem = (vm_stat.free_count + vm_stat.inactive_count) * page_size / (1024 * 1024);
        long usedMem = totalMem - freeMem;
        usedPercent = (double)usedMem / totalMem * 100.0;
#else
        // 默认实现
        totalMem = 8192; // 默认8GB
        freeMem = 4096;  // 默认4GB可用
        usedPercent = 50.0;
#endif
    }

    // 检查端口占用情况（使用socket API，不依赖net-tools）
    bool isPortInUse(int port) {
        try {
            int sockfd = socket(AF_INET, SOCK_STREAM, 0);
            if (sockfd < 0) {
                return false;
            }
            
            // 设置socket选项以允许地址重用
            int opt = 1;
            setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
            
            struct sockaddr_in addr;
            addr.sin_family = AF_INET;
            addr.sin_port = htons(port);
            addr.sin_addr.s_addr = INADDR_ANY;
            
            int result = bind(sockfd, (struct sockaddr*)&addr, sizeof(addr));
            close(sockfd);
            
            return result != 0; // 如果bind失败，说明端口被占用
        } catch (const std::exception& e) {
            return false; // 出现异常时假设端口可用
        }
    }

    // 获取占用指定端口的进程信息（直接读取/proc/net/tcp，不依赖net-tools）
    std::string getPortProcessInfo(int port) {
#ifdef __linux__
        try {
            // 直接读取/proc/net/tcp文件
            std::ifstream tcp_file("/proc/net/tcp");
            if (!tcp_file.is_open()) {
                return "无法读取端口信息 (容器环境限制)";
            }
            
            std::string line;
            std::getline(tcp_file, line); // 跳过标题行
            
            // 将端口转换为16进制格式
            std::stringstream port_hex;
            port_hex << std::hex << std::uppercase << port;
            std::string target_port = ":" + port_hex.str();
            
            while (std::getline(tcp_file, line)) {
                if (line.find(target_port) != std::string::npos) {
                    // 找到对应端口，可以进一步解析inode来找进程
                    tcp_file.close();
                    return "端口被占用 (详细信息需进一步解析)";
                }
            }
            tcp_file.close();
            return "端口空闲";
        } catch (const std::exception& e) {
            return "端口信息读取异常: " + std::string(e.what());
        }
#else
        return isPortInUse(port) ? "端口被占用" : "端口空闲";
#endif
    }

    // 清屏
    void clearScreen() {
        std::cout << "\033[2J\033[H";
    }

public:
    void displaySystemInfo() {
        clearScreen();
        
        std::cout << "==================== 系统监控信息 ====================" << std::endl;
        std::cout << std::endl;
        
        // 显示当前时间
        std::cout << "当前时间: " << getCurrentTime() << std::endl;
        std::cout << std::endl;
        
        // 显示CPU使用率
        double cpuUsage = getCPUUsage();
        std::cout << "CPU使用率: " << std::fixed << std::setprecision(2) 
                  << cpuUsage << "%" << std::endl;
        
        // 显示内存使用情况
        double memUsedPercent;
        long totalMem, freeMem;
        getMemoryUsage(memUsedPercent, totalMem, freeMem);
        
        std::cout << "内存使用情况:" << std::endl;
        std::cout << "   总内存: " << totalMem << " MB" << std::endl;
        std::cout << "   空闲内存: " << freeMem << " MB" << std::endl;
        std::cout << "   已使用: " << std::fixed << std::setprecision(2) 
                  << memUsedPercent << "%" << std::endl;
        std::cout << std::endl;
        
        // 检查7897端口占用情况
        int targetPort = 7897;
        bool portInUse = isPortInUse(targetPort);
        std::cout << "端口 " << targetPort << " 状态: ";
        
        if (portInUse) {
            std::cout << "被占用" << std::endl;
            std::string processInfo = getPortProcessInfo(targetPort);
            std::cout << "   详情: " << processInfo << std::endl;
        } else {
            std::cout << "空闲" << std::endl;
        }
        
        std::cout << std::endl;
        std::cout << "=================================================" << std::endl;
        std::cout << "按 Ctrl+C 退出程序" << std::endl;
        std::cout << "下次刷新: 1秒后..." << std::endl;
    }

    void run() {
        std::cout << "启动系统监控程序" << std::endl;
        std::this_thread::sleep_for(std::chrono::seconds(1));
        
        while (true) {
            displaySystemInfo();
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }
};

int main() {
    SystemMonitor monitor;
    monitor.run();
    return 0;
}
