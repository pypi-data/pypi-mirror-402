from django.db import transaction

from celery_task_class import Task as BaseTask


class Task(BaseTask):
    def apply_async_on_commit(self, *args, **kwargs):
        return transaction.on_commit(
            lambda: self.apply_async(*args, **kwargs)
        )

    def delay_on_commit(self, *args, **kwargs):
        return transaction.on_commit(
            lambda: self.delay(*args, **kwargs)
        )


class TransactionRunMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)

        # Resolve run() via MRO
        run = getattr(cls, "run", None)

        if run and not getattr(run, "_is_atomic", False):

            @transaction.atomic
            def atomic_run(self, *args, **kwargs):
                return run(self, *args, **kwargs)

            atomic_run._is_atomic = True
            atomic_run.__name__ = run.__name__
            atomic_run.__doc__ = run.__doc__

            setattr(cls, "run", atomic_run)

        return cls


class TransactionTask(Task, metaclass=TransactionRunMeta):
    pass
