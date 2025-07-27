# README

我并非该项目源代码作者，后通过阅读源码分析原理和技术细节。

# 基本结构

## 核心数据处理文件

### 数据库连接类

* **dbConnectMySql.cs** - MySQL数据库连接
* **dbConnectInfluxdb.cs** - InfluxDB时序数据库连接
* **dbConnectPI.cs** - PI工业历史数据库连接
* **dbConnectExcel.cs** - Excel文件操作

### 主处理模块

* **dbOperater.cs** - 核心数据操作逻辑
* **ExtractDataFromHis.cs** - 历史数据提取（主要在Form1.cs）
* **myTimer.cs** - 定时任务调度

### 配置模块

* **Form1.cs** - 主控制界面
* **InfluxSet.cs** - InfluxDB配置
* **AddDatabase.cs** - 数据库管理

## 核心处理流程

### 1. 多数据源管理

**-** PI工业历史数据库
**-** MySQL关系数据库
**-** InfluxDB时序数据库
**-** Excel电子表格

### 2. 定时处理机制

myTimer.cs实现：

* 定时数据采集
* 自动同步任务
* 后台任务协调

### 3. 数据处理

dbOperater.cs包含：

* 数据校验转换
* 跨库数据映射
* 批量处理
* 错误恢复

### 4. 多线程

项目特点：

* 多线程并发处理
* 生产者-消费者模式
* 多源并行处理

## 关键功能

1. **工业数据采集** - 从PI系统提取时序数据
2. **数据库迁移** - 跨数据库系统转移数据
3. **实时处理** - 定时自动同步
4. **配置管理** - 可视化参数设置
5. **Excel集成** - 表格数据导入导出

从工业系统(PI)到现代时序数据库(InfluxDB)的数据迁移，同时通过MySQL管理元数据。

# 细节

基于 readPointsInThread.cs 的分析：索引快速定位和差值存储。

## 1. 数据具体操作流程

### 核心处理逻辑：

````csharp
// 数据处理的主要步骤
1. 读取IDX索引文件 → 解析数据点信息和索引
2. 根据索引读取HIS历史数据文件 → 提取时序数据块
3. 解析差值数据 → 还原完整时序数据
4. 写入InfluxDB时序数据库
````

### 详细操作过程：

#### Step 1: IDX文件解析

````csharp
// 解析数据点映射关系
private Dictionary<int, string> getPointCodeAndXh(string sFilename)
{
    // 1. 读取文件到字节数组
    byte[] binarydata = File.ReadAllBytes(sFilename);
  
    // 2. 从偏移22位置读取AxPoint数量（4字节）
    int iAxPointsNum = BitConverter.ToInt32(pointNum, 0);
  
    // 3. 从偏移118位置开始读取每个数据点信息
    iStart = 118;
    for (int i = 0; i < iAxPointsNum; i++)
    {
        // 读取点名（变长字符串，以0x00结束）
        string sPointCode = System.Text.Encoding.Default.GetString(pointCode);
  
        // 读取点序号（偏移+32位置，4字节）
        int nPointXh = BitConverter.ToInt32(pointXh, 0);
  
        // 每个点信息36字节
        iStart = iStart + 36;
    }
}
````

#### Step 2: HIS数据块读取

````csharp
// 按2分钟数据块读取
for (int i = 0; i < 30; i++)   // 30个2分钟块 = 1小时
{
    // 从IDX文件获取数据块在HIS文件中的地址
    blockAddress = BitConverter.ToInt32(address1, 0);
  
    // 读取数据块头部信息
    iArrayCount = hisBinarydata[blockAddress];  // 数组个数
    iOffset = iArrayCount * 9;                  // 数据块大小
  
    // 提取2分钟数据块
    Array.Copy(hisBinarydata, blockAddress + 2, dataBlock1, 0, iOffset);
  
    // 解析数据块
    readBlockData_writeTo_Influx(dataBlock1, iArrayCount, sPointCode, iXh);
}
````

#### Step 3: 差值数据解析

````csharp
// 差值
private void readBlockData_writeTo_Influx(byte[] binaryData, int iArrayCount, string sPointCode, int iXh)
{
    // 1. 读取第一个完整值（4字节浮点数）
    point.fValue = BitConverter.ToSingle(temp, 0);
  
    // 2. 读取差值（4字节浮点数）
    float cha = BitConverter.ToSingle(temp, 0);
  
    // 3. 通过差值计算后续数据点
    for (int j = 1; j < arrayNums[i]; j++)
    {
        chaPoint.fValue = lastValue + cha;  // 累加差值
        lastValue = chaPoint.fValue;
    }
  
    // 4. 写入InfluxDB
    dbconnect.InsertData(chaPoint);
}
````

## 2. HIS和IDX文件格式推理

### IDX文件格式（索引文件）：

````
[文件头部] (117字节)
├── 偏移0-21:   文件标识和其他信息 (22字节)
├── 偏移22-25:  AxPoint数量 (4字节, int32)
├── 偏移26-29:  DxPoint数量 (4字节, int32)
├── 偏移30-117: 其他头部信息 (87字节)

[数据点定义区] (从偏移118开始)
├── 每个AxPoint: 36字节
│   ├── 偏移0-31:  点名 (变长字符串，以0x00结束，最大32字节)
│   ├── 偏移32-35: 点序号 (4字节, int32)
├── 每个DxPoint: 36字节 (格式类似)

[索引区] (数据点定义区之后)
├── 30个时间段索引 (每2分钟一个，共1小时)
├── 每个时间段包含所有点的地址索引
├── 每个地址索引: 4字节 (指向HIS文件中的数据块)
````

### HIS文件格式（历史数据文件）：

````
[数据块1] [数据块2] ... [数据块N]

每个数据块结构 (2分钟数据):
├── 偏移0:     数组个数 (1字节)
├── 偏移1:     保留字节
├── 偏移2开始: 数据
│   ├── 每个数组数据个数 (1字节)
│   ├── 第一个完整值 (4字节浮点数)
│   ├── 差值 (4字节浮点数)
│   └── 通过差值计算后续数据

数据块大小计算: 数组个数 × 9字节
````

### 数据解析：

1. **差值存储**：存储第一个完整值和一个差值
2. **累加还原**：后续值 = 前一个值 + 差值
3. **时间分辨率**：每秒一个数据点，2分钟=120个数据点

### 时间组织结构：

- **文件级别**：每小时一对文件（.his + .idx）
- **块级别**：每2分钟一个数据块
- **点级别**：每秒一个数据点
- **文件命名**：`YYYYMMDDHH.his` 和 `YYYYMMDDHH.idx`

# 错误

## mysql connect issue

```bash

************** 异常文本 **************
MySql.Data.MySqlClient.MySqlException (0x80004005): Unable to connect to any of the specified MySQL hosts.
   在 MySql.Data.MySqlClient.NativeDriver.Open()
   在 MySql.Data.MySqlClient.Driver.Open()
   在 MySql.Data.MySqlClient.Driver.Create(MySqlConnectionStringBuilder settings)
   在 MySql.Data.MySqlClient.MySqlPool.GetPooledConnection()
   在 MySql.Data.MySqlClient.MySqlPool.TryToGetDriver()
   在 MySql.Data.MySqlClient.MySqlPool.GetConnection()
   在 MySql.Data.MySqlClient.MySqlConnection.Open()
   在 ExtractDataFromHis.dbConnectMySql.connect() 位置 c:\Users\rcny\Desktop\duoxiancheng\ExtractDataFromHis\ExtractDataFromHis\ExtractDataFromHis\dbConnectMySql.cs:行号 112
   在 ExtractDataFromHis.Form1.button_ReadIdx_Click(Object sender, EventArgs e) 位置 c:\Users\rcny\Desktop\duoxiancheng\ExtractDataFromHis\ExtractDataFromHis\ExtractDataFromHis\Form1.cs:行号 163
   在 System.Windows.Forms.Control.OnClick(EventArgs e)
   在 System.Windows.Forms.Button.OnMouseUp(MouseEventArgs mevent)
   在 System.Windows.Forms.Control.WmMouseUp(Message& m, MouseButtons button, Int32 clicks)
   在 System.Windows.Forms.Control.WndProc(Message& m)
   在 System.Windows.Forms.ButtonBase.WndProc(Message& m)
   在 System.Windows.Forms.Button.WndProc(Message& m)
   在 System.Windows.Forms.NativeWindow.Callback(IntPtr hWnd, Int32 msg, IntPtr wparam, IntPtr lparam)

```

**解决方案是安装mysql**

### windows 无法启动 mysql

```bash
Target host is configured as Windows, but seems to be a different OS. Please review the connection settings
```

**[解决方案](https://blog.csdn.net/sinat_31994101/article/details/123421433)**：

1. 控制面板 → 时钟和区域 → 区域
2. 管理标签 → 更改系统区域设置
3. 勾选 “Beta版：使用Unicode UTF-8提供全球语言支持(U)”


---

python 重写

---



# IDX文件结构完整分析报告

## 文件概况

通过 `guess_idx_file.py` 成功解析了IDX文件的完整结构，验证了我们之前的推测。

### 基本信息

- **文件**: `2025070222.idx`
- **文件大小**: 4,794,774 字节 (约4.8MB)
- **分析时间**: 2025-07-25 11:34:36
- **输出报告**: `2025070222_idx_analysis.txt`

## IDX文件结构验证

### 1. 文件头部 (118字节) ✅

```
[偏移0-21]   文件标识: "HIS_INDEX_FILE VER2.10" (22字节)
[偏移22-25]  AxPoint数量: 11,241 个 (4字节)
[偏移26-29]  DxPoint数量: 19,494 个 (4字节)  
[偏移30-117] 其他头部信息: 87字节 (大部分为0填充)
```

### 2. 数据点定义区 (从偏移118开始) ✅

```
AxPoint定义区:
├── 11,241个AxPoint × 36字节 = 404,676字节
├── 每个点包含: 点名(变长) + 序号(4字节)
├── 起始偏移: 118
├── 结束偏移: 404,794

DxPoint定义区:  
├── 19,494个DxPoint × 36字节 = 701,784字节
├── 每个点包含: 点名(变长) + 序号(4字节)
├── 起始偏移: 404,794
├── 结束偏移: 1,106,578
```

### 3. 索引区 (1,106,574字节开始) ✅

```
总数据点: 30,735个 (11,241 + 19,494)
时间段: 30个 (每2分钟一段，共1小时)
索引项: 30 × 30,735 × 4字节 = 3,688,200字节
起始偏移: 1,106,574
结束偏移: 4,794,774 (正好等于文件大小)
```

## 数据点类型分析

### AxPoint (模拟量点) - 11,241个

主要包含系统监控和测量数据：

**系统监控类**:

- `SYS_XCU001_Memory` - 系统内存使用率
- `SYS_XCU001_CPULoad` - 系统CPU负载
- `SYS_XCU101_Memory` - 备用系统内存
- ... (各种系统节点的监控数据)

**测量仪表类**:

- `QBB1YZXFXY-AI01` 到 `QBB1YZXFXY-AI15` - 模拟输入信号
- 各种传感器和仪表读数

### DxPoint (数字量点) - 19,494个

主要包含开关量和状态信息：

**系统状态类**:

- `SYS_XCU001_AN_OFF` - 系统A网络离线状态
- `SYS_XCU001_BN_OFF` - 系统B网络离线状态
- ... (各种系统状态信号)

**设备状态类**:

- `20GSPDIS037A` - 设备状态指示
- `20TSILOST220V1` - 电源丢失报警
- `LeakAL` - 泄漏报警
- ... (各种设备状态和报警)

## 索引机制验证

### 时间分段索引

```
时间块0 (0-1分钟):   偏移1,106,574 开始
时间块1 (2-3分钟):   偏移1,229,514 开始  
时间块2 (4-5分钟):   偏移1,352,454 开始
时间块3 (6-7分钟):   偏移1,475,394 开始
时间块4 (8-9分钟):   偏移1,598,334 开始
... 共30个时间块
```

### HIS文件地址映射

每个时间块包含30,735个地址指针，指向HIS文件中对应的数据块：

```
时间块0: HIS地址范围 21 - 1,818,294
时间块1: HIS地址范围 1,818,294 - 3,654,402  
时间块2: HIS地址范围 3,654,402 - 5,475,603
时间块3: HIS地址范围 5,475,603 - 7,271,874
...
```

## 数据组织特点

### 1. 分层存储结构

- **IDX文件**: 存储元数据和索引信息
- **HIS文件**: 存储压缩的实际时序数据

### 2. 时间分段管理

- 每2分钟一个数据块，便于快速定位
- 30个数据块覆盖1小时完整数据

### 3. 高效索引机制

- 直接地址指针，O(1)时间复杂度访问
- 支持30,735个并发数据点的高效查询

### 4. 空间优化

- 使用4字节地址指针而非8字节
- 变长字符串存储点名，节省空间

## 技术价值

这种文件格式设计体现了工控系统对性能的极致追求：

1. **高效访问**: 通过索引实现快速数据定位
2. **大容量**: 支持3万+数据点的并发存储
3. **时间优化**: 按时间分段组织，便于历史查询
4. **压缩存储**: 结合HIS文件的差值压缩算法
5. **可靠性**: 结构化存储，支持数据完整性验证

## 应用场景

这种数据格式典型应用于：

- 大型工业控制系统
- 电力系统SCADA
- 石化过程控制
- 建筑楼宇自控
- 智能制造系统

处理如此大规模的实时数据采集、存储和历史查询需求。

## 文件输出

详细的分析结果已保存到：
`/his-data/2025070222_idx_analysis.txt` (187行完整报告)

包含了每个数据点的详细信息和索引地址映射关系，可用于进一步的数据处理和分析。


# 指定数据导出


**功能描述：**

- 导出指定数据点在整个小时内（30个时间块）的时序数据
- 展示单个测点的时间变化趋势
- 包含该数据点的完整历史轨迹

**输出文件：**

- 格式：`{文件名}_mode2_{数据点名}_timeseries.xlsx`
- 示例：`2025070222_mode2_20MCS-UNITMW_timeseries.xlsx`

**数据内容：**

- TimeStamp：时间戳
- Value：数据值
- Quality：数据质量
- PointCode：数据点代码
- PointName：数据点名称
- XH：序号

**统计信息：**

- 数据点基本信息
- 数值统计（最小值、最大值、平均值、中位数）
- 每2分钟汇总表

**适用场景：**

- 单个测点的趋势分析
- 时序数据分析
- 设备运行状态监控
