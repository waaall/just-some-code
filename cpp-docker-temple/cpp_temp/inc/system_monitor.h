#ifndef SYSTEM_MONITOR_H
#define SYSTEM_MONITOR_H

#include <string>

/**
 * @brief 系统监控类
 * 
 * 提供系统信息监控功能，包括：
 * - CPU使用率监控
 * - 内存使用情况
 * - 端口占用检查
 * - 系统时间显示
 */
class SystemMonitor {
private:
    // 获取当前时间
    std::string getCurrentTime();
    
    // 获取CPU使用率
    double getCPUUsage();
    
    // 获取内存使用情况
    void getMemoryUsage(double& usedPercent, long& totalMem, long& freeMem);
    
    // 检查端口占用情况
    bool isPortInUse(int port);
    
    // 获取占用指定端口的进程信息
    std::string getPortProcessInfo(int port);
    
    // 清屏
    void clearScreen();

public:
    /**
     * @brief 显示系统信息
     */
    void displaySystemInfo();
    
    /**
     * @brief 运行监控循环
     */
    void run();
};

#endif // SYSTEM_MONITOR_H
