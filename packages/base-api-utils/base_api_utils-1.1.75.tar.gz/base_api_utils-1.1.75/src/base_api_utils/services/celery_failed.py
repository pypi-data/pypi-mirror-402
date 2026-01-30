from django_celery_results.models import TaskResult
from celery import current_app
from datetime import datetime
from django.core.management.base import CommandError
import json


def list_failed_tasks(*, limit=50, task_name=None, since=None):
    queryset = TaskResult.objects.filter(status='FAILURE').order_by('-date_done')

    if task_name:
        queryset = queryset.filter(task_name=task_name)

    if since:
        try:
            since_date = datetime.fromisoformat(since)
            queryset = queryset.filter(date_done__gte=since_date)
        except ValueError:
            raise CommandError(
                f'Invalid date format: {since}. Use ISO format (YYYY-MM-DD)'
            )

    return queryset[:limit], queryset.count()


def get_task(task_id: str) -> TaskResult:
    try:
        return TaskResult.objects.get(task_id=task_id)
    except TaskResult.DoesNotExist:
        raise CommandError(f'Task with ID {task_id} not found.')


def retry_task(task: TaskResult):
    try:
        task_func = current_app.tasks.get(task.task_name)
        if not task_func:
            raise CommandError(f'Task {task.task_name} not found in registered tasks.')
    except Exception as e:
        raise CommandError(f'Error loading task {task.task_name}: {e}')

    try:
        args = json.loads(task.task_args) if task.task_args else []
        kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}

        if not isinstance(args, list):
            args = []
        if not isinstance(kwargs, dict):
            kwargs = {}
    except (json.JSONDecodeError, TypeError) as e:
        raise CommandError(f'Error parsing task arguments: {e}')

    return task_func.apply_async(args=args, kwargs=kwargs)


def retry_all_failed_tasks(*, limit=50, task_name=None, since=None):
    queryset = TaskResult.objects.filter(status='FAILURE').order_by('-date_done')

    if task_name:
        queryset = queryset.filter(task_name=task_name)

    if since:
        try:
            since_date = datetime.fromisoformat(since)
            queryset = queryset.filter(date_done__gte=since_date)
        except ValueError:
            raise CommandError(
                f'Invalid date format: {since}. Use ISO format (YYYY-MM-DD)'
            )

    tasks = queryset[:limit]

    results = {
        "total": queryset.count(),
        "processed": len(tasks),
        "success": 0,
        "errors": 0,
    }

    for task in tasks:
        try:
            retry_task(task)
            results["success"] += 1
        except Exception:
            results["errors"] += 1

    return results



def get_exception_summary(task: TaskResult) -> str:
    if not task.result:
        return 'No exception info'

    try:
        result = json.loads(task.result) if isinstance(task.result, str) else task.result

        if isinstance(result, dict):
            exc_type = result.get('exc_type')
            exc_message = result.get('exc_message')

            if exc_type:
                summary = exc_type.split('.')[-1]
                if exc_message:
                    msg = exc_message[:50]
                    if len(exc_message) > 50:
                        msg += '...'
                    summary += f': {msg}'
                return summary

        result_str = str(result)
        return result_str[:50] + ('...' if len(result_str) > 50 else '')
    except Exception:
        return 'Unable to parse exception'
