"""
Acroname MTM Utilities.

This module provides utilities for working with Acroname Manufacturing Test
Modules using the Brainstem python library.
"""
import copy
import time
from statistics import mean, median

from brainstem.result import Result


def mtm_exec(func, *args, **kwargs):
    """
    Execute brainstem function call.

    :param func: Function to execute
    :param args: Function args
    :param kwargs: Function kwargs
    :return: Function results
    """
    retries = 3
    value = None

    while retries > 0:
        result = func(*args, **kwargs)
        error = value = copy.deepcopy(result)

        if isinstance(result, Result):
            error = result.error
            value = result.value

        if error == 0:
            break
        else:
            retries -= 1
            if retries == 0:
                raise Exception(f"Brainstem Error {func.__name__}: {repr(result)}")

    return value


def get_voltage(channel, num_samples=10, scalar=1):
    """
    Get a voltage reading from the specified channel.

    Reads from the specified channel for the given number of samples. A
    dictionary is then returned containing the min, max, and mean readings.

    :param channel: MTM-DAQ2 channel to read
    :type channel: Analog
    :param num_samples: Number of readings to take of the specified channel
    :type num_samples: int
    :param scalar: Scalar to apply to voltage reading, i.e Voltage Divider
    :type scalar: float
    :return: Voltage reading dictionary7
    :rtype: dict
    """
    start_time = time.time()
    samples = [
        mtm_exec(channel.getVoltage) / 1000000.0 * scalar for _ in range(num_samples)
    ]
    end_time = time.time()
    return {
        "min": min(samples),
        "max": max(samples),
        "mean": mean(samples),
        "median": median(samples),
        "samples": samples,
        "duration": end_time - start_time,
    }


def get_current(channel, num_samples=10):
    """
    Get a current reading from a power channel.

    Reads from the specified channel for the given number of samples. A
    dictionary is then returned containing the min, max, and mean readings.
    """
    samples = [mtm_exec(channel.getCurrent) / 1000000.0 for _ in range(num_samples)]
    return {
        "min": min(samples),
        "max": max(samples),
        "mean": mean(samples),
        "median": median(samples),
        "samples": samples,
    }


def byte_list_to_int(byte_list, big_endian=False):
    """
    Convert a list of bytes to an integer.

    :param byte_list: List of bytes to convert to a int
    :type byte_list: list
    :param big_endian: Big/little endian flag
    :type big_endian: bool
    :return: Integer value from list
    :rtype: int
    """
    value = 0
    for i, v in enumerate(byte_list):
        if big_endian:
            value = (value << 8) + v
        else:
            value += v << i * 8

    return value
