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


#=======================核心函数（主函数）==========================
def DMG_Gain_Compare():
    if Character == 1:
        Ganyu_Compare()

    elif Character == 2:
        Zhongli_Compare()

    elif Character == 3:
        print("温迪的计算会加入元素精通的影响，还在开发中")

    elif Character == 4:
        Genenal_Compare()

    else:
        print("输入格式错误")


##=========================================================
##=======                  主代码                  =========
##=========================================================
DMG_Gain_Compare()
