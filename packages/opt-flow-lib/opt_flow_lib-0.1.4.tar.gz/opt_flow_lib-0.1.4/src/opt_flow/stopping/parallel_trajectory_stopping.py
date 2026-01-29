from opt_flow.stopping._base import BaseStopping 
from opt_flow.callback import CallbackArgs

class ParallelTrajectoryStopping(BaseStopping):
    __dependencies__ = ["iterations_without_improvement", "time_without_improvements", "iteration", "total_improvements", "individual", "current_best"]
    
    def __init__(self, min_polling_interval: float, max_polling_interval: float, polling_delta: float, polling_interval: float, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_polling_interval = min_polling_interval
        self.max_polling_interval = max_polling_interval
        self.polling_delta = polling_delta
        self.polling_interval = polling_interval
        
    def _stop(self, args: CallbackArgs) -> bool:
        simulated_polling_interval = self.polling_interval
        if self.polling_delta != 0:
            accepted_tags = [moment[2] for moment in args.history if moment[1] == 'parallel_improvement']
            for accepted in accepted_tags:
                if accepted:
                    simulated_polling_interval = max(self.min_polling_interval, simulated_polling_interval * (1 - self.polling_delta))
                else:
                    simulated_polling_interval = min(self.max_polling_interval, simulated_polling_interval * (1 + self.polling_delta))
            time_without_improvement = 0
            while simulated_polling_interval != self.max_polling_interval:
                time_without_improvement += simulated_polling_interval
                simulated_polling_interval = min(self.max_polling_interval, simulated_polling_interval * (1 + self.polling_delta))
            time_without_improvement += self.max_polling_interval
        else:
            time_without_improvement = self.polling_interval
        return args.time_without_improvement >= time_without_improvement
    
    def _is_null(self, individual) -> bool:
        return False