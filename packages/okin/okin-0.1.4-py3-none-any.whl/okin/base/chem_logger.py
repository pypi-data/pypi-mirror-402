import logging
chem_logger = logging.getLogger(__name__)
chem_logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
log_format = "%(asctime)s.%(msecs)-2.2s [%(levelname)-9.9s] [%(filename)-25.25s] :: %(message)s"
formatter = logging.Formatter(fmt=log_format,datefmt='%Y-%m-%d %H:%M:%S')
# chem_logger.propagate = True
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
chem_logger.addHandler(stream_handler)

# chem_logger.debug("Test")