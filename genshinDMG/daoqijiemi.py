import numpy as np

##=========================================================
##=======                   函数                   =========
##=========================================================

#=======================核心函数：计算打击次数========================
def Find(RoteMatrix, dimension):
    ##输入初始状态
    Input = input("""请将雷立方的初始状态按顺序依次输入，空格隔开：\n""")
    InitState = np.array([int(n) for n in Input.split()])

    #初始化循环参数
    Solution = np.array([np.random.randint(0,4) for _ in range(dimension)])
    i = 0
    Zero = [0] * dimension
    
    #循环：结果均为4的倍数，或者循环过多次停止
    while list(np.mod(RoteMatrix.dot(Solution)+InitState,4)) != Zero and i<2000:
        Solution = np.array([np.random.randint(0,4) for _ in range(dimension)])
        i = i+1
    
    print(Solution)

#=======================四个魔方（荒海地下）========================
def Four():
    Dyi  = np.array([1,1,0,1]) 
    Der  = np.array([1,1,1,0])
    Dsan = np.array([0,1,1,1])
    Dsi  = np.array([1,0,1,1])
    RoteMatrix = np.array([Dyi,Der,Dsan,Dsi]).T

    Find(RoteMatrix, 4)

#=======================五个魔方（荒海地下）========================
def Five():
    Dyi  = np.array([1,0,1,0,0]) 
    Der  = np.array([1,1,1,0,0])
    Dsan = np.array([1,0,1,0,1])
    Dsi  = np.array([0,0,1,1,1])
    Dwu  = np.array([0,0,1,0,1])
    RoteMatrix = np.array([Dyi,Der,Dsan,Dsi,Dwu]).T

    print(RoteMatrix)

    Find(RoteMatrix, 5)


##=========================================================
##=======                  主代码                  =========
##=========================================================
def main():
    Which = int(input("""若是四个魔方，请输入4；\n若是五个魔方，请输入5：\n"""))
    
    if Which == 4:
        Four()
    elif Which == 5:
        Five()
    else:
        print("请输入正确的数字～")

if __name__ == '__main__':
    main()