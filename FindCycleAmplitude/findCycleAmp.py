# import xlrd,openpyxl              #xlrd新版不支持xlsx格式，需要再安装openpyxl
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt   #若用python画图则import


##=========================================================
##=======                   常量                   =========
##=========================================================

WorkFolder = "data"         #数据所在文件夹
InputName = "3"             #数据文件名
InputFormat = ".xlsx"       #数据文件格式
ECN = 100                   #一个周期数据数量Each Cycle Number


##=========================================================
##=======                   函数                   =========
##=========================================================

#============最核心的函数，首先按照周期分割数据，再找到平均Amp并保存============
def splitAndFind(List, OutFile):
    TotalLength = len(List)                             #list总长
    CycleNum = int(TotalLength / ECN + 1)               #总周期数
    ShiftNum = TotalLength - int(TotalLength / ECN) * ECN

    AmpList = [findAveAmp(List[0 : ShiftNum - 1])]
    for x in range(1,CycleNum):
        Head = ShiftNum + ECN * (x-1)
        Tail = ShiftNum + ECN * x -1
        Amp = findAveAmp(List[Head : Tail])
        AmpList.append(Amp)
    # 保存
    listToTxt(AmpList, OutFile)

#=========================找到一个周期的平均幅值=========================
def findAveAmp(List):       #测试代码中有效率更高的函数，但这个更易读，若这个函数遇到性能瓶颈可以更换
    AmpList = []            #存放幅值的list
    Extreme = List[0]       #存放极值点
    Before = List[0]        #临时值，存放前一个
    Flag = True             #表示相邻两数的大小,后大于前为True

    for x in List:  
        if x - Before < 0 and Flag == True:
            AmpList.append(abs(Before - Extreme)) 
            Flag = False
            Extreme = Before    #这句和上句不能换，猜测是解释器问题，无法及时将Before赋值给Extreme 
        elif x - Before > 0 and Flag == False:
            AmpList.append(abs(Before - Extreme))
            Flag = True
            Extreme = Before
        Before = x

    return np.mean(AmpList)

#=========================将list写到txt文件中=========================
def listToTxt(List, OutFile):
    File = open(OutFile, 'w')       #w表示每次覆盖写入新文件
    for i in range(len(List)):
        #去除[]、逗号，换行
        s = str(List[i]).replace('[','').replace(']','').replace(',','') +'\n'
        File.write(s)
    File.close()


##=========================================================
##=======                  主代码                  =========
##=========================================================

if __name__ == '__main__':
    # 把数据读入内存，格式是DataFrame，矩阵形式，两列数据分别叫做first、second
    InitMatrics = pd.read_excel(f"{WorkFolder}/{InputName}{InputFormat}", engine='openpyxl', header=None, names=['first','second'])
    
    #每列数据计算保存一份
    for col in ["first", "second"]:
        #这列数据转为list，然后调用函数，找出所有幅值（amplitude），并保存
        splitAndFind(InitMatrics[col].tolist(), f"{WorkFolder}/{InputName}_{col}.txt")


##=========================================================
##=======                 测试代码                 =========
##=========================================================

# 找出所有幅值
def findAllAmp(List):
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

    return AmpList

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