Added `as_task()` method:

```python
from celery import Celery
from celery import shared_task

from celery_task_class import Task

app = Celery(
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


class MyTask(Task):
    def run(self, *args, **kwargs):
        print('MyTask.run()')


@shared_task(base=MyTask, bind=True)
def run(self, *args, **kwargs):
    print('run() function task')
    super(self.__class__, self).run(*args, **kwargs)


class MyTask2(MyTask):
    def run(self, *args, **kwargs):
        print('MyTask2.run()')
        super().run(*args, **kwargs)


my_task = MyTask.as_task()
my_task2 = MyTask2.as_task()
```

Caller:

```python
from mycode import my_task

my_task.delay()
```
