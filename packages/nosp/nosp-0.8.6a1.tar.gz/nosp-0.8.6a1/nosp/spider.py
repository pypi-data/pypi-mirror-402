import abc
import datetime
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Callable

from loguru import logger

from . import SpiderInfo
from .database import Redis
from .http import Request, BaseRequest
import argparse

from .utils import get_md5


class SpiderThreadPool(object):

    def __init__(self):
        self.executor: Optional[ThreadPoolExecutor] = None

    def future_callback(self, future):
        if future.exception():
            raise future.exception()

    def submit_task(self, task_func, task):
        """
        向线程池中添加新任务
        :param task_func:
        :param task:
        :return:
        """
        future = self.executor.submit(task_func, task)
        future.add_done_callback(self.future_callback)

    def get_task_count(self) -> int:
        """
        获取当前线程池中还有多少任务数量
        :return:
        """
        return self.executor._work_queue.qsize()

    def start_batch_task(self, task_func, task_list: list, thread_num: int, wait=True):
        """
        多线程批量处理任务
        :param task_func: 任务函数
        :param task_list: 任务列表
        :param thread_num: 线程数量
        :param wait: 是否等待
        :return:
        """
        self.executor = ThreadPoolExecutor(max_workers=thread_num)
        try:
            for task in task_list:
                future = self.executor.submit(task_func, *task)
                future.add_done_callback(self.future_callback)
        finally:
            if wait:
                self.executor.shutdown(wait=True)
            # if wait:
            #     self.executor.shutdown(wait=False)
            #     while True:
            #         try:
            #             time.sleep(10)
            #         except KeyboardInterrupt:
            #             self.executor.shutdown(wait=True,cancel_futures=True)

    def task_wait(self):
        self.executor.shutdown(wait=True)


class BaseSpider(abc.ABC):

    def __init__(self, info: SpiderInfo = None, headers=None, cookies=None, proxy_url=None):
        """
        Spider 基类
        :param info: SpiderInfo
        :param headers: self.request -> headers
        :param cookies: self.request -> cookies
        :param proxy_url: 代理池地址
        """
        self.info = info
        self.local = threading.local()
        self.headers = headers if headers is not None else getattr(self.__class__, "headers", None)
        self.cookies = cookies if cookies is not None else getattr(self.__class__, "cookies", None)
        self.catch_exceptions = getattr(self.__class__, "catch_exceptions", None)
        self.proxy_url = proxy_url if proxy_url is not None else getattr(self.__class__, "proxy_url", None)

    def get_request(self):
        return Request(proxy_url=self.proxy_url, headers=self.headers, cookies=self.cookies,
                       catch_exceptions=self.catch_exceptions)

    @property
    def request(self) -> BaseRequest:
        if not hasattr(self.local, 'request'):
            self.local.request = self.get_request()
        return self.local.request

    def start_cl(self, *args, **kwargs):
        pass

    def start(self, *args):
        parser = argparse.ArgumentParser()
        parser.add_argument("-cl", action="store_true", help="启用存量模式")
        parser.add_argument("-t", type=int, default=10, help="线程数量")
        parsed_args = parser.parse_args()  # 使用传入的 args，避免覆盖 sys.argv

        # 如果命令行没指定 -cl，则检查环境变量
        if not parsed_args.cl:
            cl_env = os.getenv('CL', '').lower()
            if cl_env in ('true', '1', 'yes', 'on'):
                parsed_args.cl = True

        if parsed_args.cl:
            logger.warning('cl=True')
            self.start_cl(thread_num=parsed_args.t)
            sys.exit(0)

    def page_list(self, *args):
        pass

    def page_detail(self, *args):
        pass

    def parse(self, *args):
        pass

class TaskManager(object):
    def __init__(self, unique_key='', redis:Optional[Redis]=None):
        self.unique_key = unique_key
        self.executor: Optional[ThreadPoolExecutor] = None
        self.executor_fs: list[Future] = []
        self.redis: Optional[Redis] = redis
        self.last_ttl_date: Optional[str] = None
        self.add_ttl = 43200
        self._active_tasks = 0
        self._lock = threading.Lock()
        self._all_done = threading.Event()
        self._st = None

    def _inc_task(self):
        if self._st is None:
            self._st = 1
        with self._lock:
            self._active_tasks += 1
            self._all_done.clear()

    def _dec_task(self):
        with self._lock:
            self._active_tasks -= 1
            if self._active_tasks == 0:
                self._all_done.set()

    @staticmethod
    def _generate_task_id(func: Callable, *args, **kwargs) -> str:
        func_name = getattr(func, '__name__', repr(func))
        arg_str = str((args, kwargs))
        md5_hash = get_md5(arg_str)
        return f"{func_name}:{md5_hash}"

    def _set_ttl(self, key):
        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        ttl_seconds = int((midnight - now).total_seconds()) + self.add_ttl
        self.redis.r.expire(key, ttl_seconds)

    def _make_cleanup_callback(self, key: str, task_id: str):
        def callback(future: Future):
            try:
                future.result()
                self.redis.r.sadd(key, task_id)
                self.redis.r.srem(key+'_tmp', task_id)
                logger.debug(f"Task succeeded: {task_id}")
            except Exception as exc:
                logger.warning(f"Task failed: {task_id}, Error: {exc}")
                try:
                    self.redis.r.srem(key+'_tmp', task_id)
                except Exception as redis_err:
                    logger.error(f"Failed to remove {task_id} from Redis: {redis_err}")
            finally:
                self._dec_task()

        return callback

    def unique_tmp_clean(self):
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        tmp_key = f"{self.unique_key}:{today_str}_tmp"
        try:
            deleted_count = self.redis.r.delete(tmp_key)
            if deleted_count:
                logger.info(f"Cleaned tmp key: {tmp_key}")
        except Exception as e:
            logger.error(f"Failed to clean tmp key {tmp_key}: {e}")

    def thread_func_unique_redis(self, thread_num, func, *args, **kwargs):
        if not self.unique_key:
            logger.error(f'未指定 unique_key')
            return False
        if self.redis is None:
            logger.error(f'失败 self.redis 没有定义')
            return False
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        today_key = f"{self.unique_key}:{today_str}"
        today_key_tmp = f"{self.unique_key}:{today_str}_tmp"
        task_id = self._generate_task_id(func, *args, **kwargs)

        if self.redis.r.sismember(today_key, task_id):
            logger.warning(f"Task already succeeded: {task_id}")
            return False

        if self.redis.r.sismember(today_key_tmp, task_id):
            logger.info(f"Task already running: {task_id}")
            return False

        added = self.redis.r.sadd(today_key_tmp, task_id)
        if not added:
            return False

        if self.last_ttl_date != today_str:
            self.redis.r.sadd(today_key, '0')
            self._set_ttl(today_key)
            self._set_ttl(today_key_tmp)
            self.last_ttl_date = today_str

        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=thread_num)

        try:
            self._inc_task()
            future = self.executor.submit(func, *args, **kwargs)
            future.add_done_callback(
                self._make_cleanup_callback(today_key, task_id)
            )
            return True
        except Exception as e:
            self._dec_task()
            logger.error(f"Submit failed {task_id} cleaning up: {e}")
            self.redis.r.srem(today_key_tmp, task_id)
            return False

    def thread_func(self, thread_num, func, *args, **kwargs):
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=thread_num)
        self.executor_fs.append(self.executor.submit(func, *args, **kwargs))

    def shutdown(self, wait=True, cancel_futures: bool = False):
        if self.executor is not None and not self.executor._shutdown:
            self.executor.shutdown(wait=wait, cancel_futures=cancel_futures)
            self.executor = None

    def wait_all_complete(self, timeout: Optional[float] = None):
        if self._st is None: self._all_done.set()
        self._all_done.wait(timeout=timeout)
        self.shutdown(False, True)
