##=========================================================
##=======                 问题描述                 =========
##=========================================================

## 有很多个excel表格，现仅演示一个，表格有两列数据，每列单独处理
## 每列数据是周期波动信号，周期已知，但信号不稳定，要求得每个周期的平均振幅
## 此版本不同之处在于加入了一些机制，比如多文件夹并行处理、残缺周期分情况处理、DC/AC数据分别处理等


##=========================================================
##=======                   常量                   =========
##=========================================================

# import xlrd,openpyxl              #xlrd新版不支持xlsx格式，需要再安装openpyxl
import os
import numpy as np
import pandas as pd
from multiprocessing import Pool
from functools import partial
# import matplotlib.pyplot as plt   #若用python画图则import

DCFolderName = "直流"
WorkFolderList = ['1', '5', '25', '100', '500']
WorkFolderName = "HZ"                  #数据所在文件夹

#数据文件名//注意，所有文件名都不带格式，最后再添加
DCFileList = ['1.8A', '1.6A', '2.0A']
ACFileList = ['30.8', '31.2', '31.5', '50.8', '51.2', '51.5', '70.8', '71.2', '71.5']        
InputFormat = ".xlsx"                                   #数据文件格式
OutSubName = ['first', 'second']                        #两列数据的名字，也作为输出文件的部分名字
OutFormat = '.txt'                                      #最终数据输出文件格式
ECNlist = [250, 100, 20, 20, 20]                        #一个周期数据数量Each Cycle Number


##=========================================================
##=======                   函数                   =========
##=========================================================

# 这是直流部分，无需计算周期相关
def DC():
    WorkFolder = DCFolderName
    for InputFile in DCFileList:
        try:
            InitMatrics = pd.read_excel(f"{WorkFolder}/{InputFile}/{InputFile}{InputFormat}", 
                                engine='openpyxl', header=None, names=OutSubName, usecols=[0,1])
        except:
            InitMatrics = pd.read_excel(f"{WorkFolder}/{InputFile}/{InputFile}{InputFormat.strip('x')}", 
                                header=None, names=OutSubName, usecols=[0,1])
        
        os.makedirs(f"{WorkFolder}/{InputFile}", exist_ok=True)

        #每列数据计算保存一份
        for col in OutSubName:
            findAllAmp(InitMatrics[col].tolist(), f"{WorkFolder}/{InputFile}/{col}_不求平均值")


#==========================对多个文件夹批量输出===========================
def ACAllFolder(FolderIndexList):
    for Index in FolderIndexList:
        ACFolder(Index)


#======================对每个文件夹内多个文件批量输出=======================
def ACFolder(FolderIdx):
    InputList = []
    for x in ACFileList:
        InputList.append(f"{WorkFolderList[FolderIdx]}-0.{x}")

    ##多核
    p = Pool() #p = Pool(processes=4)
    partial_ACFile = partial(ACFile, FolderIndex=FolderIdx)
    p.map(partial_ACFile, InputList)
    p.close()
    p.join()


#================这个是100HZ、500HZ的，电流不全，所以单独弄==================
def specialOne(FolderIdx):
    Perfix = WorkFolderList[FolderIdx]
    List = ['30.8', '31.2', '31.5', '50.8', '51.2', '70.8', '71.2', '71.5']
    InputList = []
    for x in List:
        InputList.append(f"{Perfix}-0.{x}")
    
    ##多核
    p = Pool() #p = Pool(processes=4)
    partial_ACFile = partial(ACFile, FolderIndex=FolderIdx)
    p.map(partial_ACFile, InputList)
    p.close()
    p.join()


#=========================对每个Excel文件操作输出==========================
def ACFile(InputFile, FolderIndex):
    WorkFolder = WorkFolderList[FolderIndex] + WorkFolderName
    # 把数据读入内存，格式是DataFrame，矩阵形式，两列数据分别叫做first、second，
    # 这次数据在更深入文件夹内（不同于第一次），所以删除了创建文件夹那一行指令
    try:
        InitMatrics = pd.read_excel(f"{WorkFolder}/{InputFile}/{InputFile}{InputFormat}", 
                                engine='openpyxl', header=None, names=OutSubName, usecols=[0,1])
    except:
        InitMatrics = pd.read_excel(f"{WorkFolder}/{InputFile}/{InputFile}{InputFormat.strip('x')}", 
                                header=None, names=OutSubName, usecols=[0,1])
    #每列数据计算保存一份
    for col in OutSubName:
        #这列数据转为list，然后调用函数，找出所有幅值（amplitude），并保存
        splitAndFind(InitMatrics[col].tolist(), f"{WorkFolder}/{InputFile}/{col}", FolderIndex)
        findAllAmp(InitMatrics[col].tolist(), f"{WorkFolder}/{InputFile}/{col}_不求平均值")


#============最核心的函数，首先按照周期分割数据，再找到平均Amp并保存============
def splitAndFind(List, OutFile, ECNindex):
    ECN = ECNlist[ECNindex]
    TotalLength = len(List)                             #list总长
    CycleNum = int(TotalLength / ECN + 1)               #总周期数
    ShiftNum = TotalLength - int(TotalLength / ECN) * ECN

    if ShiftNum <= 5:           # 若几乎没有数据缺失或冗余，则不需要处理这个残缺周期
        AmpList = []            
        ANList = []
    else:
        AmpList = [findAveAmp(List[0 : ShiftNum])[0]]   #这个list就是每个周期的平均幅值
        ANList = [findAveAmp(List[0 : ShiftNum])[1]]    #Amp Num list存放每个周期幅值出现次数

    for x in range(1,CycleNum):
        Head = ShiftNum + ECN * (x-1)
        Tail = ShiftNum + ECN * x 
        Amp, AmpNum = findAveAmp(List[Head : Tail])
        AmpList.append(Amp)
        ANList.append(AmpNum)
    # 保存
    listToTxt(AmpList, OutFile)
    listToTxt(ANList, f"{OutFile}_每周期次数")


#=========================找到一个周期的平均幅值=========================
def findAveAmp(List):       #测试代码中有效率更高的函数，但这个更易读，若这个函数遇到性能瓶颈可以更换
    AmpList = []            #存放幅值的list
    Extreme = List[0]       #存放极值点
    Before = List[0]        #临时值，存放前一个
    Flag = True             #表示相邻两数的大小,后大于前为True
    AmpNum = 0              #记录幅值出现次数

    for x in List:  
        if x - Before < 0 and Flag == True:
            AmpList.append(abs(Before - Extreme)) 
            Flag = False
            Extreme = Before    #这句和上句不能换，猜测是解释器问题，无法及时将Before赋值给Extreme
            AmpNum += 1 
        elif x - Before > 0 and Flag == False:
            AmpList.append(abs(Before - Extreme))
            Flag = True
            Extreme = Before
            AmpNum += 1
        Before = x

    return np.mean(AmpList), AmpNum


#=========================将list写到txt文件中=========================
def listToTxt(List, OutFile):
    File = open(f"{OutFile}{OutFormat}", 'w')       #w表示每次覆盖写入新文件
    for i in range(len(List)):
        #去除[]、逗号，换行
        s = str(List[i]).replace('[','').replace(']','').replace(',','') +'\n'
        File.write(s)
    File.close()


#================================找出所有幅值================================
def findAllAmp(List, OutFile):
    AmpList = []            #存放幅值的list
    Extreme = List[0]       #存放极值点
    Before = List[0]        #临时值，存放前一个
    Flag = True             #表示相邻两数的大小,后大于前为True

    # for idx, x in enumerate(List):
    for x in List:  
        if x - Before < 0 and Flag == True:
            AmpList.append(Before - Extreme) 
            Flag = False
            Extreme = Before    #这句和上句不能换，猜测是解释器问题，无法及时将Before赋值给Extreme 
        elif x - Before > 0 and Flag == False:
            AmpList.append(Before - Extreme)
            Flag = True
            Extreme = Before
        Before = x

    listToTxt(AmpList, OutFile)


##=========================================================
##=======                 测试代码                 =========
##=========================================================


#这个方法效率高一些，但是更难读，相比之下，若循环次数不多，建议用list
def anotherfindAveAmp(List):
    AddAmp = 0              #存放幅值的和
    Extreme = List[0]       #存放极值点
    Before = List[0]        #临时值，存放前一个
    Flag = True             #表示相邻两数的大小,后大于前为True
    Times = 0               #记录幅值出现次数

    for x in List:
        if x - Before < 0 and Flag == True:
            AddAmp = abs(Before - Extreme) + AddAmp
            Flag = False
            Extreme = Before   #这句和上句不能换，猜测是解释器问题，无法及时将Before赋值给Extreme
            Times += 1
        elif x - Before > 0 and Flag == False:
            AddAmp =  abs(Before - Extreme) + AddAmp
            Flag = True
            Extreme = Before
            Times += 1
        Before = x

    return AddAmp / Times 


##=========================================================
##=======                  主代码                  =========
##=========================================================

if __name__ == '__main__':
    # DC()
    ACAllFolder([0,1,3,4])
    # specialOne(2)
    # specialOne(4)   


