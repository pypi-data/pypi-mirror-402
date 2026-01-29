from functools import update_wrapper

from celery import Task as BaseTask
from celery import shared_task


class Task(BaseTask):
    @classmethod
    def get_task_decorator(cls):
        return shared_task(bind=True, base=cls)

    @classmethod
    def as_task(cls):
        def run(self, *args, **kwargs):
            print('task created with as_task()')
            return super(self.__class__, self).run(*args, **kwargs)

        update_wrapper(run, cls, updated=())
        return cls.get_task_decorator()(run)
