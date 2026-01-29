import logging

    
def _configure_log():
    logger = logging.getLogger("opt_flow")
    logger.setLevel(logging.INFO)     
    if not logger.handlers:
        handler = logging.StreamHandler()   
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False  
    
_configure_log()