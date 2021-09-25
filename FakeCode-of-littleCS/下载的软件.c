#include "syscall" //系统调用

#define ServerAddress Add = 2.3.3.3


send(char content){
    syscall.print(content"已发送");
    syscall.网络发送(Add,content)
}

int main(){
    syscall.read(3);      //把3号块的文件读到内存
    syscall.print("正在加载");

    char content = syscall.input();
    
    if(push_button){
        send(content);
    }

    return 0;
}