import joblib
import typing
import inspect

import cvtda.logging
import cvtda.dumping

def parallel(
    function,
    iterable,
    n_jobs: int = -1,
    return_as: str = 'list',
    num_parameters: typing.Optional[str] = None
):
    def init_worker(logger, dumper):
        cvtda.logging.BaseLogger.current_logger = logger
        cvtda.dumping.BaseDumper.current_dumper = dumper

    initargs = (cvtda.logging.logger(), cvtda.dumping.dumper())
    num_parameters = num_parameters or len(inspect.signature(function).parameters)
    with joblib.parallel_backend(backend = 'loky', initializer = init_worker, initargs = initargs):
        if num_parameters == 1:
            return joblib.Parallel(return_as = return_as, n_jobs = n_jobs)(
                joblib.delayed(function)(item) for item in iterable
            )
        else:
            return joblib.Parallel(return_as = return_as, n_jobs = n_jobs)(
                joblib.delayed(function)(*item) for item in iterable
            )
