#include "调度"

struct semaphore{
    left_num;
    struct 等待队列地址 Address;
};

init(semaphore resource, num){
    resource.left_num = num;
    resource.Address = new struct 等待队列地址;
}

//上锁
wait(semaphore resource){
    resource.left_num --1;
    
    if(resource.left_num < 0){
        调度.block(resource.Address); //阻塞该进程
    }
}

//解锁
signal(semaphore resource){
    resource.left_num ++1;
    
    if(resource.left_num <= 0){
        调度.wakeup(resource.Address); //唤醒该进程
    }
}

