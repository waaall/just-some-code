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

    Plot(CRIT_DMG_Rate, DMG_Rate_CRIT, 14450)

# 计算夜兰的收益
def YeLan():
    #=========计算暴击收益=========
    Basic_HP = 14450
    CRIT_Rate = np.linspace(30,100,100)         
    DMG_Rate_CRIT = ((1 + (CRIT_Rate+3.9)/100 * (2*CRIT_Rate)/100) / (1 + CRIT_Rate/100 * 2*CRIT_Rate/100) -1) * 100

    #找极值点
    CRIT_Max = max(DMG_Rate_CRIT.tolist())
    CRIT_Max_Index = np.argmax(DMG_Rate_CRIT)

    #=========计算生命收益=========
    HP_Bonus_Per = np.linspace(50,200,300)
    HP = Basic_HP * (1+HP_Bonus_Per/100)
    DMG_Rate_HP = ((1 + (HP_Bonus_Per + 5.8)/100) / (1 + HP_Bonus_Per/100) - 1)*100

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

    #=========生命收益图=========
    plt.subplot(122)
    plt.plot(HP,DMG_Rate_HP,color=colorList[2])
    plt.xlabel("HP")
    plt.ylabel("DMG_Rate(5.8HP)%")
    plt.xlim(Basic_HP*1.5,Basic_HP*3)
    plt.ylim(1,4)
    
    #画出对应收益点
    Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_HP, CRIT_Max)
    plt.plot(HP[Correspond_Index],CRIT_Max,marker="H")
    #标记对应收益点
    show_HP=f"[{str(round(HP[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    plt.annotate(show_HP,xy=(HP[Correspond_Index],Correspond_Value),xytext=(HP[Correspond_Index]-6,Correspond_Value+0.1))
    
    plt.title('HP',loc='left')
    plt.tight_layout() 
    plt.savefig(PhotoName,dpi=200,format='png')


# 计算胡桃的收益
def HuTao():
    #=========计算暴击收益=========
    CRIT_Rate = np.linspace(30,100,200)  
    DMG_Rate_CRIT = ((1 + (CRIT_Rate+3.9)/100 * (2*CRIT_Rate)/100) / (1 + CRIT_Rate/100 * 2*CRIT_Rate/100) -1) * 100

    #找极值点
    CRIT_Max = max(DMG_Rate_CRIT.tolist())
    CRIT_Max_Index = np.argmax(DMG_Rate_CRIT)

    #=======计算爆伤收益(百暴)=======
    CRIT_DMG = np.linspace(200,300,200)
    DMG_Rate_CRITDMG = (((CRIT_DMG+107.8)/100) / ((CRIT_DMG+100)/100) - 1)*100

    #=========计算生命收益=========
    Basic_HP = 15552
    HP_Bonus_Per = np.linspace(50,250,200)
    HP = Basic_HP * (1+HP_Bonus_Per/100)
    Basic_ATK = 1155 # HuTao_HuMo_ZhuiYi_Basic_ATK = 715*1.18+311
    ATK = HP*(0.0626+0.018) + Basic_ATK # 0.018是一精护摩
    DMG_Rate_HP = (((HP+Basic_HP*0.058)*(0.0626+0.018) + Basic_ATK) / ATK - 1) * 100
    
    #=========计算火伤收益=========
    Pyro_DMG = np.linspace(46.6,220,300)
    DMG_Rate_Pyro = ((1+Pyro_DMG/100+0.058) / (1+Pyro_DMG/100) -1) * 100

    #=========计算精通收益=========
    EM = np.linspace(50,400,800)    
    # EM_Profit = 25*EM/(9*(EM+1400))+1
    DMG_Rate_EM = ((25*(EM+23)/(9*(EM+23+1400))+1)/(25*EM/(9*(EM+1400))+1) - 1) * 100 


    plt.figure(figsize=(32, 8))
    #=========双暴收益图=========  
    plt.subplot(151)
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


    #=======爆伤收益图(百暴)=======
    plt.subplot(152)
    plt.plot(CRIT_DMG,DMG_Rate_CRITDMG,color=colorList[2])
    plt.xlabel("CRIT_DMG(100%CRIT_Rate)")
    plt.ylabel("DMG_Rate(7.8CRITDMG)%")
    plt.xlim(200,300)
    plt.ylim(1,4)
    plt.title('CRIT_DMG(100%CRIT_Rate)',loc='left')

    #=========精通收益图=========
    plt.subplot(153)
    plt.plot(EM,DMG_Rate_EM,color=colorList[3])
    plt.xlabel("Elemental_Mastery")
    plt.ylabel("DMG_Rate(23EM)%")
    plt.xlim(50,400)
    plt.ylim(1,4)

    #画出对应收益点
    Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_EM, CRIT_Max)
    plt.plot(EM[Correspond_Index],CRIT_Max,marker="H")
    #标记对应收益点
    show_EM=f"[{str(round(EM[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    plt.annotate(show_EM,xy=(EM[Correspond_Index],Correspond_Value),xytext=(EM[Correspond_Index]-6,Correspond_Value+0.1))

    plt.title('Elemental_Mastery',loc='left')

    #=========火伤收益图=========
    plt.subplot(154)
    plt.plot(Pyro_DMG,DMG_Rate_Pyro,color=colorList[4])
    plt.xlabel("Pyro_DMG")
    plt.ylabel("DMG_Rate(5.8Pyro)%")
    plt.xlim(46.6,220)
    plt.ylim(1,4)
    
    #画出对应收益点
    Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_Pyro, CRIT_Max)
    plt.plot(Pyro_DMG[Correspond_Index],CRIT_Max,marker="H")
    #标记对应收益点
    show_Pyro_DMG=f"[{str(round(Pyro_DMG[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    plt.annotate(show_Pyro_DMG,xy=(Pyro_DMG[Correspond_Index],Correspond_Value),xytext=(Pyro_DMG[Correspond_Index]-6,Correspond_Value+0.1))
    
    plt.title('Pyro_DMG',loc='left')

    #=========生命收益图=========
    plt.subplot(155)
    plt.plot(ATK,DMG_Rate_HP,color=colorList[5])
    plt.xlabel("Real_ATK")
    plt.ylabel("DMG_Rate(5.8HP)%")
    plt.xlim(3000,4500)
    plt.ylim(1,4)
    
    # #画出对应收益点
    # Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_HP, CRIT_Max)
    # plt.plot(HP[Correspond_Index],CRIT_Max,marker="H")
    # #标记对应收益点
    # show_HP=f"[{str(round(HP[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    # plt.annotate(show_HP,xy=(HP[Correspond_Index],Correspond_Value),xytext=(HP[Correspond_Index]-6,Correspond_Value+0.1))
    
    plt.title('HP(With HuMo)',loc='left')


    plt.tight_layout() 
    plt.savefig(PhotoName,dpi=200,format='png')


# 看胡桃的收益平衡性
def HuTao_balance():
    #=========输入面板========= 
    Input = input("""请将胡桃面板按顺序(开E攻击力 火伤加成 元素精通 暴击率 暴击伤害)依次输入，空格隔开：\n""")
    Attribute = np.array([float(n) for n in Input.split()])
    ATK = Attribute[0]
    Pyro_DMG = Attribute[1]
    EM = Attribute[2]  
    CRIT_Rate = Attribute[3]
    CRIT_DMG = Attribute[4]

    #=========暴击收益========= 
    DMG_Rate_CRIT = ((1 + (CRIT_Rate+3.9)/100 * (CRIT_DMG)/100) / (1 + CRIT_Rate/100 * CRIT_DMG/100) -1) * 100
    if CRIT_Rate > 96.1:
        DMG_Rate_CRIT = ((1 + CRIT_DMG/100) / (1 + CRIT_Rate/100 * CRIT_DMG/100) -1) * 100
    if CRIT_Rate > 100:
        CRIT_Rate = 100

    #========爆伤收益==========
    DMG_Rate_CRITDMG = ((1 + CRIT_Rate/100 * (CRIT_DMG+7.8)/100) / (1 + CRIT_Rate/100 * CRIT_DMG/100) -1) * 100
    
    #=========生命收益=========
    Basic_HP = 15552
    DMG_Rate_HP = (((Basic_HP*0.058)*(0.0626+0.018) + ATK) / ATK - 1) * 100
    
    #=========火伤收益=========
    DMG_Rate_Pyro = ((1+Pyro_DMG/100+0.058) / (1+Pyro_DMG/100) -1) * 100
    
    #=========精通收益=========  
    DMG_Rate_EM = ((25*(EM+23)/(9*(EM+23+1400))+1)/(25*EM/(9*(EM+1400))+1) - 1) * 100 

    #=========期望伤害========= 
    DMG = ATK * (1 + Pyro_DMG/100) * (1 + CRIT_Rate/100 * CRIT_DMG/100) * 1.5 * (1 + 25*EM/(9*(EM+1400)+1)) * 2.426 * 0.45 

    After_CRIT_DMG = ATK * (1 + Pyro_DMG/100) * (1 + CRIT_DMG/100) * 1.5 * (1 + 25*EM/(9*(EM+1400)+1)) * 2.426 * 0.45

    Profit = [DMG_Rate_HP, DMG_Rate_Pyro, DMG_Rate_EM, DMG_Rate_CRIT, DMG_Rate_CRITDMG]

    #=========画图=========
    fig, ax = plt.subplots()
    X = ["HP", "Pyro_DMG", "EM", "CRIT_Rate", "CRIT_DMG"]
    ax.bar(X, Profit, width=0.4, color = [colorList[0], colorList[5], colorList[1], colorList[3], colorList[2]])
    ax.set(ylim=(1, 4))
    
    for a,b in zip(X, Profit):
        plt.text(a, b+0.05, '%.2f' %b, ha='center', va= 'bottom',fontsize=8)

    StringDMG = "Expected_DMG = " + str(int(DMG)) + "\nCRIT_DMG = " + str(int(After_CRIT_DMG))
    plt.title(StringDMG,loc='right')
    plt.tight_layout() 
    plt.savefig("HuTao_balance.png",dpi=200,format='png')
    plt.show()

# 计算胡桃在不同队伍的收益
def HuTao_Team():
    #=========设置buff=========
    ATK_Atem_Num = 2
    ATK_Atem = 0.058 * ATK_Atem_Num 
    TaoLong = 0.48
    Zongshi = 0.2
    QianYan = 0.2
    ZhongMo = 0.2

    ZhongMo_EM = 100
    MoNa = 100
    ShaTang = 190
    ABD = 125

    # 胡行钟阿
    ATK_buff = ATK_Atem + Zongshi
    EM_buff = ABD


    # ATK_buff = TaoLong + Zongshi + QianYan + ZhongMo
    # EM_buff = ZhongMo_EM + ShaTang + MoNa + ABD
    
    #=========计算生命收益=========
    Basic_HP = 15552
    HP_Bonus_Per = np.linspace(50,250,200)
    HP = Basic_HP * (1+HP_Bonus_Per/100)
    Basic_ATK = 1155 + 715 * ATK_buff # HuTao_HuMo_ZhuiYi_Basic_ATK = 715*1.18+311
    ATK = HP*(0.0626+0.018) + Basic_ATK # 0.018是一精护摩
    
    DMG_Rate_HP = (((Basic_HP*0.058)*(0.0626+0.018) + ATK) / ATK - 1) * 100

    #=========计算精通收益=========
    EM = np.linspace(50,400,800)    
    # EM_Profit = 25*EM/(9*(EM+1400))+1
    DMG_Rate_EM = ((25*(EM+EM_buff+23)/(9*(EM+EM_buff+23+1400))+1)/(25*(EM+EM_buff)/(9*(EM+EM_buff+1400))+1) - 1) * 100 


    plt.figure(figsize=(16, 8))

    #=========精通收益图=========
    plt.subplot(121)
    plt.plot(EM,DMG_Rate_EM,color=colorList[2])
    plt.xlabel("Elemental_Mastery")
    plt.ylabel("DMG_Rate(23EM)%")
    plt.xlim(50,400)
    plt.ylim(1,3)

    # #画出对应收益点
    # Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_EM, CRIT_Max)
    # plt.plot(EM[Correspond_Index],CRIT_Max,marker="H")
    # #标记对应收益点
    # show_EM=f"[{str(round(EM[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    # plt.annotate(show_EM,xy=(EM[Correspond_Index],Correspond_Value),xytext=(EM[Correspond_Index]-6,Correspond_Value+0.1))

    plt.title('Elemental_Mastery',loc='left')

    #=========生命收益图=========
    plt.subplot(122)
    plt.plot(HP,DMG_Rate_HP,color=colorList[3])
    plt.xlabel("Real_ATK")
    plt.ylabel("DMG_Rate(5.8HP)%")
    plt.xlim(23328,40000)
    plt.ylim(1,3)
    
    # #画出对应收益点
    # Correspond_Index,Correspond_Value = Find_Closest(DMG_Rate_HP, CRIT_Max)
    # plt.plot(HP[Correspond_Index],CRIT_Max,marker="H")
    # #标记对应收益点
    # show_HP=f"[{str(round(HP[Correspond_Index]))}, {str(round(Correspond_Value,2))}%]"
    # plt.annotate(show_HP,xy=(HP[Correspond_Index],Correspond_Value),xytext=(HP[Correspond_Index]-6,Correspond_Value+0.1))
    
    plt.title('HP(With HuMo)',loc='left')

    plt.tight_layout() 
    plt.savefig("HuTao_Team.png",dpi=200,format='png')


##=========================================================
##=======                  主代码                  =========
##=========================================================
def main():
    # HuTao()
    HuTao_balance()
    # HuTao_Team()

    # Basic_ATK = int(input("请输入人物基础攻击力："))
    # GenOrNot = float(input("若计算通用情况，请输入0.0; 若计算夜兰, 请输入1.0; 若计算冰套双冰永动体系，请输入面板暴击率："))
    
    # if GenOrNot == 0.0:
    #     CalGeneral(Basic_ATK)
    # elif GenOrNot == 1.0:
    #     YeLan()
    # else:
    #     GanYu(GenOrNot + 55.0, Basic_ATK) ##雾切神里1016；锻造神里796；阿莫斯甘雨943；锻造甘雨845

if __name__ == '__main__':
    #设置所有生成图片的字体大小
    plt.rcParams.update({'font.size': 12})
    
    main()

