import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 

colorList = ['#4f4f4f', '#d35e5b', '#3d7ba7', '#369a62', '#844784', '#c59706', 
        '#292929', '#c1362c', '#29526f', '#598455', '#473e85', '#dbc19d']
markers = ["H", "*", "v", "^", "D", "x"]
PhotoName = "收益图.png"
##=========================================================
##=======                   函数                   =========
##=========================================================
def Find_Closest(array, value):
    n = [abs(i-value) for i in array]
    idx = n.index(min(n))
    return idx,array[idx]

def Plot(CRIT_Rate, DMG_Rate_CRIT, Basic_ATK):
    #找极值点
    CRIT_Max = max(DMG_Rate_CRIT.tolist())
    CRIT_Max_Index = np.argmax(DMG_Rate_CRIT)

    #=========计算攻击收益=========
    ATK_Bonus_Per = np.linspace(50,200,300)
    ATK = Basic_ATK * (1+ATK_Bonus_Per/100)
    DMG_Rate_ATK = ((1 + (ATK_Bonus_Per + 5.8)/100) / (1 + ATK_Bonus_Per/100) - 1)*100

    plt.figure(figsize=(16, 8))
    #=========双暴收益图=========  
    plt.subplot(121)
    plt.plot(CRIT_Rate,DMG_Rate_CRIT,color=colorList[1])
    # plt.legend(loc="upper right", fontsize=20)
    
    plt.xlabel("CRIT Rate/CRIT_DMG_Rate")
    plt.ylabel("DMG_Rate(3.9CRIT or 7.8CRIT_DMG)%")
    # plt.xticks(xTick)
    plt.ylim(1,4)

    show_max_CRIT=f"max:[{str(round(CRIT_Rate[CRIT_Max_Index]))}%, {str(round(CRIT_Max,2))}%]"
    # 画出最大值点的位置
    plt.plot(CRIT_Rate[CRIT_Max_Index],CRIT_Max,marker="H")
    # 标记出最大值点
    plt.annotate(show_max_CRIT,xy=(CRIT_Rate[CRIT_Max_Index],CRIT_Max),xytext=(CRIT_Rate[CRIT_Max_Index]-6,CRIT_Max+0.1))
    
    plt.title('CRIT',loc='left')

    #=========攻击力收益图=========
    plt.subplot(122)
    plt.plot(ATK,DMG_Rate_ATK,color=colorList[2])
    plt.xlabel("ATK")
    plt.ylabel("DMG_Rate(5.8ATK)%")
    plt.xlim(Basic_ATK*1.5,Basic_ATK*3)
    plt.ylim(1,4)
    
    #画出对应收益点
    Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_ATK, CRIT_Max)
    plt.plot(ATK[Correspond_Index],CRIT_Max,marker="H")
    #标记对应收益点
    show_ATK=f"[{str(round(ATK[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    plt.annotate(show_ATK,xy=(ATK[Correspond_Index],Correspond_Value),xytext=(ATK[Correspond_Index]-6,Correspond_Value+0.1))
    
    plt.title('ATK',loc='left')
    plt.tight_layout() 
    plt.savefig(PhotoName,dpi=200,format='png')

#计算通用情况下的暴击收益函数
def CalGeneral(Basic_ATK):
    #=========计算暴击收益=========
    CRIT_Rate = np.linspace(20,80,100)         
    DMG_Rate_CRIT = ((1 + (CRIT_Rate+3.9)/100 * (2*CRIT_Rate)/100) / (1 + CRIT_Rate/100 * 2*CRIT_Rate/100) -1) * 100

    #=========调用画图函数=========
    Plot(CRIT_Rate, DMG_Rate_CRIT, Basic_ATK)

#计算冰套双冰永冻体系的暴伤收益函数
def GanYu(CRIT_Rate, Basic_ATK):
    #=========计算暴伤收益=========
    CRIT_DMG_Rate = np.linspace(120,270,300)  

    #这个变量名字起的不好，指暴击暴伤收益       
    DMG_Rate_CRIT = ((1 + (CRIT_Rate)/100 * (CRIT_DMG_Rate+7.8)/100) / (1 + CRIT_Rate/100 * CRIT_DMG_Rate/100) -1) * 100

    Plot(CRIT_DMG_Rate, DMG_Rate_CRIT, Basic_ATK)


##=========================================================
##=======                  主代码                  =========
##=========================================================
def main():
    Basic_ATK = int(input("请输入人物基础攻击力："))
    GenOrNot = float(input("若计算通用情况，请输入0.0，若计算冰套双冰永动体系，请输入面板暴击率："))
    
    if GenOrNot == 0.0:
        CalGeneral(Basic_ATK)
    else:
        GanYu(GenOrNot + 55.0, Basic_ATK) ##雾切神里1016；锻造神里796；阿莫斯甘雨943；锻造甘雨845

if __name__ == '__main__':
    #设置所有生成图片的字体大小
    plt.rcParams.update({'font.size': 18})
    
    main()

