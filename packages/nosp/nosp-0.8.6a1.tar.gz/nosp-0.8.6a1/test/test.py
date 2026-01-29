import concurrent.futures
import time

def task(n):
    print(f"Task {n} starting")
    time.sleep(2)
    return n * n

# 1. 手动创建线程池
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

# 2. 提交多个任务（返回 Future 对象）
futures = []
for i in range(100):
    future = executor.submit(task, i)
    futures.append(future)



time.sleep(10)
print('stop')


# 4. 手动关闭线程池（重要！）
executor.shutdown(wait=True)  # wait=True 表示等待所有任务完成后再关闭

