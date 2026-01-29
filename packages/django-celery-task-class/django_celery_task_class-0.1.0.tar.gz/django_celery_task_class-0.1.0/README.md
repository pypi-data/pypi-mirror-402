`Task`

Adds `apply_async_on_commit()` and `delay_on_commit()` methods to Task class. 

`TransactionTask`

Class that has `run()` wrapped in @transaction.atomic.

```python
from django_celery_task_class import Task
from django_celery_task_class import TransactionTask

class MyTask(Task):
    def run(self, *args, **kwargs):
        pass


class MyTransactionTask(TransactionTask):
    def run(self, *args, **kwargs):
        # Runs inside a @transaction.atomic
        pass


my_task = MyTask.as_task()
my_transaction_task = MyTransactionTask.as_task()
```

Caller:

```python
from mycode import my_task

my_task.delay_on_commit()
my_transaction_task.apply_async_on_commit()
```
