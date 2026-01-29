"""
consumer_exception Module
"""

from .consumer_exception import ConsumerException

class MissingResourceException(ConsumerException):
    """
    A MissingResourceException should be raised by any consumers that fail to locate a
    resource using its Identifier. 
    """
    def __init__(self, message):
        super().__init__(message)
