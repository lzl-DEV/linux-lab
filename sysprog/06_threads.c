/* 06_threads.c —— TLPI 第 30 章：线程同步
 * 4 个线程各把全局计数加 10 万次：不加锁会丢更新，加互斥锁才是准确值。
 */
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#define NTHREADS 4
#define LOOPS    100000

static long counter = 0;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int use_lock = 0;

static void *worker(void *arg)
{
    (void) arg;
    for (long i = 0; i < LOOPS; i++) {
        if (use_lock)
            pthread_mutex_lock(&lock);
        counter++;                      /* 读-改-写，不是原子操作 */
        if (use_lock)
            pthread_mutex_unlock(&lock);
    }
    return NULL;
}

static void run(const char *tag, int lock)
{
    pthread_t tid[NTHREADS];
    counter = 0;
    use_lock = lock;

    for (int i = 0; i < NTHREADS; i++) {
        if (pthread_create(&tid[i], NULL, worker, NULL) != 0) {
            perror("pthread_create");
            exit(EXIT_FAILURE);
        }
    }
    for (int i = 0; i < NTHREADS; i++)
        pthread_join(tid[i], NULL);

    printf("%-8s 期望 %7d，实际 %7ld\n", tag, NTHREADS * LOOPS, counter);
}

int main(void)
{
    run("不加锁", 0);
    run("加锁", 1);
    return 0;
}
