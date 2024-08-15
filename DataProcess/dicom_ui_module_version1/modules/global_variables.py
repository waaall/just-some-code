'''
此文件为“全局变量”
'''

#算例文件夹名
AddFolder = "add"
Material = ["Graphene", "BP", "Net-τ", "Graphyne_beta", "Graphyne_delta", "Popgraphene"]
Folder = ["H", "Strain", 'Velocity', 'Tep']            #相对一级文件夹名称
POR_S = [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10, 12]


#算例输入文件名
File_H = ["Hfriction.in", "data.txt", "potential"]
File_S =["friction.in", "model.lmp", "potential"]
File_GK = ["myGK.in", "model.lmp", "potential"]
FinalData = "final.lmp"

#结果输出文件名
MLog = "log.txt"                #log文件去掉多余信息
VideoFolder = "video"

#脚本名
BatFile = "run.bat"
PlotScript = "AfterHS.py"
ResetScript = ["resetBefore.py", "resetAfter.py"]


##下面这几个量是用与Search文件内函数的参数
BaseUnit = 2.46
UpUnit = 4.26084499
duplicateFactor = 6912
CellSize = [3.23120000, 5.59660257, 5.14770000]
