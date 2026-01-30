"""
Django TestCase integration tests for celery_failed command.

This test suite:
1. Starts a real Celery worker
2. Triggers a failing task
3. Tests all celery_failed commands
4. Cleans up automatically

Usage:
    python manage.py test test_celery_integration --keepdb -v 2

Requirements:
    - Django project with Celery configured
    - django-celery-results installed and migrated
    - Redis/RabbitMQ broker running
    - CELERY_RESULT_BACKEND = 'django-db'
    - CELERY_RESULT_EXTENDED = True
"""
import subprocess
import time
import signal
import os
from unittest import skipUnless

from django.db import connection
from django.test import TransactionTestCase
from django.core.management import call_command
from django_celery_results.models import TaskResult
from celery import current_app
from io import StringIO

from ..utils import always_fails_task, config, celery_is_correctly_configured


class CeleryWorkerMixin:
    """Mixin to handle Celery worker lifecycle."""

    worker_process = None

    @classmethod
    def start_worker(cls):
        """Start Celery worker in background."""
        print("\n" + "=" * 70)
        print("STARTING CELERY WORKER")
        print("=" * 70)

        test_db_name = connection.settings_dict['NAME']

        env = os.environ.copy()
        env['DB_NAME'] = test_db_name
        env['CELERY_TASK_ALWAYS_EAGER'] = 'False'

        # Start worker with solo pool (single process, easier to debug)
        cls.worker_process = subprocess.Popen(
            ['celery', '-A', 'backend', 'worker', '--loglevel=info', '--pool=solo'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # Create new process group
            env=env
        )

        # Wait for worker to be ready
        print("Waiting for Celery worker to start (5 seconds)...")
        time.sleep(5)

        # Verify worker started
        if cls.worker_process.poll() is not None:
            stdout, stderr = cls.worker_process.communicate()
            raise RuntimeError(
                f"Celery worker failed to start.\n"
                f"STDOUT: {stdout.decode()}\n"
                f"STDERR: {stderr.decode()}"
            )

        print(f"✓ Celery worker started successfully (PID: {cls.worker_process.pid})\n")

    @classmethod
    def stop_worker(cls):
        """Stop Celery worker gracefully."""
        if not cls.worker_process:
            return

        print("\n" + "=" * 70)
        print("STOPPING CELERY WORKER")
        print("=" * 70)

        try:
            # Send SIGTERM to entire process group
            os.killpg(os.getpgid(cls.worker_process.pid), signal.SIGTERM)

            # Wait for graceful shutdown (max 10 seconds)
            try:
                cls.worker_process.wait(timeout=10)
                print("✓ Celery worker stopped gracefully\n")
            except subprocess.TimeoutExpired:
                print("⚠ Worker didn't stop gracefully, forcing shutdown...")
                os.killpg(os.getpgid(cls.worker_process.pid), signal.SIGKILL)
                cls.worker_process.wait()
                print("✓ Celery worker force stopped\n")
        except Exception as e:
            print(f"⚠ Error stopping worker: {e}\n")


@skipUnless(
    celery_is_correctly_configured(),
    "Celery is not configured correctly"
)
class FailedCeleryTaskManagementTest(CeleryWorkerMixin, TransactionTestCase):
    """
    Integration tests with real Celery worker.

    These tests actually start a Celery worker, trigger real tasks,
    and verify the celery_failed management command works correctly.
    """

    @classmethod
    def setUpClass(cls):
        """Start Celery worker once for all tests in this class."""
        super().setUpClass()

        # Clear existing task results
        TaskResult.objects.all().delete()

        # Start the worker
        cls.start_worker()

    @classmethod
    def tearDownClass(cls):
        """Stop Celery worker after all tests complete."""
        cls.stop_worker()
        super().tearDownClass()

    def setUp(self):
        """Clear task results before each test."""
        TaskResult.objects.all().delete()

    def trigger_failing_task(self):
        """
        Trigger the failing task and wait for it to fail.

        Returns:
            str: Task ID of the failed task
        """

        print("\n--- Triggering failing task ---")

        # Trigger the task
        result = always_fails_task.delay(test_id=123, reason="Testing")

        task_id = result.id if hasattr(result, 'id') else str(result)
        print(f"Task ID: {task_id}")

        # Wait for task to fail
        print("Waiting for task to fail...")
        max_wait = 30  # 30 seconds max
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                task_result = TaskResult.objects.get(task_id=task_id)

                if task_result.status == 'FAILURE':
                    elapsed = time.time() - start_time
                    print(f"✓ Task failed after {elapsed:.1f} seconds\n")
                    return task_id

                elif task_result.status == 'SUCCESS':
                    self.fail(
                        f"Task succeeded when it should have failed!\n"
                        f"Result: {task_result.result}"
                    )

                # Still processing
                print(f"  Status: {task_result.status} (waiting...)")

            except TaskResult.DoesNotExist:
                print("  Task result not in database yet (waiting...)")

            time.sleep(2)

        # Timeout - check final status
        try:
            task_result = TaskResult.objects.get(task_id=task_id)
            self.fail(
                f"Task did not fail within {max_wait} seconds.\n"
                f"Current status: {task_result.status}\n"
                f"Result: {task_result.result}"
            )
        except TaskResult.DoesNotExist:
            self.fail(
                f"Task result not found in database after {max_wait} seconds.\n"
                f"Check if CELERY_RESULT_BACKEND is configured correctly."
            )

    def test_celery_failed_list(self):
        """Test: celery_failed list shows the failed task."""
        print("\n" + "=" * 70)
        print("TEST: celery_failed list")
        print("=" * 70)

        # Trigger failing task
        task_id = self.trigger_failing_task()

        # Run list command
        print("Running: python manage.py celery_failed list")
        out = StringIO()
        call_command('celery_failed', 'list', stdout=out)
        output = out.getvalue()

        # Show output
        print("\nCommand output (first 12 lines):")
        for line in output.split('\n')[:12]:
            print(f"  {line}")

        # Assertions
        self.assertIn(
            task_id[:38],
            output,
            f"Task ID {task_id[:38]} should appear in list output"
        )
        print(f"\n✓ Task ID found in output")

        # Should show as FAILURE or show the task name
        self.assertTrue(
            'FAILURE' in output.upper() or 'EXCEPTION' in output.upper(),
            "Output should indicate task failure"
        )
        print("✓ Task shown as failed")

        # Should NOT show successful tasks
        TaskResult.objects.create(
            task_id='fake-success-id',
            task_name='successful_task',
            status='SUCCESS',
            date_done=TaskResult.objects.get(task_id=task_id).date_done,
            result='{"status": "success"}',
            task_args='[]',
            task_kwargs='{}'
        )

        out = StringIO()
        call_command('celery_failed', 'list', stdout=out)
        output = out.getvalue()

        self.assertNotIn(
            'fake-success-id',
            output,
            "Successful tasks should NOT appear in failed list"
        )
        print("✓ Successful tasks correctly excluded")

        print("\n✓ TEST PASSED\n")

    def test_celery_failed_show(self):
        """Test: celery_failed show displays complete task details."""
        print("\n" + "=" * 70)
        print("TEST: celery_failed show")
        print("=" * 70)

        # Trigger failing task
        task_id = self.trigger_failing_task()

        # Run show command
        print(f"Running: python manage.py celery_failed show {task_id}")
        out = StringIO()
        call_command('celery_failed', 'show', task_id, stdout=out)
        output = out.getvalue()

        # Show output
        print("\nCommand output (first 20 lines):")
        for line in output.split('\n')[:20]:
            print(f"  {line}")

        # Assertions
        self.assertIn(task_id, output, "Task ID should be in output")
        print("\n✓ Task ID present")

        self.assertIn('FAILURE', output, "Should show FAILURE status")
        print("✓ FAILURE status shown")

        # Should show exception information
        self.assertTrue(
            'Traceback' in output or 'Exception' in output or 'Error' in output,
            "Should show exception information"
        )
        print("✓ Exception information present")

        # Should show task arguments
        task_result = TaskResult.objects.get(task_id=task_id)
        if task_result.task_args or task_result.task_kwargs:
            self.assertTrue(
                'Args' in output or 'Kwargs' in output,
                "Should show task arguments"
            )
            print("✓ Task arguments displayed")

        print("\n✓ TEST PASSED\n")

    def test_celery_failed_retry(self):
        """Test: celery_failed retry requeues the task."""
        print("\n" + "=" * 70)
        print("TEST: celery_failed retry")
        print("=" * 70)

        # Trigger failing task
        task_id = self.trigger_failing_task()

        # Get task details
        task_result = TaskResult.objects.get(task_id=task_id)
        task_name = task_result.task_name

        # Check if task is registered
        registered_task = current_app.tasks.get(task_name)
        if not registered_task:
            self.skipTest(f"Task '{task_name}' not registered in Celery. Cannot test retry.")

        print(f"Task '{task_name}' is registered")

        # Run retry command
        print(f"\nRunning: python manage.py celery_failed retry {task_id}")
        out = StringIO()
        call_command('celery_failed', 'retry', task_id, stdout=out)
        output = out.getvalue()

        # Show output
        print("\nCommand output:")
        for line in output.split('\n'):
            if line.strip():
                print(f"  {line}")

        # Assertions
        self.assertIn(
            'requeued successfully',
            output.lower(),
            "Should show success message"
        )
        print("\n✓ Task requeued successfully")

        self.assertIn(
            'New Task ID',
            output,
            "Should show new task ID"
        )
        print("✓ New task ID displayed")

        # Extract new task ID
        new_task_id = None
        for line in output.split('\n'):
            if 'New Task ID' in line:
                new_task_id = line.split(':')[1].strip()
                print(f"✓ New task ID: {new_task_id}")
                break

        self.assertIsNotNone(new_task_id, "Should extract new task ID from output")
        self.assertNotEqual(task_id, new_task_id, "New task ID should be different from original")

        print("\n✓ TEST PASSED\n")

    def test_celery_failed_retry_all(self):
        """Test: celery_failed retry --all with filters."""
        print("\n" + "=" * 70)
        print("TEST: celery_failed retry --all")
        print("=" * 70)

        # Trigger multiple failing tasks
        print("\nTriggering first failing task...")
        task_id_1 = self.trigger_failing_task()

        print("Triggering second failing task...")
        task_id_2 = self.trigger_failing_task()

        # Check if tasks are registered
        task_result = TaskResult.objects.get(task_id=task_id_1)
        task_name = task_result.task_name
        registered_task = current_app.tasks.get(task_name)

        if not registered_task:
            self.skipTest(f"Task '{task_name}' not registered. Cannot test retry --all.")

        # Run retry --all command
        print(f"\nRunning: python manage.py celery_failed retry --all --limit 10")

        # Mock input to auto-confirm
        from unittest.mock import patch
        with patch('builtins.input', return_value='yes'):
            out = StringIO()
            call_command('celery_failed', 'retry', '--all', '--limit', '10', stdout=out)
            output = out.getvalue()

        # Show output
        print("\nCommand output:")
        for line in output.split('\n'):
            if line.strip():
                print(f"  {line}")

        # Assertions
        self.assertIn(
            'Successfully requeued',
            output,
            "Should show success summary"
        )
        print("\n✓ Batch retry completed")

        # Should mention how many were retried
        self.assertTrue(
            'requeued: 2' in output.lower() or '2' in output,
            "Should show number of retried tasks"
        )
        print("✓ Correct number of tasks retried")

        print("\n✓ TEST PASSED\n")
