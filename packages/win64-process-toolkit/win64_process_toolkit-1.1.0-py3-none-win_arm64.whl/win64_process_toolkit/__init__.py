from typing import List, Union, overload
from win64_process_toolkit.__internal.native_lib import __get_native_lib


class ProcessInfo:
    """Windows Process Information"""

    @property
    def name(self):
        """Process Name (read only)"""
        return getattr(self, "__name")

    @property
    def id(self):
        """Process ID (read only)"""
        return getattr(self, "__id")


def get_process_id(process_name: str) -> int:
    """
    Get the ID of a process by name

    Args:
        process_name (str): _description_

    Returns:
        int: Process ID (0 if process not exist)
    """
    return __get_native_lib().get_process_id(process_name)


@overload
def inject_dll(process: int, dll_path: str) -> bool:
    """Inject a DLL into an existed process

    Args:
        process (int): The process ID
        dll_path (str): The file path of the DLL

    Returns:
        bool: True if succeed
    """


@overload
def inject_dll(process: str, dll_path: str) -> bool:
    """Inject a DLL into an existed process

    Args:
        process (str): The process name
        dll_path (str): The file path of the DLL

    Returns:
        bool: True if succeed
    """


def inject_dll(process: Union[int, str], dll_path: str) -> bool:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().inject_dll(process, dll_path)


def get_runtime_processes() -> List[ProcessInfo]:
    """Get all running process information

    Returns:
        List[ProcessInfo]: Runtime processes
    """
    result = []
    lib = __get_native_lib()
    count = lib.create_process_snapshot()
    for index in range(count):
        info = ProcessInfo()
        setattr(info, "__name", lib.get_process_name_from_snapshot(index))
        setattr(info, "__id", lib.get_process_id_from_snapshot(index))
        result.append(info)
    lib.free_process_snapshot()
    return result


def get_runtime_process_names() -> List[str]:
    """Get all running process names

    Returns:
        List[str]: Runtime process names
    """
    result = []
    lib = __get_native_lib()
    count = lib.create_process_snapshot()
    for index in range(count):
        result.append(lib.get_process_name_from_snapshot(index))
    lib.free_process_snapshot()
    return result


@overload
def kill_process(process: int, exit_code: int = 1) -> bool:
    """Kill an existing process

    Args:
        process (int): The process ID
        exit_code (int, optional): Process exit code. Defaults to 1.

    Returns:
        bool: True if succeed
    """


@overload
def kill_process(process: str, exit_code: int = 1) -> bool:
    """Kill an existing process

    Args:
        process (str): The process name
        exit_code (int, optional): Process exit code. Defaults to 1.

    Returns:
        bool: True if succeed
    """


@overload
def check_process(process: int) -> bool:
    """Check process existing

    Args:
        process (int): The process ID

    Returns:
        bool: True if exists
    """


@overload
def check_process(process: str) -> bool:
    """Check process existing

    Args:
        process (str): The process name

    Returns:
        bool: True if exists
    """


@overload
def suspend_process(process: int) -> bool:
    """suspend a process

    Args:
        process (str): The process name

    Returns:
        bool: True if succeed
    """


@overload
def suspend_process(process: str) -> bool:
    """suspend a process

    Args:
        process (str): The process name

    Returns:
        bool: True if succeed
    """


@overload
def resume_process(process: int) -> bool:
    """resume a process

    Args:
        process (int): The process ID

    Returns:
        bool: True if succeed
    """


@overload
def resume_process(process: str) -> bool:
    """resume a process

    Args:
        process (str): The process name

    Returns:
        bool: True if succeed
    """


@overload
def get_process_executable(process: int) -> str:
    """Get process executable file full path

    Args:
        process (int): The process ID

    Returns:
        str: executable file full path
    """


@overload
def get_process_executable(process: str) -> str:
    """Get process executable file full path

    Args:
        process (str): The process name

    Returns:
        str: executable file full path
    """


def kill_process(process: Union[int, str], exit_code: int = 1) -> bool:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().kill_process(process, exit_code)


def check_process(process: Union[int, str]) -> bool:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().check_process(process)


def suspend_process(process: Union[int, str]) -> bool:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().suspend_process(process)


def resume_process(process: Union[int, str]) -> bool:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().resume_process(process)


def get_process_executable(process: Union[int, str]) -> str:
    if isinstance(process, str):
        process = get_process_id(process)
    if process == 0:
        return False
    return __get_native_lib().get_process_executable_path(process)
