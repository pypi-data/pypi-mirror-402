from opt_flow.trajectory._base import BaseTrajectory
from typing import Optional, List
from opt_flow.acceptance import BaseAcceptance
from opt_flow.structure import BaseIndividual
from multiprocessing import Queue, shared_memory, Event, Process
from opt_flow.trajectory.interfaces import Decoder
from opt_flow.structure import Data
from queue import Empty, Full
from opt_flow.stopping import OrStopping
import struct
import time
from opt_flow.trajectory.interfaces import Encoder
import msgpack
from opt_flow.utils.logger import _configure_log
import logging
from opt_flow.config import config, configure
from opt_flow.stopping import BaseStopping, ParallelTrajectoryStopping, TimeLimitStopping
from opt_flow.callback.trajectory import ParallelPollingUpdate
from opt_flow.callback.stopping import ParallelTrajectoryTimeStoppingUpdate
from opt_flow.callback import Callback 
from typing import List
from opt_flow.stats import StatsRecord

class ParallelTrajectory(BaseTrajectory):
    """
    Executes multiple trajectory operators in parallel on a given individual.

    This class allows concurrent execution of multiple `BaseTrajectories` instances
    on the same individual using multiprocessing. An encoder and decoder are required
    to serialize and deserialize individuals for shared memory communication. A central
    arbiter monitors and updates the best individual according to a given acceptance
    criterion.

    Attributes
    ----------
    trajectories : List[BaseTrajectories]
        The trajectory operators to execute in parallel.
    encoder : Encoder
        Encodes a individual into a serialized format for shared memory communication.
    decoder : Decoder
        Decodes a serialized individual back into a `Baseindividual` instance.
    acceptance : BaseAcceptance
        Acceptance criterion used to select the best individual among parallel trajectories.
    polling_interval : float
        Time interval (in seconds) between polling shared memory for updates.
    min_polling_interval : float
        Minimum allowed polling interval.
    max_polling_interval : float
        Maximum allowed polling interval.
    polling_delta : float
        Amount to adjust the polling interval dynamically.
    data : Data
        The data associated with the individuals being improved.
    """

    def __init__(
        self,
        data: Data,
        trajectories: List[BaseTrajectory],
        encoder: Encoder,
        decoder: Decoder,
        polling_interval: float,
        min_polling_interval: float,
        max_polling_interval: float,
        polling_delta: float,
        early_stopping: bool = False,
        acceptance: Optional[BaseAcceptance] = None,
        stopping_criterion: Optional[BaseStopping] = None,
        callbacks: Optional[List[Callback]] = None,
    ):
        if not config.parallel:
            raise RuntimeError("Cannot execute a parallel algorithm without setting parallel to True.")
        self.trajectories = trajectories
        self.acceptance = acceptance or config.default_acceptance
        self.encoder = encoder
        self.decoder = decoder
        self.polling_interval = polling_interval
        self.min_polling_interval = min_polling_interval
        self.max_polling_interval = max_polling_interval
        self.polling_delta = polling_delta
        self.data = data
        if early_stopping:
            new_stopping = OrStopping([stopping_criterion, ParallelTrajectoryStopping(min_polling_interval, max_polling_interval, polling_delta, polling_interval)])
            new_callbacks = []
            if callbacks:
                new_callbacks.extend(callbacks)
                new_callbacks.append(ParallelPollingUpdate(self))
            else:
                new_callbacks.append(ParallelPollingUpdate(self))
        else:
            new_stopping = stopping_criterion
        super().__init__(new_stopping, new_callbacks)

    def _update_stoppings(self):
        for trajectory in self.trajectories:
            stopping = TimeLimitStopping(self.polling_interval)
            trajectory._stopping_criterion = OrStopping(
                [
                    trajectory._stopping_criterion,
                    stopping,
                ]
            )
            self._callbacks.append(ParallelTrajectoryTimeStoppingUpdate(self, stopping))

    def _unupdate_stoppings(self):
        for trajectory in self.trajectories:
            stopping_criterion: OrStopping = trajectory._stopping_criterion
            if len(stopping_criterion.strategies) > 2:
                stopping_criterion.strategies.pop()
            else:
                stopping_criterion = stopping_criterion.strategies[0]
            trajectory._stopping_criterion = stopping_criterion
            self._callbacks.pop()
            self._callbacks.pop()

    def iterate(self, individual: BaseIndividual):
        """
        Applies all registered trajectories in parallel to the given individual,
        updating the individual to the best candidate according to the acceptance
        criterion.

        This method launches separate worker processes for each trajectory
        operator, along with an arbiter process that monitors and maintains
        the best individual. Shared memory and queues are used for inter-process
        communication. The process continues until the stopping criterion is met.

        Parameters
        ----------
        individual : BaseIndividual
            The individual to improve. This object will be updated in-place with
            the best result found by the parallel trajectories.
        """
        self._update_stoppings()
        individual_queue = Queue()
        stop_event = Event()
        tracker_queue = Queue()

        initial_encoded_sol = self.encoder.encode(individual)
        serialized = msgpack.packb(initial_encoded_sol, use_bin_type=True)
        config_dict = config.to_dict()

        extra_space = max(int(len(serialized) * 0.1), 1024)
        buffer_size = (len(serialized) + extra_space + 7) & ~7
        shared_mem = shared_memory.SharedMemory(create=True, size=buffer_size)
        shared_bytes = memoryview(shared_mem.buf)

        struct.pack_into("<I", shared_bytes, 0, len(serialized))
        shared_bytes[4 : 4 + len(serialized)] = serialized
        shared_bytes[4 + len(serialized) :] = b"\x00" * (
            buffer_size - 4 - len(serialized)
        )

        arbiter = Process(
            target=self._arbiter_process,
            args=(individual_queue, tracker_queue, shared_mem.name, buffer_size, stop_event, config_dict),
        )

        workers = [
            Process(
                target=self._trajectory_worker,
                args=(
                    trajectory,
                    initial_encoded_sol,
                    shared_mem.name,
                    buffer_size,
                    individual_queue,
                    stop_event,
                    config_dict
                ),
            )
            for trajectory in self.trajectories
        ]

        try:
            arbiter.start()
            for w in workers:
                w.start()
                

            while not stop_event.is_set():
                stored_length = struct.unpack_from("<I", shared_bytes, 0)[0]
                if stored_length > 0:
                    final_data = bytes(shared_bytes[4 : 4 + stored_length])
                    final_dict = msgpack.unpackb(
                        final_data, raw=False, strict_map_key=False
                    )
                    best_individual = self.decoder.decode(self.data, final_dict)
                    improved = best_individual != individual
                    if not self._should_continue(best_individual, improved, self.short_name):
                        stop_event.set()
                        break
                    individual.overwrite_with(best_individual)

                time.sleep(self.polling_interval)

            for w in workers:
                w.join(timeout=2)
                if w.is_alive():
                    w.terminate()
                    w.join(timeout=1)
                    if w.is_alive():
                        w.kill()
            try:
                while True:
                    rec = tracker_queue.get(timeout=0.01)
                    self._tracker._record(rec)
            except Empty:
                pass
            arbiter.join(timeout=10)
            if arbiter.is_alive():
                arbiter.terminate()
                arbiter.join(timeout=1)
                if arbiter.is_alive():
                    arbiter.kill()
        except Exception as e:
            logging.error(e)
            stop_event.set()
            for w in workers:
                if w.is_alive():
                    w.terminate()
                    w.join()
                    if w.is_alive():
                        w.kill()
                        
            if arbiter.is_alive():
                arbiter.terminate()
                arbiter.join()
                if arbiter.is_alive():
                    arbiter.kill()

        finally:
            stored_length = struct.unpack_from("<I", shared_bytes, 0)[0]
            if stored_length > 0:
                final_data = bytes(shared_bytes[4 : 4 + stored_length])
                final_dict = msgpack.unpackb(
                    final_data, raw=False, strict_map_key=False
                )
                final_individual = self.decoder.decode(self.data, final_dict)
                individual.overwrite_with(final_individual)

            shared_bytes.release()  
            shared_mem.close()
            shared_mem.unlink()
            self._unupdate_stoppings()
            

    def _arbiter_process(
        self, individual_queue: Queue, tracker_queue: Queue, shared_mem_name: str, size: int, stop_event, config_dict
    ):
        _configure_log()
        configure(config_dict)
        shm = shared_memory.SharedMemory(name=shared_mem_name)
        shared_bytes = memoryview(shm.buf)

        try:
            while not stop_event.is_set():
                try:
                    new_individual_dict, new_name = individual_queue.get(timeout=0.1)
                    new_individual = self.decoder.decode(self.data, new_individual_dict) 

                    stored_length = struct.unpack_from("<I", shared_bytes, 0)[0]
                    current_best = None
                    if stored_length > 0 and stored_length <= size - 4:
                        try:
                            data = shared_bytes[4 : 4 + stored_length]
                            try:
                                current_best_dict = msgpack.unpackb(
                                    data, raw=False, strict_map_key=False
                                )
                            finally:
                                data.release()
                            current_best = self.decoder.decode(
                                self.data, current_best_dict
                            )
                        except Exception:
                            current_best = None

                    if current_best is None or self.acceptance.compare_individuals(
                        current_best, new_individual
                    ):
                        self._record_workers(new_name, True, new_individual, tracker_queue)
                        serialized = msgpack.packb(new_individual_dict, use_bin_type=True)
                        total_length = len(serialized)

                        if total_length <= size - 4:
                            struct.pack_into("<I", shared_bytes, 0, total_length)

                            shared_bytes[4 : 4 + total_length] = serialized

                            prev_length = (
                                stored_length if current_best is not None else 0
                            )
                            if total_length < prev_length:
                                shared_bytes[4 + total_length : 4 + prev_length] = (
                                    b"\x00" * (prev_length - total_length)
                                )
                        else:
                            self._record_workers(new_name, False, new_individual, tracker_queue)
                        
                except Empty:
                    continue
                except Exception as e:
                    logging.error(e)
                    continue
        finally:
            shared_bytes.release()
            shm.close()

    def _trajectory_worker(
        self,
        trajectory: BaseTrajectory,
        initial_individual_dict,
        shared_mem_name: str,
        size: int,
        individual_queue: Queue,
        stop_event,
        config_dict,
    ):
        _configure_log()
        configure(config_dict)
        shm = shared_memory.SharedMemory(name=shared_mem_name)
        shared_bytes = memoryview(shm.buf)

        try:
            local_individual = self.decoder.decode(self.data, initial_individual_dict)
            while not stop_event.is_set():
                try:
                    trajectory.iterate(local_individual)
                    individual_dict = self.encoder.encode(local_individual)
                    try:
                        individual_queue.put((individual_dict, trajectory.short_name), block=False)
                    except Full:
                        pass

                    stored_length = struct.unpack_from("<I", shared_bytes, 0)[0]
                    if stored_length > 0 and stored_length <= size - 4:
                        serialized_data = memoryview(
                            shared_bytes[4 : 4 + stored_length]
                        )
                        try:
                            current_best_dict = msgpack.unpackb(
                                serialized_data, raw=False, strict_map_key=False
                            )
                        finally:
                            serialized_data.release()
                        local_individual = self.decoder.decode(
                            self.data, current_best_dict
                        )

                except Exception as e:
                    logging.error(e)
                    continue
        finally:
            shared_bytes.release()
            shm.close()

    def _record_workers(self, name: str, improved: bool, individual: BaseIndividual, tracker_queue: Queue):
        record = StatsRecord(individual.get_objective(), improved, None, name)
        tracker_queue.put(record)
