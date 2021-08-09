#include <stdio.h>
#include <iostream>
#include <string>

//=============================================结构定义=============================================
#define MaxVertexNum 100

//邻接矩阵法
struct AMGraph{
    std::string VetData[MaxVertexNum];
    bool Edge[MaxVertexNum][MaxVertexNum];
    int vernum;
};

struct VetStackNode{
    int data;
    VetStackNode *next;
};


// //邻接表法（顺序+链式存储）
// //"边"/"弧"
// struct ArcNode{
//     int adjvex;    //边/弧指向哪个结点
//     struct ArcNode *next; //指向下一条弧的指针
//     //InfoType info;  //边权值
// };
// //"顶点"
// struct VNode{
//     string data; //顶点信息，数据类型不定，int只是一个例子
//     ArcNode *first;//第一条边/弧
// };
// //用邻接表存储的图
// struct ALGraph{
//     VNode AdjList[MaxVertexNum];
//     int vexnum,arcnum; //从0开始
// };


//=============================================函数声明=============================================
bool InitStack(VetStackNode * S);
bool Push(VetStackNode * S, int vernum);
bool Pop(VetStackNode * S, int & vernum);
bool isEmpty(VetStackNode * S);

bool InitGraph(AMGraph * Gra);
// bool AddVex(AMGraph * Gra, string data);
// bool AddEdge(AMGraph * Gra, int invexnum, int outvexnum);

bool DeleteVex(AMGraph * Gra, int vexnum);

bool Topo(AMGraph * Gra);
bool InverTopo(AMGraph * Gra);

int OutDegree(AMGraph * Gra, int vexnum);


//=============================================常用函数定义=============================================
bool InitStack(VetStackNode * S) {
    // VetStackNode *S = new VetStackNode;//分配一个头节点
    // if (S == NULL) {
    //     return false;
    // }
    S->next = NULL;
    return true;
}

bool Push(VetStackNode * S, int vernum){
    //入站不需要检查
    VetStackNode *ls = new VetStackNode;
    if (ls == NULL)return false;
    ls->data = vernum;
    ls->next = S->next;
    S->next = ls;
    return true;
}

bool Pop(VetStackNode * S, int &vernum){
    //判断
    if (S->next == NULL)return false;//栈空,这里的条件
    VetStackNode *q;
    q = S->next;
    S->next = q->next;
    vernum = q->data;
    delete(q);
    return true;
}

bool isEmpty(VetStackNode * S){
    if (S->next == NULL){
        return true;
    }
    else
        return false;
}

bool InitGraph(AMGraph * Gra){
    for (int i = 0; i < MaxVertexNum; ++i)
    {
        Gra->VetData[i] = "";
        for (int j = 0; j < MaxVertexNum; ++j){
            Gra->Edge[i][j] = 0;
        }
    }
    //修改这部分就是修改图的结构（节点和边）
    Gra->vernum = 7;
    Gra->VetData[0] = "准备厨具";
    Gra->VetData[1] = "打鸡蛋";
    Gra->VetData[2] = "下锅炒";
    Gra->VetData[3] = "吃";
    Gra->VetData[4] = "买菜";
    Gra->VetData[5] = "洗番茄";
    Gra->VetData[6] = "切番茄";

    Gra->Edge[0][1] = true;
    Gra->Edge[0][6] = true;
    Gra->Edge[4][1] = true;
    Gra->Edge[4][5] = true;
    Gra->Edge[1][2] = true;
    Gra->Edge[6][2] = true;
    Gra->Edge[2][3] = true;
    Gra->Edge[5][6] = true;

    return true;
}

//返回该顶点的出度
int OutDegree(AMGraph * Gra, int VetId){
    int outdegrees = 0;
    for (int i = 0; i < Gra->vernum; ++i){
        if (Gra->Edge[VetId][i] == true)
            ++outdegrees;
    }
    return outdegrees;
}

//逆拓扑排序
bool InverTopo(AMGraph * Gra){
    //初始化一个栈，用来暂存出度为0的顶点
    VetStackNode * vetstack = new VetStackNode;
    // VetStackNode * vetstack; //这个会引发错误“illegal hardware instruction”，为什么？
    InitStack(vetstack);

    //检查所有顶点，若出度为零，则压入栈
    for (int i = 0; i < Gra->vernum; ++i){
        if (OutDegree(Gra, i) == 0){
            Push(vetstack,i);
            // std::cout << Gra->VetData[i] << "压入栈" << std::endl;//测试代码
        }
    }
    int count = 0;
    while(!isEmpty(vetstack)){
        //将栈顶顶点出栈
        int outid = 0;
        Pop(vetstack,outid);
        std::cout << Gra->VetData[outid] << "出栈" << std::endl;//测试代码
        ++count;
        for (int k = 0; k < Gra->vernum; ++k){
            if (Gra->Edge[k][outid] == true){
                Gra->Edge[k][outid] = false;
                if (OutDegree(Gra, k) == 0){
                    Push(vetstack,k);
                    // std::cout << Gra->VetData[k] << "压入栈" << std::endl;//测试代码
                }
            }
        }
    }
    if (count < Gra->vernum){
        return false;
    }
    else
        return true;
}

//=============================================main函数=============================================
int main()
{   
    AMGraph * MyGra = new AMGraph;
    InitGraph(MyGra);
    InverTopo(MyGra);

    return 0;
}

