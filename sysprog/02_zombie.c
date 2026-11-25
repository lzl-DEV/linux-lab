/* 02_zombie.c —— TLPI 第 24、26 章：fork 与僵尸进程
 * 子进程立刻退出，父进程先不 wait，用 ps 观察 Z 状态；回收后再观察一次。
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>

static void show(const char *tag, pid_t pid)
{
    char cmd[128];
    printf("--- %s ---\n", tag);
    fflush(stdout);
    snprintf(cmd, sizeof cmd, "ps -o pid,ppid,stat,comm -p %ld", (long) pid);
    system(cmd);
}

int main(void)
{
    pid_t child = fork();
    if (child == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    }
    if (child == 0) {
        printf("子进程 %ld 立刻退出（exit 0），此时父进程还在 sleep\n",
               (long) getpid());
        exit(EXIT_SUCCESS);
    }

    sleep(1);                       /* 父进程“忘了” wait，子进程变成僵尸 */
    show("子进程已退出、父进程尚未 wait", child);

    int status;
    if (waitpid(child, &status, 0) == -1) {
        perror("waitpid");
        exit(EXIT_FAILURE);
    }
    printf("waitpid 回收后，子进程退出状态 = %d\n", WEXITSTATUS(status));
    show("回收之后（ps 已查不到该进程）", child);
    return 0;
}
