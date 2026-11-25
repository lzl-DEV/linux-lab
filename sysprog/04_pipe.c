/* 04_pipe.c —— TLPI 第 44 章：管道
 * pipe() + fork()：子进程写入一端，父进程从另一端读；注意两端要关掉不用的 fd。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int fd[2];
    if (pipe(fd) == -1) {
        perror("pipe");
        exit(EXIT_FAILURE);
    }

    pid_t child = fork();
    if (child == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    }

    if (child == 0) {
        close(fd[0]);                       /* 子进程只写 */
        char msg[64];
        int n = snprintf(msg, sizeof msg, "hello from child, pid = %ld\n",
                         (long) getpid());
        if (write(fd[1], msg, (size_t) n) != n) {
            perror("write");
            _exit(EXIT_FAILURE);
        }
        close(fd[1]);
        _exit(EXIT_SUCCESS);
    }

    close(fd[1]);                           /* 父进程只读 */
    char buf[128];
    ssize_t n = read(fd[0], buf, sizeof buf - 1);
    if (n == -1) {
        perror("read");
        exit(EXIT_FAILURE);
    }
    buf[n] = '\0';
    printf("父进程从管道读到 %ld 字节：%s", (long) n, buf);
    close(fd[0]);

    int status;
    waitpid(child, &status, 0);
    printf("子进程已回收，退出状态 = %d\n", WEXITSTATUS(status));
    return 0;
}
