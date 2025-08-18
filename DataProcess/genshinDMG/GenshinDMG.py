#此代码变量命名参考原神英文wiki，链接在下
#https://genshin-impact.fandom.com/wiki/Damage

#此计算都是基于本人文章的理论，由于实战情况复杂，具体计算结果是否具有参考意义，可以参考文章的具体讲述

Character = int(input("""你想计算的人物若是甘雨，请输入1；
              若是钟离，请输入2；
              若是温迪，请输入3；
              若是其他，请输入4：\n"""))

InputStat = input("""请将人物的面板参数按顺序依次输入，空格隔开：
顺序为：基础攻击力 攻击力加成 暴击率 暴击伤害 对应元素伤害加成 元素精通\n""")

Stats = [float(n) for n in InputStat.split()]

##=========================================================
##=======                   函数                   =========
##=========================================================

#=======================基本伤害期望========================
def Basic_DMG(Bonus):
    BasicATK = Stats[0]+Bonus[0]                #基础攻击力
    ATKBonus = Stats[1]+BasicATK*Bonus[1]/100   #攻击力加成
    CRITRate = (Stats[2]+Bonus[2])/100          #暴击率
    CRITDMG = (Stats[3]+Bonus[3])/100           #暴击伤害
    DMGBonus = (Stats[4]+Bonus[4])/100          #对应元素伤害加成
    EleMastery = Stats[5]+Bonus[5]              #元素精通

    DMGExpect = (BasicATK+ATKBonus) * (1+CRITRate*CRITDMG) * (1+DMGBonus)
    return DMGExpect

def Swirl_DMG(Char_Level, EleMastery):
    if Char_Level > 69:
        #还有待拟合
        Basic_Swirl_DMG = 868
        DMG = Basic_Swirl_DMG * 0.9 * 1.28 * (1.6 + 16 * EleMastery/(EleMastery + 2000))
        return DMG
    else:
        print("由于等级低扩散反应伤害收益低，所以不计算70级以下扩散伤害")

#=======================稀释后伤害增幅========================
def Gain_Rate(Bonus,Basic):
    Rate = ((Basic_DMG(Bonus) / Basic_DMG(Basic))-1)*100
    return Rate

def Genenal_Compare():
    print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,0,0,0,0])}\n=============\n")
    if Stats[2] < 35.0:
        if Stats[3] > 135.0:
            #计算暴伤头换暴击头收益：
            print(f"若暴伤头换暴击头收益伤害提升：")
        elif Stats[1]/Stats[0] > 2:
            #计算攻击头换为暴击头收益
            print(f"若攻击头换暴击头收益伤害提升：")
        else:
            print("\n=============\n你的双爆这么低，你是和我一样的非酋吗^_^\n=============\n")
            Rate = {'攻击收益':Gain_Rate([0,5.8,0,0,0,0],[0,0,0,0,0,0]), '暴击率收益':Gain_Rate([0,0,3.9,0,0,0],[0,0,0,0,0,0]), '爆伤收益': Gain_Rate([0,0,0,7.8,0,0])}
            print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

    elif Stats[2] > 80.0 and Character != 1:
        if Stats[3] < 140.0:
            #计算暴击头换暴伤头收益
            print(f"若暴击头换暴伤头收益伤害提升：")

        elif Stats[1]/Stats[0] < 1.2:
            #计算暴击头换攻击头
            print(f"若暴击头换攻击头收益伤害提升：")
        else:
            print("\n=============\n你的双爆这么高，你是欧皇吧^_^，但是暴击超过80%几乎没有收益了\n=============\n")
            Rate = {'攻击收益':Gain_Rate([0,5.8,0,0,0,0],[0,0,0,0,0,0]), '暴击率收益':0, '爆伤收益': Gain_Rate([0,0,0,7.8,0,0],[0,0,0,0,0,0])}
            print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")
    
    else:
        Rate = {'攻击收益':Gain_Rate([0,5.8,0,0,0,0],[0,0,0,0,0,0]), '暴击率收益':Gain_Rate([0,0,3.9,0,0,0],[0,0,0,0,0,0]), '爆伤收益': Gain_Rate([0,0,0,7.8,0,0],[0,0,0,0,0,0])}
        print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

#=======================钟离伤害期望==========================
def Zhongli_DMG(Zhongli,Bonus):
    BasicATK = Stats[0]+Bonus[0]                #基础攻击力
    ATKBonus = Stats[1]+BasicATK*Bonus[1]/100   #攻击力加成
    CRITRate = (Stats[2]+Bonus[2])/100          #暴击率
    CRITDMG = (Stats[3]+Bonus[3])/100           #暴击伤害
    DMGBonus = (Stats[4]+Bonus[4])/100          #对应元素伤害加成
    EleMastery = Stats[5]+Bonus[5]              #元素精通
    HP = Zhongli[0]+Zhongli[1]+Zhongli[0]*Bonus[6]/100 #生命
    Ability = Zhongli[2]/100                    #技能倍率

    DMGExpect = (HP*0.33 + (BasicATK+ATKBonus)*Ability) * (1+CRITRate*CRITDMG) * (1+DMGBonus)
    return DMGExpect

def Zhongli_Rate(Zhongli,Bonus):
    Rate = ((Zhongli_DMG(Zhongli,Bonus) / Zhongli_DMG(Zhongli,[0,0,0,0,0,0,0]))-1)*100
    return Rate

def Zhongli_Compare():
    Input = (input("请输入钟离的基础生命值，生命加成与Q技能倍率（仅计算Q技能伤害）："))
    Zhongli = [float(n) for n in Input.split()]
    InitialDMG = Zhongli_DMG(Zhongli,[0,0,0,0,0,0,0])
    
    print(f"\n=============\nQ技能伤害期望为：{InitialDMG}\n=============\n")
    
    Rate = {'攻击收益':Zhongli_Rate(Zhongli,[0,5.8,0,0,0,0,0]), '暴击率收益':Zhongli_Rate(Zhongli,[0,0,3.9,0,0,0,0]),
            '爆伤收益': Zhongli_Rate(Zhongli,[0,0,0,7.8,0,0,0]), '生命收益':Zhongli_Rate(Zhongli,[0,0,0,0,0,0,5.8])}
    print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

#=======================甘雨伤害期望==========================
def Ganyu_Compare():
    ### 这部分要重写，写成每部分空格分开输入，用数组记录条件，叠加被动的
    GanyuEnv = int(input("""你的甘雨若打融化反应输入1；
          若只打冰伤输入2；
          若是双冰阵容，请输入3；
          若圣遗物为冰四件套，请输入4；
          若圣遗物为乐团四件套，请输入5；
          若武器为阿莫斯之弓（仅算一精），请输入6；
          若武器为精1试作弓，请输入71，精1输入72；
注释：不打反应双冰且冰4阿莫斯则输入2346，且此计算至考虑重击，不考虑大招：\n"""))
    
    #这里没有加55%暴击率是考虑实际的被动触发率并非100%，阿莫斯被动按照3层计算，试作按照
    if GanyuEnv ==2347:
        print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,0,0,0,0])}\n=============\n")
        Rate = {'攻击收益':Gain_Rate([0,5.8,50,0,0,0],[0,0,50,0,0,0]), '暴击率收益':Gain_Rate([0,0,53.9,0,0,0],[0,0,50,0,0,0]), '爆伤收益': Gain_Rate([0,0,50,7.8,0,0],[0,0,50,0,0,0])}
        print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")
    
    elif GanyuEnv ==237:
        print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,0,0,0,0])}\n=============\n")
        Rate = {'攻击收益':Gain_Rate([0,5.8,30,0,0,0],[0,0,30,0,0,0]), '暴击率收益':Gain_Rate([0,0,33.9,0,0,0],[0,0,30,0,0,0]), '爆伤收益': Gain_Rate([0,0,30,7.8,0,0],[0,0,30,0,0,0])}
        print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

    elif GanyuEnv ==247:
        print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,0,0,0,0])}\n=============\n")
        Rate = {'攻击收益':Gain_Rate([0,5.8,35,0,0,0],[0,0,35,0,0,0]), '暴击率收益':Gain_Rate([0,0,38.9,0,0,0],[0,0,35,0,0,0]), '爆伤收益': Gain_Rate([0,0,35,7.8,0,0],[0,0,35,0,0,0])}
        print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

    elif GanyuEnv ==2357:
        print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,0,0,0,0])}\n=============\n")
        Rate = {'攻击收益':Gain_Rate([0,5.8,30,0,35,0],[0,0,30,0,35,0]), '暴击率收益':Gain_Rate([0,0,33.9,0,35,0],[0,0,30,0,35,0]), '爆伤收益': Gain_Rate([0,0,30,7.8,35,0],[0,0,30,0,35,0])}
        print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

    elif GanyuEnv ==2346:
        print(f"\n=============\n当前不考虑技能倍率的伤害期望为：{Basic_DMG([0,0,50,0,0,0])}\n=============\n")

    else:
        print("请输入正确的组合～(你要是打反应，冰套暴击率加成是无效的哦)")


#=======================温迪伤害期望==========================
def Venti_DMG(Venti,Bonus):
    #下面考虑对群（3人）扩散非水元素伤害，一个输出循环（2E1Q）

    #风伤(其中“1.28*0.63/2”是大招染色伤害和风伤的比例)
    Total_Anemo_DMG = Basic_DMG(Bonus) * 0.45 * (Venti[0]/100*2 + Venti[1]/100 * (1+1.28*0.63/2) * 19) * 3
    
    #扩散伤害
    Single_Swirl_DMG = Swirl_DMG(90, Stats[5]+Bonus[5])
    Total_Swirl_DMG = Single_Swirl_DMG * 8 * 6
    
    #总伤害
    Total_Venti_DMG = Total_Swirl_DMG + Total_Anemo_DMG

    return Total_Venti_DMG

def Venti_Rate(Venti,Bonus):
    Rate = ((Venti_DMG(Venti,Bonus) / Venti_DMG(Venti,[0,0,0,0,0,0]))-1)*100
    return Rate

def Venti_Compare():
    Input = (input("请输入温迪的E与Q技能倍率："))
    Venti = [float(n) for n in Input.split()] 
    #现面板伤害
    print(f"\n=============\n温迪对群（3人）染色非水元素总伤害为：{Venti_DMG(Venti,[0,0,0,0,0,0])}\n=============\n")

    #副词条收益
    Rate = {'攻击收益':Venti_Rate(Venti,[0,5.8,0,0,0,0]), '暴击率收益':Venti_Rate(Venti,[0,0,3.9,0,0,0]),
            '爆伤收益': Venti_Rate(Venti,[0,0,0,7.8,0,0]), '精通收益':Venti_Rate(Venti,[0,0,0,0,0,23])}
    print(f"\n=============\n副词条收益分别为:\n{Rate}\n=============\n")

#=======================核心函数（主函数）==========================
def DMG_Gain_Compare():
    if Character == 1:
        Ganyu_Compare()

    elif Character == 2:
        Zhongli_Compare()

    elif Character == 3:
        Venti_Compare()

    elif Character == 4:
        Genenal_Compare()

    else:
        print("输入格式错误")


##=========================================================
##=======                  主代码                  =========
##=========================================================
DMG_Gain_Compare()
