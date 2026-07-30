#include "semaphore" //信号量
#include "Driver"

semaphore 硬盘地址框;
semaphore Buffer;   //硬盘缓冲区

semaphore.init(硬盘地址框,1)   // 每次只能一个进程读一个块
semaphore.init(Buffer,1);  // 只有一个硬盘缓冲区，所有进程互斥访问

read(Address){
    semaphore.wait(硬盘地址框);   //用前上锁
    Driver.放到地址框里(Address);

    semaphore.wait(Buffer);
    Driver.缓冲区拿走();

    semaphore.signal(Buffer);   
    semaphore.signal(硬盘地址框);   //用完解锁

}