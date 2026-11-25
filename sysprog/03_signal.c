/* 03_signal.c —— TLPI 第 20、22 章：信号处理
 * 用 sigaction 安装 SIGINT 处理函数，getpid()+kill 给自己发信号，
 * 用 volatile sig_atomic_t 记录收到的信号；再验证 SIGKILL 不可捕获。
 */
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t got_signal = 0;

static void handler(int sig)
{
    got_signal = sig;
}

int main(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction");
        exit(EXIT_FAILURE);
    }

    printf("已安装 SIGINT 处理函数，pid = %ld\n", (long) getpid());
    printf("给自身发送 SIGINT……\n");
    if (kill(getpid(), SIGINT) == -1) {
        perror("kill");
        exit(EXIT_FAILURE);
    }
    printf("处理函数收到的信号编号 = %d（SIGINT = %d）\n",
           (int) got_signal, SIGINT);

    printf("尝试给 SIGKILL 安装处理函数：");
    fflush(stdout);
    sa.sa_handler = handler;
    if (sigaction(SIGKILL, &sa, NULL) == -1)
        printf("失败（预期结果：SIGKILL 与 SIGSTOP 不能被捕获或忽略）\n");

    printf("程序正常结束\n");
    return 0;
}
