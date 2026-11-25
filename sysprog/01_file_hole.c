/* 01_file_hole.c —— TLPI 第 4、5 章：文件 I/O 与文件空洞
 * 先用 write 写 3 个字节，再 lseek 跳过 1MB，然后写 3 个字节；
 * 用 stat 对比“逻辑大小 st_size”与“实际占用 st_blocks”。
 */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void)
{
    const char *path = "sparse.dat";
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        perror("open");
        exit(EXIT_FAILURE);
    }

    if (write(fd, "abc", 3) != 3) {
        perror("write");
        exit(EXIT_FAILURE);
    }
    if (lseek(fd, 1024 * 1024, SEEK_SET) == -1) {   /* 跳过 1 MB */
        perror("lseek");
        exit(EXIT_FAILURE);
    }
    if (write(fd, "xyz", 3) != 3) {
        perror("write");
        exit(EXIT_FAILURE);
    }
    close(fd);

    struct stat sb;
    if (stat(path, &sb) == -1) {
        perror("stat");
        exit(EXIT_FAILURE);
    }
    printf("st_size   = %lld 字节   （逻辑大小）\n", (long long) sb.st_size);
    printf("st_blocks = %lld 个 512B 块 = %lld 字节（实际占用磁盘）\n",
           (long long) sb.st_blocks, (long long) sb.st_blocks * 512);
    printf("空洞部分  = %lld 字节\n",
           (long long) sb.st_size - (long long) sb.st_blocks * 512);
    return 0;
}
