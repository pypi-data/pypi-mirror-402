from importlib import import_module

from arq import func


def _load_task_modules(task_packages):
    modules = []
    for pkg in task_packages:
        modules.append(import_module(f"{pkg}.tasks"))
    return modules


def _normalize_fn_to_dotted(fn):
    if isinstance(fn, str):
        return fn
    return "{}.{}".format(fn.__module__, getattr(fn, "__name__", fn.__class__.__name__))


def collect_cron_jobs_and_functions(task_packages):
    cron_jobs = []
    functions = []

    for module in _load_task_modules(task_packages):
        # also allow optional explicit FUNCTIONS = [callable, ...]
        extra_funcs = getattr(module, "FUNCTIONS", [])
        for fn in extra_funcs:
            # replace name so if we have two functions with the same name in different
            # modules, it still works
            functions.append(func(_normalize_fn_to_dotted(fn)))

        # Each tasks.py should define CRON_JOBS = [cron(...), ...]
        jobs = getattr(module, "CRON_JOBS", [])

        for job in jobs:
            # Set ID of the job, used to enforce job uniqueness
            if not job.job_id:
                job.job_id = job.name

            # replace name so if we have two functions with the same name in different
            # modules, it still works
            job.name = f"cron:{_normalize_fn_to_dotted(job.coroutine)}"
            cron_jobs.append(job)

    return cron_jobs, functions
