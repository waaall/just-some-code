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
def Gain_Rate(Bonus):
    Rate = ((Basic_DMG(Bonus) / Basic_DMG([0,0,0,0,0,0]))-1)*100
    return Rate

def Genenal_Compare():
    if Stats[2] < 35.0:
        if Stats[3] > 135.0:
            #计算暴伤头换暴击头收益：
            print(f"若暴伤头换暴击头收益伤害提升：")
        else:
            print("\n=========\n你的双爆这么低，你是和我一样的非酋吗^_^\n=========\n")

    elif Stats[2] > 80.0:
        if Stats[3] < 140.0:
            #计算暴击头换暴伤头收益
            print(f"若暴击头换暴伤头收益伤害提升：")

        elif Stats[1]/Stats[0] < 1.2:
            #计算暴击头换攻击头
            print(f"若暴击头换攻击头收益伤害提升：")
        else:
            print("\n=========\n你的双爆这么高，你是欧皇吧^_^\n=========\n")
            Rate = {'攻击收益':Gain_Rate([0,5.8,0,0,0,0]), '暴击率收益':Gain_Rate([0,0,3.9,0,0,0]), '爆伤收益': Gain_Rate([0,0,0,7.8,0,0])}
            print(f"副词条收益分别为:\n{Rate}")
    
    else:
        Rate = {'攻击收益':Gain_Rate([0,5.8,0,0,0,0]), '暴击率收益':Gain_Rate([0,0,3.9,0,0,0]), '爆伤收益': Gain_Rate([0,0,0,7.8,0,0])}
        print(f"副词条收益分别为:\n{Rate}")

#=======================钟离伤害期望==========================
def Zhongli_DMG(Zhongli,Bonus):
    BasicATK = Stats[0]+Bonus[0]                #基础攻击力
    ATKBonus = Stats[1]+BasicATK*Bonus[1]       #攻击力加成
    CRITRate = (Stats[2]+Bonus[2])/100          #暴击率
    CRITDMG = (Stats[3]+Bonus[3])/100           #暴击伤害
    DMGBonus = (Stats[4]+Bonus[4])/100          #对应元素伤害加成
    EleMastery = Stats[5]+Bonus[5]              #元素精通
    HP = Zhongli[0]+Zhongli[1]+Zhongli[0]*Bonus[6]/100 #生命
    Ability = Zhongli[2]/100                    #技能倍率

    DMGExpect = (HP*0.33 + (BasicATK+ATKBonus)*Ability) * (1+CRITRate*CRITDMG) * (1+DMGBonus)
    return DMGExpect

def Zhongli_Rate():
    Input = (input("请输入钟离的基础生命值，生命加成与Q技能倍率（仅计算Q技能伤害）："))
    Zhongli = [float(n) for n in Input.split()]
    InitialDMG = Zhongli_DMG(Zhongli,[0,0,0,0,0,0,0])
    print(f"Q技能伤害期望为：{InitialDMG}")


#=======================核心函数（主函数）==========================
def DMG_Gain_Compare():
    if Character == 1:
        print("甘雨由于其冰套等会影响其伤害计算，还在开发中")

    elif Character == 2:
        Zhongli_Rate()

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