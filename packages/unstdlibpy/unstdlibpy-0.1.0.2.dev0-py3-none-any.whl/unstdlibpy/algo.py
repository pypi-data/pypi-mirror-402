
"""
This module re-exports selected functions and classes from the standard
libraries `bisect`, `heapq`, and `collections`, along with some custom
algorithmic utilities.
It provides a unified interface for common algorithmic operations.
Functions included:
- binary_search: Perform binary search on a sorted array.
- top_k_elements: Get the top k largest elements from an iterable.
- sliding_window: Generate a sliding window of a specified size over an iterable.

More than these.
Colours are in this. Such as RED, BLACK, PURPLE, CHINESE_RED, MAGIC_COLOR...

Module for defining constants that cannot be changed once set.
Includes common mathematical and physical constants.

Module for saving and loading data to/from files in JSON format.
Provides functions to save, load, delete, check existence, list files, and clear files in a directory.

"""

from bisect import bisect_left
from heapq import nlargest
from collections import deque
from typing import List, Tuple, Any, Iterable, Deque, Callable
from json import loads, dumps
from os import remove, path, listdir
from sys import getsizeof

class Const:
    """A class to define constants. Once a constant is set, it cannot be changed."""
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set a constant value. Raises an AttributeError if the constant is already set.
        :param name: The name of the constant.
        :param value: The value of the constant.
        """

        if name in self.__dict__:
            raise AttributeError(f"Cannot reassign constant '{name}'")
        self.__dict__[name] = value


class Storage:
    def __init__(self):
        pass

    def save(self, data: str,filename: str) -> None:
        """
        Save data to a file in JSON format.
        :param data: The data to save.
        :param filename: The name of the file to save the data to.
        """

        try:
            with open(filename, 'w') as f:
                f.write(dumps(data))
        except Exception as e:
            print(f"Error saving data to {filename}: {e}")

    def load(self, filename: str):
        """
        Load data from a file in JSON format.
        :param filename: The name of the file to load the data from.
        :return: The loaded data.
        """
        
        try:
            with open(filename, 'r') as f:
                data = f.read()
                return loads(data)
        except Exception as e:
            print(f"Error loading data from {filename}: {e}")
            return None

    def delete(self, filename: str) -> None:
        """
        Delete a file.
        :param filename: The name of the file to delete.
        """

        try:
            remove(filename)
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")

    def exists(self, filename: str) -> bool:
        """
        Check if a file exists.
        :param filename: The name of the file to check.
        :return: True if the file exists, False otherwise.
        """

        return path.exists(filename)
    
    def list_files(self, directory: str) -> List[str]:
        """
        List all files in a directory.
        :param directory: The directory to list files from.
        :return: A list of file names in the directory.
        """

        try:
            return [f for f in listdir(directory) if path.isfile(path.join(directory, f))]
        except Exception as e:
            print(f"Error listing files in directory {directory}: {e}")
            return []

    def clear(self, directory: str) -> None:
        """
        Delete all files in a directory.
        :param directory: The directory to clear files from.
        """

        try:
            for f in self.list_files(directory):
                self.delete(path.join(directory, f))
        except Exception as e:
            print(f"Error clearing files in directory {directory}: {e}")


def floatequ(num1: float, num2: float, e: float=1e-10) -> float:
    return abs(num1 - num2) < e * (int(num1 + num2) >> 1)

def binary_search(arr: List[Any], target: Any) -> int:
    """
    Perform binary search on a sorted array.
    :param arr: A sorted list of elements.
    :param target: The element to search for.
    :return: The index of the target element if found, otherwise -1.
    """

    index = bisect_left(arr, target)
    if index != len(arr) and arr[index] == target:
        return index
    return -1

def top_k_elements(iterable: Iterable[Any], k: int) -> List[Any]:
    """
    Get the top k largest elements from an iterable.
    :param iterable: An iterable of elements.
    :param k: The number of top elements to retrieve.
    :return: A list of the top k largest elements.
    """

    return nlargest(k, iterable)

def sliding_window(iterable: Iterable[Any], window_size: int) -> Iterable[Tuple[Any, ...]]:
    """
    Generate a sliding window of a specified size over an iterable.
    :param iterable: An iterable of elements.
    :param window_size: The size of the sliding window.
    :return: An iterable of tuples representing the sliding windows.
    """

    if window_size <= 0:
        raise ValueError("window_size must be > 0")

    it = iter(iterable)
    window: Deque[Any] = deque(maxlen=window_size)

    try:
        for _ in range(window_size):
            window.append(next(it))
    except StopIteration:
        # Not enough elements for a full window: yield nothing
        return

    yield tuple(window)

    for elem in it:
        window.append(elem)
        yield tuple(window)

def sort(num: Iterable[Any]) -> Iterable[Any]:
    """
    Sort for a Iterable
    :param num: A function of sorting.
    :type num: Iterable[Any]
    :return: An Iterable of sorting.
    :rtype: Iterable[Any]
    """
    return sorted(num)

def exec(func: Callable, *arg, **kwarg) -> Any:
    return func(*arg, **kwarg)

def printsprint(*values: object, sep: str | None = "", end: str | None = "\n", file = None, flush = False) -> None:
    print(*values, sep=sep, end=end, flush=flush,file=file)

def rgb(string: str, r: int, g: int, b: int, mode: str = 't') -> str:
    assert isinstance(r, int) and isinstance(g, int) and isinstance(b, int) and \
        0 <= r < 256 and 0 <= g < 256 and 0 <= b < 256, f'Bad rgb: {r=}, {g=}, {b=}.'
    if mode == 't': m: int = 38
    elif mode == 'b': m: int = 48
    else: raise NameError(f'Unknown mode: \'{mode}\'.')
    return f'\033[{m};2;{r};{g};{b}m{string}\033[0m'

def make_rgb_mode(r: int, g: int, b: int, mode: str = 't') -> Callable:
    assert isinstance(r, int) and isinstance(g, int) and isinstance(b, int) and \
        0 < r < 256 and 0 < g < 256 and 0 < b < 256, f'Bad rgb: {r=}, {g=}, {b=}.'
    if mode == 't': m: int = 38
    elif mode == 'b': m: int = 48
    else: raise NameError(f'Unknown mode: \'{mode}\'.')
    def wrap(string: str) -> str:
        return f'\033[{m};2;{r};{g};{b}m{string}\033[0m'
    wrap.__name__ = f'rgb({r=}, {g=}, {b=})'
    return wrap

def make_rgb(r: int, g: int, b: int) -> Callable:
    assert isinstance(r, int) and isinstance(g, int) and isinstance(b, int) and \
        0 <= r < 256 and 0 <= g < 256 and 0 <= b < 256, f'Bad rgb: {r=}, {g=}, {b=}.'
    
    def wrap(string: str, mode: str = 't') -> str:
        if mode == 't': m: int = 38
        elif mode == 'b': m: int = 48
        else: raise NameError(f'Unknown mode: \'{mode}\'.')
        return f'\033[{m};2;{r};{g};{b}m{string}\033[0m'
    wrap.__name__ = f'rgb({r=}, {g=}, {b=})'
    return wrap

def sizeof(var: Any) -> int:
    if hasattr(var, '__iter__'):
        l = 0
        for i in var: l += getsizeof(i)
        return getsizeof(var) + l
    else:
        return getsizeof(var)

num2_16: int = 0xFFFF
num2_32: int = 0xFFFFFFFF
num2_64: int = 0xFFFFFFFF_FFFFFFFF
float_inf: float = float('inf')
float_minf: float = float('-inf')
float_zero: float = 0.0

# some colors.
RED = make_rgb(255, 0, 0)
BLUE = make_rgb(0, 0, 255)
GREEN = make_rgb(0, 255, 0)
YELLOW = make_rgb(255, 255, 0)
ORANGE = make_rgb(255, 128, 0)
CYAN = make_rgb(0, 255, 255)
PURPLE = make_rgb(255, 0, 255)
BLACK = make_rgb(0, 0, 0)
WHITE = make_rgb(255, 255, 255)

# special red
CHINESE_RED = make_rgb(230, 0, 18)
BRIGHT_RED  = make_rgb(255, 0, 36)

# special blue
SKY_BLUE = make_rgb(135, 206, 235)

#special green
EMERALD_GREEN = make_rgb(80, 200, 120)

# ???
MAGIC_COLOR = make_rgb(74, 65, 42)

const = Const()
function_const = Const()
class_const = Const()
num_const = Const()

# Defining some common mathematical and physical constants

num_const.pi = 3.141592653589793 # Pi
num_const.e = 2.718281828459045 # Euler's number
num_const.phi = 1.618033988749895 # Golden ratio
num_const.gravity = 9.80665  # m/s^2
num_const.speed_of_light = 299792458  # m/s
num_const.avogadro_number = 6.02214076e23  # 1/mol
num_const.boltzmann_constant = 1.380649e-23  # J/K
num_const.planck_constant = 6.62607015e-34  # J·s
num_const.gas_constant = 8.314462618  # J/(mol·K)
num_const.elementary_charge = 1.602176634e-19  # C
num_const.fine_structure_constant = 7.2973525693e-3  # dimensionless
num_const.hubble_constant = 67.4  # km/s/Mpc
num_const.universal_gravitational_constant = 6.67430e-11  # m^3/(kg·s^2)
num_const.stefan_boltzmann_constant = 5.670374419e-8  # W/(m^2·K^4)
num_const.electron_mass = 9.10938356e-31  # kg
num_const.proton_mass = 1.67262192369e-27  # kg
num_const.neutron_mass = 1.67492749804e-27  # kg
num_const.water_density = 997  # kg/m^3 at 25 °C
num_const.standard_temperature = 273.15  # K
num_const.standard_pressure = 101325  # Pa
num_const.light_year = 9.4607e15  # meters
num_const.astronomical_unit = 1.495978707e11  # meters
num_const.parsec = 3.0857e16  # meters
num_const.electron_volt = 1.602176634e-19  # Joules
num_const.coulomb_constant = 8.9875517923e9  # N·m²/C²
num_const.magnetic_constant = 1.25663706212e-6  # N/A²
num_const.electric_constant = 8.854187817e-12  # F/m
num_const.permeability_of_free_space = 4e-7 * 3.141592653589793  # H/m
num_const.impedance_of_free_space = 376.730313668  # Ohms
num_const.rydberg_constant = 10973731.568160  # 1/m
num_const.solar_mass = 1.98847e30  # kg
num_const.jupiter_mass = 1.898e27  # kg
num_const.earth_mass = 5.97237e24  # kg
num_const.moon_mass = 7.342e22  # kg
num_const.solar_radius = 6.9634e8  # meters
num_const.earth_radius = 6.371e6  # meters
num_const.universe_age = 13.8e9  # years
num_const.planck_length = 1.616255e-35  # meters
num_const.planck_time = 5.391247e-44  # seconds
num_const.planck_mass = 2.176434e-8  # kg
num_const.planck_temperature = 1.416784e32  # Kelvin
num_const.bohr_radius = 5.29177210903e-11  # meters
num_const.classical_electron_radius = 2.8179403262e-15  # meters
num_const.thomson_cross_section = 6.6524587321e-29  # m²
num_const.faraday_constant = 96485.33212  # C/mol
num_const.universal_molar_volume = 22.414  # L/mol at STP

storage = Storage()

if __name__ == '__main__':
    print(sizeof(storage))
    print(CHINESE_RED("Water of cow is milk"))
    print(RED        ("Water of cow is milk"))
    print(BRIGHT_RED ("Water of cow is milk"))
    print(MAGIC_COLOR("Water of cow is milk"))

