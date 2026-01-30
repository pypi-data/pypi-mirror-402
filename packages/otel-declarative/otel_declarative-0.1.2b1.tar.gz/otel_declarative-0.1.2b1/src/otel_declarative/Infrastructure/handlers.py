import queue
import logging
from typing import cast
from logging.handlers import QueueHandler

class NonBlockingQueueHandler(QueueHandler):
    """
    非阻塞式异步队列处理器

    职责:
        1、扩展标准库 QueueHandler, 重写核心入队逻辑
        2、实现 '队列满时自动丢弃最旧日志' 策略, 确保新日志优先
        3、消除 queue.Full 异常的抛出, 保证 stderr 的清洁与业务线程的零阻塞
    """
    def enqueue(self, record: logging.LogRecord) -> None:
        """
        执行非阻塞入队操作

        逻辑:
            1、立即尝试入队
            2、若队列已满:
                a、尝试从队列头部移除一个最旧元素以腾出空间
                b、再次尝试将当前新记录入队
            3、若在极端并发竞争下第二次入队依然失败, 则静默丢弃当前记录, 不抛出任何错误

        :param record: 待处理的日志记录对象
        """
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            try:
                cast(queue.Queue, self.queue).get_nowait()
            except (queue.Empty, AttributeError):
                pass

            try:
                self.queue.put_nowait(record)
            except queue.Full:
                pass
