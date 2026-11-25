/* 05_mmap.c —— TLPI 第 49 章：内存映射
 * 用 MAP_SHARED|MAP_ANONYMOUS 建一块父子共享的内存，
 * 与普通（私有）变量对比，说明“共享映射”与“写时复制”的区别。
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int *shared = mmap(NULL, sizeof(int), PROT_READ | PROT_WRITE,
                       MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    if (shared == MAP_FAILED) {
        perror("mmap");
        exit(EXIT_FAILURE);
    }
    *shared = 0;
    int local = 0;               /* 普通变量：fork 后是各写各的副本 */

    pid_t child = fork();
    if (child == -1) {
        perror("fork");
        exit(EXIT_FAILURE);
    }

    if (child == 0) {
        *shared = 42;
        local = 99;
        printf("子进程写入后：*shared = %d，local = %d\n", *shared, local);
        _exit(EXIT_SUCCESS);
    }

    wait(NULL);
    printf("父进程看到：*shared = %d（MAP_SHARED 对子进程可见），"
           "local = %d（普通变量仍是自己的副本）\n", *shared, local);

    munmap(shared, sizeof(int));
    return 0;
}
