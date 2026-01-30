from __future__ import annotations
__all__ = ['MultiBackend']
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterator, NoReturn
from minfx.neptune_v2.exceptions import AllBackendsFailedError, BackendError, NeptuneMultiBackendClosedError
from minfx.neptune_v2.internal.backends.neptune_backend import NeptuneBackend
from minfx.neptune_v2.internal.utils.logger import get_logger
logger = get_logger()
MAX_RETRY_TIMEOUT_SECONDS = 30
HEALTH_CHECK_INTERVAL_SECONDS = 60
MAX_PARALLEL_WORKERS = 10
FAILURE_THRESHOLD = 3

@dataclass(frozen=True)
class Healthy:
    last_success_time: float

@dataclass(frozen=True)
class Failing:
    consecutive_failures: int
    last_error: Exception
    last_success_time: float

@dataclass(frozen=True)
class Degraded:
    consecutive_failures: int
    last_error: Exception
BackendHealth = Healthy | Failing | Degraded

def is_routable(health):
    return isinstance(health, (Healthy, Failing))

@dataclass
class BackendState:
    backend: NeptuneBackend
    index: int
    health: BackendHealth = field(default_factory=lambda: Healthy(last_success_time=time.time()))

def compute_success_health():
    return Healthy(last_success_time=time.time())

def compute_failure_health(current_health, error):
    if isinstance(current_health, Healthy):
        return Failing(consecutive_failures=1, last_error=error, last_success_time=current_health.last_success_time)
    elif isinstance(current_health, Failing):
        n = current_health.consecutive_failures
        if n < FAILURE_THRESHOLD - 1:
            return Failing(consecutive_failures=n + 1, last_error=error, last_success_time=current_health.last_success_time)
        else:
            return Degraded(consecutive_failures=n + 1, last_error=error)
    elif isinstance(current_health, Degraded):
        return Degraded(consecutive_failures=current_health.consecutive_failures + 1, last_error=error)
    return Degraded(consecutive_failures=1, last_error=error)

class MultiBackend(NeptuneBackend):

    def __init__(self, backends):
        self._backend_states = [BackendState(backend=b, index=i) for i, b in enumerate(backends)]
        self._init_common(len(backends))

    @classmethod
    def from_indexed_backends(cls, indexed_backends):
        instance = object.__new__(cls)
        instance._backend_states = [BackendState(backend=b, index=idx) for idx, b in indexed_backends]
        instance._init_common(len(indexed_backends))
        return instance

    def _init_common(self, num_backends):
        self._lock = threading.Lock()
        self._container_lock = None
        self._shutdown_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=min(num_backends, MAX_PARALLEL_WORKERS), thread_name_prefix='multi_backend')
        self._health_check_timer = None
        self._start_health_check_timer()

    def _check_not_closed(self):
        if self._shutdown_event.is_set():
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')

    def iterate_backends(self):
        for state in self._backend_states:
            yield state.backend

    @property
    def _is_single_backend(self):
        return len(self._backend_states) == 1

    def _raise_all_failed(self, errors):
        if self._is_single_backend and len(errors) == 1:
            raise errors[0].cause from None
        raise AllBackendsFailedError(errors)

    def set_container_lock(self, lock):
        self._container_lock = lock

    def _start_health_check_timer(self):
        self._health_check_timer = threading.Timer(HEALTH_CHECK_INTERVAL_SECONDS, self._check_degraded_backends)
        self._health_check_timer.daemon = True
        self._health_check_timer.start()

    def _check_degraded_backends(self):
        if self._shutdown_event.is_set():
            return
        with self._lock:
            degraded_info = [(state.index, state.backend) for state in self._backend_states if isinstance(state.health, Degraded)]
        for index, backend in degraded_info:
            backend_id = f'[backend {index}] ({backend.get_display_address()})'
            try:
                backend.health_ping()
                self._transition_on_success(index)
                logger.info(f'{backend_id} recovered')
            except Exception as e:
                logger.info(f'{backend_id} health check: still degraded ({e}). Will retry in {HEALTH_CHECK_INTERVAL_SECONDS}s')
        if not self._shutdown_event.is_set():
            self._start_health_check_timer()

    def _transition_on_success(self, index):
        with self._lock:
            pos = self._find_state_position(index)
            if pos is None:
                return
            current = self._backend_states[pos]
            old_health = current.health
            new_health = compute_success_health()
            self._backend_states[pos] = BackendState(backend=current.backend, index=current.index, health=new_health)
            if isinstance(old_health, Failing):
                logger.info(f'{self._backend_id(index)} health: Failing -> Healthy (recovered)')
            elif isinstance(old_health, Degraded):
                logger.info(f'{self._backend_id(index)} health: Degraded -> Healthy (recovered)')

    def _transition_on_failure(self, index, error):
        with self._lock:
            pos = self._find_state_position(index)
            if pos is None:
                return
            current = self._backend_states[pos]
            old_health = current.health
            new_health = compute_failure_health(old_health, error)
            self._backend_states[pos] = BackendState(backend=current.backend, index=current.index, health=new_health)
            if isinstance(old_health, Healthy) and isinstance(new_health, Failing):
                logger.warning(f'{self._backend_id(index)} health: Healthy -> Failing (first failure: {error})')
            elif isinstance(old_health, Failing) and isinstance(new_health, Failing):
                logger.warning(f'{self._backend_id(index)} health: Failing -> Failing ({new_health.consecutive_failures} consecutive failures)')
            elif isinstance(old_health, Failing) and isinstance(new_health, Degraded):
                logger.warning(f'{self._backend_id(index)} health: Failing -> Degraded ({new_health.consecutive_failures} consecutive failures). Will retry in {HEALTH_CHECK_INTERVAL_SECONDS}s')
            elif isinstance(old_health, Degraded) and isinstance(new_health, Degraded):
                logger.warning(f'{self._backend_id(index)} health: Degraded -> Degraded ({new_health.consecutive_failures} consecutive failures). Will retry in {HEALTH_CHECK_INTERVAL_SECONDS}s')

    def _get_routable_backends(self):
        with self._lock:
            routable = [s for s in self._backend_states if is_routable(s.health)]
            return routable if routable else list(self._backend_states)

    def _find_state_by_index(self, index):
        for state in self._backend_states:
            if state.index == index:
                return state
        return None

    def _find_state_position(self, index):
        for pos, state in enumerate(self._backend_states):
            if state.index == index:
                return pos
        return None

    def _backend_id(self, index):
        state = self._find_state_by_index(index)
        if state:
            return f'[backend {index}] ({state.backend.get_display_address()})'
        return f'[backend {index}]'

    def _format_health_status(self, health):
        if isinstance(health, Healthy):
            return 'healthy'
        elif isinstance(health, Failing):
            return f'failing, {health.consecutive_failures} errors'
        elif isinstance(health, Degraded):
            return f'degraded, {health.consecutive_failures} errors'
        return 'unknown'

    def mark_backend_disconnected(self, index, error=None):
        if error is None:
            error = Exception('Connection lost')
        with self._lock:
            pos = self._find_state_position(index)
            if pos is None:
                return
            current = self._backend_states[pos]
            if isinstance(current.health, Healthy):
                new_health = Degraded(consecutive_failures=FAILURE_THRESHOLD, last_error=error)
                self._backend_states[pos] = BackendState(backend=current.backend, index=current.index, health=new_health)

    def get_display_address(self):
        return self._backend_states[0].backend.get_display_address()

    @property
    def _client_config(self):
        return self._backend_states[0].backend._client_config

    def get_project(self, project_id):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_project(project_id)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
                logger.warning(f'{self._backend_id(state.index)} failed to get project: {e}')
        self._raise_all_failed(errors)

    def get_available_projects(self, workspace_id=None, search_term=None):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_available_projects(workspace_id, search_term)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_available_workspaces(self):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_available_workspaces()
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def create_run(self, project_id, git_info=None, custom_run_id=None, notebook_id=None, checkpoint_id=None, *, _external_id=None, _external_sys_id=None):
        self._check_not_closed()
        errors = []
        with self._lock:
            backends_snapshot = list(self._backend_states)
        if not backends_snapshot:
            raise AllBackendsFailedError([])
        if self._shutdown_event.is_set():
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        primary_state = backends_snapshot[0]
        primary_result = None
        total_backends = len(backends_snapshot)
        is_multi_backend = total_backends > 1
        if is_multi_backend:
            logger.info(f'Initializing run on {total_backends} backends...')
            logger.info(f'{self._backend_id(primary_state.index)}: initializing (primary)...')
        try:
            primary_result = primary_state.backend.create_run(project_id, git_info, custom_run_id, notebook_id, checkpoint_id, _external_id=_external_id, _external_sys_id=_external_sys_id)
            self._transition_on_success(primary_state.index)
            if is_multi_backend:
                logger.info(f'{self._backend_id(primary_state.index)}: initialized (primary)')
        except Exception as e:
            self._transition_on_failure(primary_state.index, e)
            error_type = type(e).__name__
            if is_multi_backend:
                logger.warning(f'{self._backend_id(primary_state.index)}: failed (primary) - {error_type}: {e}')
            else:
                logger.warning(f'{self._backend_id(primary_state.index)} failed to create run: {error_type}: {e}')
            errors.append(BackendError(backend_index=primary_state.index, cause=e))
            self._raise_all_failed(errors)
        remaining_backends = backends_snapshot[1:]
        if not remaining_backends:
            return primary_result

        def create_on_secondary(state):
            logger.info(f'{self._backend_id(state.index)}: initializing (secondary)...')
            try:
                result = state.backend.create_run(project_id, git_info, custom_run_id, notebook_id, checkpoint_id, _external_id=primary_result.id, _external_sys_id=primary_result.sys_id)
                self._transition_on_success(state.index)
                logger.info(f'{self._backend_id(state.index)}: initialized (secondary)')
                return (state.index, result, None)
            except Exception as e:
                self._transition_on_failure(state.index, e)
                error_type = type(e).__name__
                return (state.index, None, f'{error_type}: {e}')
        try:
            futures = {self._executor.submit(create_on_secondary, state): state for state in remaining_backends}
        except RuntimeError:
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            for future in as_completed(futures, timeout=MAX_RETRY_TIMEOUT_SECONDS):
                idx, result, error = future.result()
                if error:
                    logger.warning(f'{self._backend_id(idx)}: failed (secondary) - {error}')
                    errors.append(BackendError(backend_index=idx, cause=error))
        except FuturesTimeoutError:
            logger.warning(f'create_run() timed out after {MAX_RETRY_TIMEOUT_SECONDS}s')
        successful_count = 1 + len(remaining_backends) - len(errors)
        if errors:
            logger.warning(f'Run initialization completed: {successful_count}/{total_backends} backends ready')
        else:
            logger.info(f'Run initialization completed: {successful_count}/{total_backends} backends ready')
        return primary_result

    def create_model(self, project_id, key):
        self._check_not_closed()
        results = {}
        errors = []
        with self._lock:
            backends_snapshot = list(self._backend_states)

        def create_on_backend(state):
            try:
                result = state.backend.create_model(project_id, key)
                self._transition_on_success(state.index)
                return (state.index, result, None)
            except Exception as e:
                self._transition_on_failure(state.index, e)
                return (state.index, None, e)
        if self._shutdown_event.is_set():
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            futures = {self._executor.submit(create_on_backend, state): state for state in backends_snapshot}
        except RuntimeError:
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            for future in as_completed(futures, timeout=MAX_RETRY_TIMEOUT_SECONDS):
                idx, result, error = future.result()
                if error:
                    errors.append(BackendError(backend_index=idx, cause=error))
                else:
                    results[idx] = result
        except FuturesTimeoutError:
            pass
        if not results:
            self._raise_all_failed(errors)
        lowest_index = min(results.keys())
        return results[lowest_index]

    def create_model_version(self, project_id, model_id):
        self._check_not_closed()
        results = {}
        errors = []
        with self._lock:
            backends_snapshot = list(self._backend_states)

        def create_on_backend(state):
            try:
                result = state.backend.create_model_version(project_id, model_id)
                self._transition_on_success(state.index)
                return (state.index, result, None)
            except Exception as e:
                self._transition_on_failure(state.index, e)
                return (state.index, None, e)
        if self._shutdown_event.is_set():
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            futures = {self._executor.submit(create_on_backend, state): state for state in backends_snapshot}
        except RuntimeError:
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            for future in as_completed(futures, timeout=MAX_RETRY_TIMEOUT_SECONDS):
                idx, result, error = future.result()
                if error:
                    errors.append(BackendError(backend_index=idx, cause=error))
                else:
                    results[idx] = result
        except FuturesTimeoutError:
            pass
        if not results:
            self._raise_all_failed(errors)
        lowest_index = min(results.keys())
        return results[lowest_index]

    def get_metadata_container(self, container_id, expected_container_type):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_metadata_container(container_id, expected_container_type)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def create_checkpoint(self, notebook_id, jupyter_path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.create_checkpoint(notebook_id, jupyter_path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def execute_operations(self, container_id, container_type, operations, operation_storage):
        self._check_not_closed()
        backend_errors = []
        results = []
        backends_to_use = self._get_routable_backends()
        logger.debug(f'Flushing {len(operations)} operations to {len(backends_to_use)} backend(s)')

        def execute_on_backend(state):
            try:
                result = state.backend.execute_operations(container_id, container_type, operations, operation_storage)
                self._transition_on_success(state.index)
                return (state.index, result, None)
            except Exception as e:
                self._transition_on_failure(state.index, e)
                return (state.index, None, e)
        if self._shutdown_event.is_set():
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        try:
            futures = {self._executor.submit(execute_on_backend, state): state for state in backends_to_use}
        except RuntimeError:
            raise NeptuneMultiBackendClosedError('MultiBackend has been closed')
        for future in as_completed(futures):
            idx, result, error = future.result()
            if error:
                logger.warning(f'{self._backend_id(idx)} failed: {error}')
                backend_errors.append(BackendError(backend_index=idx, cause=error))
            else:
                results.append(result)
        if not results:
            self._raise_all_failed(backend_errors)
        max_processed = max((r[0] for r in results))
        for processed, partial_errors in results:
            for err in partial_errors:
                logger.debug(f'Partial error from successful backend: {err}')
        logger.debug(f'Buffer flush complete: {max_processed} operations processed')
        return (max_processed, backend_errors)

    def get_attributes(self, container_id, container_type):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_attributes(container_id, container_type)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
                logger.warning(f'{self._backend_id(state.index)} failed to get attributes: {e}')
        self._raise_all_failed(errors)

    def download_file(self, container_id, container_type, path, destination=None, progress_bar=None):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.download_file(container_id=container_id, container_type=container_type, path=path, destination=destination, progress_bar=progress_bar)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def download_file_set(self, container_id, container_type, path, destination=None, progress_bar=None):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.download_file_set(container_id=container_id, container_type=container_type, path=path, destination=destination, progress_bar=progress_bar)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_float_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_float_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_int_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_int_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_bool_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_bool_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_file_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_file_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_string_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_string_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_datetime_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_datetime_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_artifact_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_artifact_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def list_artifact_files(self, project_id, artifact_hash):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.list_artifact_files(project_id, artifact_hash)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_float_series_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_float_series_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_string_series_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_string_series_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_string_set_attribute(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_string_set_attribute(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def download_file_series_by_index(self, container_id, container_type, path, index, destination, progress_bar):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.download_file_series_by_index(container_id, container_type, path, index, destination, progress_bar)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_image_series_values(self, container_id, container_type, path, offset, limit):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_image_series_values(container_id, container_type, path, offset, limit)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_string_series_values(self, container_id, container_type, path, offset, limit):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_string_series_values(container_id, container_type, path, offset, limit)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_float_series_values(self, container_id, container_type, path, offset, limit):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.get_float_series_values(container_id, container_type, path, offset, limit)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def get_run_url(self, run_id, workspace, project_name, sys_id):
        return self._backend_states[0].backend.get_run_url(run_id, workspace, project_name, sys_id)

    def get_all_run_urls(self, run_id, workspace, project_name, sys_id):
        urls = []
        for state in self._backend_states:
            try:
                url = state.backend.get_run_url(run_id, workspace, project_name, sys_id)
                urls.append(url)
            except Exception:
                pass
        return urls

    def get_project_url(self, project_id, workspace, project_name):
        return self._backend_states[0].backend.get_project_url(project_id, workspace, project_name)

    def get_model_url(self, model_id, workspace, project_name, sys_id):
        return self._backend_states[0].backend.get_model_url(model_id, workspace, project_name, sys_id)

    def get_model_version_url(self, model_version_id, model_id, workspace, project_name, sys_id):
        return self._backend_states[0].backend.get_model_version_url(model_version_id, model_id, workspace, project_name, sys_id)

    def fetch_atom_attribute_values(self, container_id, container_type, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.fetch_atom_attribute_values(container_id, container_type, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def search_leaderboard_entries(self, project_id, types=None, query=None, columns=None, limit=None, sort_by='sys/creation_time', ascending=False, progress_bar=None):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.search_leaderboard_entries(project_id=project_id, types=types, query=query, columns=columns, limit=limit, sort_by=sort_by, ascending=ascending, progress_bar=progress_bar)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def list_fileset_files(self, attribute, container_id, path):
        self._check_not_closed()
        backends_to_try = self._get_routable_backends()
        errors = []
        for state in backends_to_try:
            try:
                result = state.backend.list_fileset_files(attribute, container_id, path)
                self._transition_on_success(state.index)
                return result
            except Exception as e:
                self._transition_on_failure(state.index, e)
                errors.append(BackendError(backend_index=state.index, cause=e))
        self._raise_all_failed(errors)

    def close(self):
        self._shutdown_event.set()
        if self._health_check_timer:
            self._health_check_timer.cancel()
        self._executor.shutdown(wait=True)
        is_multi_backend = len(self._backend_states) > 1
        if is_multi_backend:
            logger.info('Closing connection to backends...')
        for state in self._backend_states:
            health_status = self._format_health_status(state.health)
            if is_multi_backend:
                logger.info(f'{self._backend_id(state.index)}: closing ({health_status})...')
            try:
                state.backend.close()
                if is_multi_backend:
                    logger.info(f'{self._backend_id(state.index)}: closed')
            except Exception as e:
                error_type = type(e).__name__
                if is_multi_backend:
                    logger.warning(f'{self._backend_id(state.index)}: failed to close - {error_type}: {e}')
                else:
                    logger.warning(f'Error closing backend {state.index}: {error_type}: {e}')