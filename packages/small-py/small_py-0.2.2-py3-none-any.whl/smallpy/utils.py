from datetime import datetime,timedelta
import time
import os
import ctypes
import pandas as pd
import json
import pyautogui as pag
from typing import Dict,Any,Optional,Sequence,Union,Tuple

def enable_virtual_terminal() -> None:
    """
    Enable virtual terminal processing for the current Windows console.

    This allows ANSI escape sequences (such as color codes and cursor
    movement) to work correctly in the Windows terminal.

    On non-Windows platforms, this function does nothing.

    Returns
    -------
    None
    """
    if os.name == 'nt':  # Windows
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(handle, mode)

def clear_terminal(
    lines: int = 1,
    length: int = 100
) -> None:
    """
    Clear previously printed lines from the terminal.

    This function moves the cursor up and overwrites the specified
    number of lines with spaces, effectively erasing them from view.

    Parameters
    ----------
    lines : int, optional
        Number of lines to clear from the terminal (default is 1).
    length : int, optional
        Number of character spaces used to overwrite each line
        (default is 100).

    Returns
    -------
    None
    """
    for _ in range(lines):
        print('\033[A'+' '*length,'\033[A')

def write_to_excel(
    dataframe: pd.DataFrame,
    output_path: str,
    print_decorators: bool = True
) -> None:
    """
    Write a Pandas DataFrame to an Excel file.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The DataFrame to be written to the Excel file.
    output_path : str
        Path (including filename) where the Excel file will be saved.
    print_decorators : bool, optional
        Whether to print status messages before and after writing
        the file (default is True).

    Returns
    -------
    None
    """
    print('WRITING TO EXCEL') if print_decorators else None
    with pd.ExcelWriter(output_path) as writer:
        dataframe.to_excel(writer, index=False)
    print(' Success') if print_decorators else None

def add_to_memory(
    memory_key:str, 
    new_entry:Dict[str,Any],
    memory_path:Optional[str]=None
) -> None:
    """
    Add or update a structured entry in a persistent JSON memory file.

    Entries are stored under a named `memory_key` and must:
    - Contain an `"id"` field
    - Share the same dictionary structure as existing entries
      under the same `memory_key`

    If an entry with the same `"id"` already exists, it is replaced.

    Parameters
    ----------
    memory_key : str
        Top-level key under which entries are stored.
    new_entry : dict
        Dictionary representing the entry to store. Must include an `"id"` key.
    memory_path : str, optional
        Path to the JSON memory file. Defaults to `memory/memory.json`.

    Returns
    -------
    None
    """
    def validate_new_entry(
            new_entry: Dict[str,Any],
            existing_entries: Sequence[Dict[str,Any]],
            memory_key: str
    ) -> None:
        """
        Validate a new memory entry against existing stored entries.

        Validation rules:
        - All entries under the same memory key must share the same dictionary structure
        - The new entry must contain an `"id"` field

        Parameters
        ----------
        new_entry : dict
            The entry being validated.
        existing_entries : sequence of dict
            Existing entries stored under the same memory key.
        memory_key : str
            Name of the memory section (used for error messages).

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the entry structure does not match existing entries
        KeyError
            If the `"id"` field is missing.
        """
        if existing_entries:
            if existing_entries[0].keys() != new_entry.keys():
                raise ValueError(
                    f'Dict structure of new entry does not match existing structure in "{memory_key}"'
                )
        if 'id' not in new_entry.keys():
            raise KeyError(f'Key "id" must be in new entries')
    
    if not memory_path:
        memory_path = r'memory\memory.json'
        
    if not os.path.isfile(memory_path):
        data = {}
    else:
        with open(memory_path,'r') as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                data = {}
    
    if memory_key not in data.keys():
        data[memory_key] = []
    
    validate_new_entry(new_entry,data[memory_key],memory_key)
    data[memory_key] = [entry for entry in data[memory_key] if entry['id'] != new_entry['id']] # removes existing entry from memory before adding new entry
    data[memory_key].append(new_entry)

    os.makedirs(os.path.dirname(memory_path), exist_ok=True)
    with open(memory_path, 'w') as file:
        json.dump(data, file, indent=2)

def is_in_memory(
    memory_key: str,
    new_entry: Dict[str, Any],
    comparison_field: str,
    memory_path: Optional[str] = None
) -> bool:
    """
    Check whether a matching entry exists in the persistent JSON memory.

    A match is defined as an entry with:
    - The same `"id"` value
    - The same value for the specified `comparison_field`

    All entries under the same `memory_key` must share the same dictionary
    structure.

    Parameters
    ----------
    memory_key : str
        Top-level key under which entries are stored.
    new_entry : dict
        Entry to compare against stored data. Must include `"id"` and
        `comparison_field`.
    comparison_field : str
        Field used to compare the new entry against existing entries.
    memory_path : str, optional
        Path to the JSON memory file. Defaults to `memory/memory.json`.

    Returns
    -------
    bool
        True if a matching entry exists, False otherwise.
    """
    def validate_new_entry(
        new_entry: Dict[str, Any],
        existing_entries: Sequence[Dict[str, Any]],
        comparison_field: str,
        memory_key: str
    ) -> None:
        """
        Validate a new entry against existing stored entries.

        Validation rules:
        - The new entry must have the same dictionary structure as existing entries
        - The new entry must contain an `"id"` key
        - The specified comparison field must exist in both existing entries
        and the new entry

        Parameters
        ----------
        new_entry : dict
            The entry being validated.
        existing_entries : sequence of dict
            Existing entries stored under the same memory key.
        comparison_field : str
            Field used for comparison in memory checks.
        memory_key : str
            Name of the memory section (used for error messages).

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the entry structure does not match existing entries
        KeyError
            If:
            - `"id"` is missing
            - `comparison_field` is missing in either entry
        """
        if existing_entries:
            if existing_entries[0].keys() != new_entry.keys():
                raise KeyError(f'Dict structure of new entry does not match existing structure in {memory_key}')
            if comparison_field not in existing_entries[0]:
                raise KeyError(f'Comparison field "{comparison_field}" not found in existing entries')
        if comparison_field not in new_entry:
            raise KeyError(f'Comparison field "{comparison_field}" not found in new entry')
        if 'id' not in new_entry:
            raise KeyError(f'Key "id" must be in new entries')
    
    if not memory_path:
        memory_path = r'memory\memory.json'

    if not os.path.isfile(memory_path):
        return False
    
    with open(memory_path,'r') as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            return False
        
    if memory_key not in data.keys():
        return False
    
    validate_new_entry(new_entry,data[memory_key],comparison_field,memory_key)
    for entry in data[memory_key]:
        if entry['id'] == new_entry['id'] and entry[comparison_field] == new_entry[comparison_field]:
            return True
    
    return False

def wait_for_image(
    image_path: Union[str,list],
    timeout: int = 5,
    interval: float = 0.1,
    conf: float = 0.95,
    invert_search = False
) -> Tuple[int, int] | bool:
    """
    Wait for an image (or list of images) to appear (or disappear) on the screen.

    Parameters
    ----------
    image_path : str or list of str
        Path to an image file, or list of image paths to search for.
    timeout : int, optional
        Maximum time to wait (seconds), default is 5.
    interval : float, optional
        Time to wait between search attempts (seconds), default is 0.1.
    conf : float, optional
        Confidence threshold for image recognition (0.0 - 1.0), default is 0.95.
    invert_search : bool, optional
        If True, waits for the image(s) to disappear instead of appear,
        default is False.

    Returns
    -------
    tuple of int or bool
        - Coordinates `(x, y)` of the found image center if invert_search is False
        - True if invert_search is True and the image(s) disappear

    Raises
    ------
    TypeError
        If `image_path` is neither a string nor a list.
    """
    start_time = time.time()
    coord = None
    printed = False
    
    imgs = []
    if isinstance(image_path,str):
        imgs.append(image_path)
        image_path = imgs
    
    if isinstance(image_path,list):
        while coord is None:
            if (time.time() - start_time) < timeout:
                pass
            else:
                if not printed:
                    if not invert_search:
                        print(f' - Unable to locate {[os.path.split(img)[1] for img in image_path]}')
                    else:
                        print(f' - Waiting for {[os.path.split(img)[1] for img in image_path]} to close')
                    printed = True
            
            for img in image_path:
                if not invert_search:
                    try:
                        coord = pag.locateCenterOnScreen(img,grayscale=True,confidence=conf)
                    except pag.ImageNotFoundException:
                        pass
                else:
                    try:
                        coord = pag.locateCenterOnScreen(img,grayscale=True,confidence=conf)
                    except pag.ImageNotFoundException:
                        coord = True
                
                time.sleep(interval)
        if printed:
            clear_terminal()
        return coord
    else:
        raise TypeError(f'Unsupported image_path type: {type(image_path)}')
    
def find_and_click(
    image_path: str,
    offset: Tuple[int,int] = (0, 0)
) -> None:
    """
    Wait for an image to appear on screen, optionally offset the coordinates,
    and perform a mouse click at that location.

    Parameters
    ----------
    image_path : str
        Path to the image to locate on screen.
    offset : tuple of int, optional
        (x, y) offset to apply to the found image coordinates before clicking.
        Default is (0, 0).

    Returns
    -------
    None
    """
    coord = wait_for_image(image_path)
    coord = offset_coords(coord,offset)
    pag.sleep(0.25)
    pag.click(coord)
    pag.sleep(0.25)

def offset_coords(
    coords: Tuple[int, int],
    offset: Tuple[int, int] = (0,0)
) -> Tuple[int,int]:
    """
    Apply an (x, y) offset to a pair of screen coordinates.

    Parameters
    ----------
    coords : tuple of int
        Original (x, y) coordinates.
    offset : tuple of int, optional
        (x, y) offset to apply. Default is (0, 0).

    Returns
    -------
    tuple of int
        New coordinates after applying the offset.

    Examples
    --------
    >>> offset_coords((100, 200), (10, -5))
    (110, 195)
    """
    x,y = coords
    x_off,y_off = offset

    return (x+x_off,y+y_off)

class Counter:
    """
    A simple progress counter to track task completion and estimate remaining time.

    Attributes
    ----------
    n : int
        Current progress count.
    count : int
        Total count to reach completion.
    formatter : str, optional
        A custom formatting string for display. Supports placeholders:
        - %n : current count
        - %N : total count
        - %T : estimated completion time (hh:mm AM/PM)
        - %t : remaining time in seconds
        - %f : remaining time formatted as "Hh Mm Ss"
    times_to_complete : list[float]
        List of time intervals between successive `display()` calls.
    start_times : list[datetime]
        Timestamps of when `display()` was called.
    max_completion_n : int
        Maximum number of recent intervals to track for averaging.
    """
    def __init__(self,count,max_completion_n=10,format=None):
        self.n:int = 0
        self.count:int = count
        self.formatter:str = format
        self.times_to_complete = []
        self.start_times = []
        self.max_completion_n = max_completion_n
    
    @property
    def __default(self):
        return f"{self.n}/{self.count}"
    
    @property
    def __formatted(self):
        formatting_map = {
            '%n':self.n,
            '%N':self.count,
            '%T':self.__completion_time,
            '%t':self.__time_remaining(),
            '%f':self.__time_remaining(formatted=True)
        }

        formatting_str = self.formatter
        for key,value in formatting_map.items():
            if value is None:
                formatting_str = formatting_str.replace(key,'')
            else:
                formatting_str = formatting_str.replace(key,f'{value}')
        
        return formatting_str
    
    @property
    def __completion_time(self):
        if self.__time_remaining() is not None:
            exp_end_time = datetime.fromtimestamp(datetime.now().timestamp() + self.__time_remaining())
            return exp_end_time.strftime('%I:%M %p')
        else:
            return None
    
    def __format_time(self,seconds):
        secs = int(seconds)
        hr = secs // 3600
        mins = (secs % 3600) // 60
        sec = secs % 60
        return f'{hr}h {mins}m {sec}s'
    
    def __time_remaining(self,formatted = False):
        if not self.times_to_complete:
            return None
        
        count_remaining = self.count - self.n
        avg_time = (sum(self.times_to_complete) / len(self.times_to_complete))
        seconds = avg_time * count_remaining

        if formatted:
            return self.__format_time(seconds)
        else:
            return round(seconds,2)

    def display(self):
        self.start_times.append(datetime.now())

        if len(self.start_times) > 1:
            self.times_to_complete.append(self.start_times[-1].timestamp() - self.start_times[-2].timestamp())
            if len(self.times_to_complete) > self.max_completion_n:
                self.times_to_complete = self.times_to_complete[-self.max_completion_n:]

        self.n += 1
        if self.formatter:
            print(self.__formatted)
        else:
            print(self.__default)

def get_most_recent_file(directory: str) -> str:
    """
    Return the most recently created or modified file in a given directory.

    Parameters
    ----------
    directory : str
        Path to the directory to search for files.

    Returns
    -------
    str
        Full path to the most recently created/modified file.
        Returns "No files found" if the directory contains no files.

    Examples
    --------
    >>> get_most_recent_file(r"C:\\Users\\Me\\Documents")
    'C:\\Users\\Me\\Documents\\latest_report.xlsx'
    """
    files = [os.path.join(directory, file) for file in os.listdir(directory) 
             if os.path.isfile(os.path.join(directory, file))]

    return max(files, key=os.path.getctime) if files else "No files found"
        
def __main():
    ...

if __name__ == '__main__':
    __main()
