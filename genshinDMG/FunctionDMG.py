import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 

colorList = ['#4f4f4f', '#d35e5b', '#3d7ba7', '#369a62', '#844784', '#c59706', 
        '#292929', '#c1362c', '#29526f', '#598455', '#473e85', '#dbc19d']
markers = ["H", "*", "v", "^", "D", "x"]
PhotoName = ["",""]
##=========================================================
##=======                   函数                   =========
##=========================================================

#=======================基本伤害期望========================


def Plot():
    plt.figure(figsize=(18, 6))

    CRITRate = np.linspace(30,80,100)         
    DMG_Rate = ((1 + (CRITRate+3.9)/100 * (2*CRITRate+7.8)/100) / (1 + CRITRate/100 * 2*CRITRate/100) -1) * 100

    

    plt.subplot(121)
    
    plt.plot(CRITRate,DMG_Rate,color=colorList[2])
    # plt.plot(x,y,color=colorList[2],marker="H")   

    plt.legend(loc="upper right", fontsize=20)
    
    plt.xlabel("CRIT_Rate")
    plt.ylabel("DMG_Rate")
    # plt.xticks(xTick)
    # plt.xlim(0,10)
    # plt.ylim(0,2)
    plt.title('(a)',loc='left')

    plt.tight_layout() 
    plt.show()
    # plt.savefig(PhotoName[0],dpi=200,format='png')

##=========================================================
##=======                  主代码                  =========
##=========================================================
#设置所有生成图片的字体大小
plt.rcParams.update({'font.size': 18})

Plot()

