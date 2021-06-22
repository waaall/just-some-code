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

def Plot():
    #=========计算暴击收益=========
    CRIT_Rate = np.linspace(20,80,100)         
    DMG_Rate_CRIT = ((1 + (CRIT_Rate+3.9)/100 * (2*CRIT_Rate)/100) / (1 + CRIT_Rate/100 * 2*CRIT_Rate/100) -1) * 100
    #找极值点
    CRIT_Max = max(DMG_Rate_CRIT.tolist())
    CRIT_Max_Index = np.argmax(DMG_Rate_CRIT)

    #=========计算攻击收益=========
    ATK_Bonus_Per = np.linspace(50,200,320)
    DMG_Rate_ATK = ((1 + (ATK_Bonus_Per + 5.8)/100) / (1 + ATK_Bonus_Per/100) - 1)*100


    plt.figure(figsize=(16, 8))
    #=========双暴收益图=========  
    plt.subplot(121)
    plt.plot(CRIT_Rate,DMG_Rate_CRIT,color=colorList[1])
    # plt.legend(loc="upper right", fontsize=20)
    
    plt.xlabel("CRIT Rate")
    plt.ylabel("DMG_Rate(3.9CRIT)%")
    # plt.xticks(xTick)
    plt.ylim(1,4)

    show_max_CRIT=f"max:[{str(round(CRIT_Rate[CRIT_Max_Index]))}%, {str(round(CRIT_Max,2))}%]"
    # 画出最大值点的位置
    plt.plot(CRIT_Rate[CRIT_Max_Index],CRIT_Max,marker="H")
    # 标记出最大值点
    plt.annotate(show_max_CRIT,xy=(CRIT_Rate[CRIT_Max_Index],CRIT_Max),xytext=(CRIT_Rate[CRIT_Max_Index]-12,CRIT_Max+0.1))
    plt.title('CRIT',loc='left')

    #=========攻击力收益图=========
    plt.subplot(122)
    plt.plot(ATK_Bonus_Per,DMG_Rate_ATK,color=colorList[2])
    plt.xlabel("ATK Bonus Percentage")
    plt.ylabel("DMG_Rate(5.8ATK)%")
    plt.ylim(1,4)
    
    #画出对应收益点
    Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_ATK, CRIT_Max)
    plt.plot(ATK_Bonus_Per[Correspond_Index],CRIT_Max,marker="H")
    #标记对应收益点
    show_ATK=f"[{str(round(ATK_Bonus_Per[Correspond_Index]))}%, {str(round(Correspond_Value,2))}%]"
    plt.annotate(show_ATK,xy=(ATK_Bonus_Per[Correspond_Index],Correspond_Value),xytext=(ATK_Bonus_Per[Correspond_Index]-6,Correspond_Value+0.1))
    plt.title('ATK',loc='left')

    plt.tight_layout() 
    plt.savefig(PhotoName,dpi=200,format='png')

##=========================================================
##=======                  主代码                  =========
##=========================================================
if __name__ == '__main__':
    #设置所有生成图片的字体大小
    plt.rcParams.update({'font.size': 18})
    
    Plot()

