struct 等待队列{
    balabala...
};
入等待队列(){
    balabala...
}
出等待队列(){
    balabala...
}

struct 就绪队列{
    balabala...
};
入就绪队列(){
    balabala...
}
出就绪队列(){
    balabala...
}

block(等待队列地址 地址){
    A进程 = 刚才压入函数栈的上个进程的;

    放入进程PCB(A进程.上下文, A进程.PCB地址);

    入等待队列(A进程.PCB地址);

    B进程 = 出就绪队列();
    放上CPU运行(B进程.PCB地址.上下文);
}

wakeup(等待队列地址 地址){
    A进程 = 刚才压入函数栈的上个进程的;

    放入进程PCB(A进程.上下文, A进程.PCB地址);

    出等待队列(A进程.PCB地址);

    B进程 = 出就绪队列();
    放上CPU运行(B进程.PCB地址.上下文);
}