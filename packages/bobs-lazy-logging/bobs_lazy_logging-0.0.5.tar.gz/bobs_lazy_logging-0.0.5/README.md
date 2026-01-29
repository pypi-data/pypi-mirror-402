Debug logging for lazy people.

'''
import logging
logger = logging.getLogger(__name__)

@LazyLogger(logger)
def something():
    ' i do something '
    return
'''

What's a LazyLoggerFactory?

"""
from lazy_logging import LazyLogger, LazyLoggerFactory

exampleLazyLogger = LazyLoggerFactory("EXAMPLE")

@exampleLazyLogger(logger)
def my_function_a():
    pass

@LazyLogger(logger,"EXAMPLE")
def my_function_b():
    pass

my_function_a == my_function_b
"""

You can set the logger level for both loggers with env var LL_LEVEL_EXAMPLE.