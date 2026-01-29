"""
Author: Marcin 'Speedy' Kotowski
Library: SimpleJsonUtils
Version: 0.1.0
    Contact:
    Discord: d2slasher
    Gmail: marcin.kotowski2k09@gmail.com
    

"""

import json
from pathlib import Path
from typing import cast, Any, Union

def _is_int_parsable(value) -> bool:
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False

def _is_float_parsable(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def _validate_path(path: str | Path, must_exist: bool = True) -> Path:
        path = Path(path)
        if path.suffix.lower() != ".json":
            raise ValueError(f"Wrong file extension {path.suffix}")
        if not path.exists() and must_exist:
            raise FileNotFoundError("File does not exist")
        return path
    
    
def read_json_file(path: str|Path,encoding:str = "utf-8") -> dict[str,Any]|list[dict[str,Any]]:
        """
        Reads and parses a JSON file from disk.

        Args:
            path (str | Path): Path to the JSON file.
            encoding (str): File encoding (default "utf-8").

        Returns:
            dict[str, Any] | list[dict[str, Any]]: Parsed JSON data.

        Raises:
            ValueError: If the file extension is not .json or structure is invalid.
            FileNotFoundError: If the file does not exist.
        """
        
        #converts string path to Path
        path = _validate_path(path)
        #reads json file
        with open(file=path, mode="r",encoding=encoding) as file:
            data = json.load(file) #returns json data info
        
        
        #checks if data is of type list
        if isinstance(data,list):
            if not data:
                return []
            return cast(list[dict[str,Any]],data)
        
        #checks if data is of type dict
        elif isinstance(data,dict):
            return cast(dict[str, Any], data)
        
        #if data isn't either dict or list raise new exception
        else:
            raise ValueError("Wrong structure of JSON file")

    
def append_to_json_file(object:dict[str,Any], path: str|Path, encoding:str= "utf-8", ensure_ascii:bool= True, indent: int=0) -> None:
        
        """
        Appends a dictionary to the JSON file or converts dict to list if needed.

        Args:
            object (dict[str, Any]): Dictionary to append.
            path (str | Path): Path to JSON file.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).

        Raises:
            ValueError: If object is not a dict or JSON structure is invalid.
            FileNotFoundError: If file does not exist.
            RuntimeError: If JSON file cannot be read.
        """


        #checks if object is correct type
        if not isinstance(object,dict):
            raise ValueError("Object has to be type dict key: string value Any type")
        
        #converts string path to Path
        path = _validate_path(path)

        #if something wents wrong with reading file returns exception message
        try:
            data = read_json_file(path=path,encoding=encoding)
        except Exception as e:
            raise RuntimeError(f"Cannot read JSON file: {e}")
        

        #if data is list type appends object to list 
        if isinstance(data,list):
            data.append(object)
            list_of_dict = data
        #if data is dict type creates new list with data and object
        elif isinstance(data,dict):
            list_of_dict = [data,object]
        
        #raises new exception if data isn't either dict or list 
        else:
            raise ValueError(f"File {path} has wrong structure")

        #dumps new list to json file
        with open(file=path,mode="w",encoding=encoding) as file:
            json.dump(list_of_dict,file,indent=indent,ensure_ascii=ensure_ascii)

def remove_dict_from_json_file(path: str|Path, match_key: str, match_value, encoding:str= "utf-8", ensure_ascii:bool= True, indent: int=0) -> None:
        """
        Removes a dictionary from JSON file based on match_key and match_value.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key to identify dictionary.
            match_value: Value of match_key to identify dictionary.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).

        Raises:
            ValueError: If dictionary not found or structure is invalid.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path
        path = _validate_path(path)
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):

            #if length of list is equal to 0 raises exception
            if len(data) == 0:
                raise ValueError("Can't remove dict - List of Dictionaries is empty")
            
            #trying to get dictionary by value
            found = next((dictionary for dictionary in data if dictionary.get(match_key) == match_value), None)
            
            #if ^^^^ didnt found dictionary rises exception
            if found is None:
                raise ValueError("Dictionary you want edit not found")
            
            #removes dict             
            data.remove(found)
            
               
        #checks if data is dict type
        elif isinstance(data,dict):
            #removes dict  
            if data.get(match_key) == match_value:
                data = {}
            else:
                raise ValueError("Dictionary does not match remove condition")
        else:
            raise ValueError("Wrong JSON structure")
        #Edits json file   
        with open(path, "w",encoding=encoding) as file:
            json.dump(data,file,ensure_ascii=ensure_ascii,indent=indent)   
    
def overwrite_json_file(path: str|Path, data_to_overwrite: Union[list, dict[str,Any]], encoding:str= "utf-8", ensure_ascii:bool= True, indent: int=0) -> None:
        """
        Overwrites the JSON file with new data.

        Args:
            path (str | Path): Path to JSON file.
            data_to_overwrite (list | dict[str, Any]): New data to overwrite old data.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).

        Raises:
            ValueError: If data_to_overwrite is not list or dict.
            FileNotFoundError: If file does not exist.
            OSError: If file cannot be overwritten.
        """
        
        #converts string path to Path
        path = _validate_path(path)
        
        

        #========= BACK UP DATA =========#
        back_up_data = None
        try:

            back_up_data = read_json_file(path, encoding)
        except Exception:
            back_up_data = None

        #if data_to_overwrite isnt type of list or dict raises new exception
        if not isinstance(data_to_overwrite,(list,dict)):
            raise ValueError(f"Object has to be type of list[dict[str,Any]], list[], dict[str,Any] - {type(data_to_overwrite)}")


        #if something went wrong with overwriteing a file we overwrite it for old data and raises exception
        try:
            with open(file=path,mode="w",encoding=encoding) as file:
                json.dump(data_to_overwrite,file,indent=indent,ensure_ascii=ensure_ascii)

        except OSError:
            if back_up_data is not None: #checks if back up data isnt empty to dont remove potencially some rests of data   
                #writes old data to file if something wents wrong with overwriteing
                with open(file=path,mode="w",encoding=encoding) as file:
                    json.dump(back_up_data,ensure_ascii=ensure_ascii,indent=indent)
                
                raise OSError("Cannot overwrite this file")
 
    
def edit_json_file(path: str|Path, match_key: str, match_value, update_key: str, new_value, encoding:str= "utf-8", ensure_ascii:bool= True, indent: int=0) -> None:
        """
        Edits the value of a key in a dictionary in the JSON file.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key used to find the correct dictionary.
            match_value: Value of match_key to identify the dictionary.
            update_key (str): Key to update within the dictionary.
            new_value: New value to assign to update_key.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).

        Raises:
            ValueError: If dictionary not found or update fails.
            FileNotFoundError: If file does not exist.
        """

        #converts string path to Path
        path = _validate_path(path)
        
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):

            #if length of list is equal to 0 raises exception
            if len(data) == 0:
                raise ValueError("Can't edit value - List of Dictionaries is empty")
            
            #trying to get dictionary by value
            found = next((dictionary for dictionary in data if dictionary.get(match_key) == match_value), None)
            
            #if ^^^^ didnt found dictionary rises exception
            if found is None:
                raise ValueError("Dictionary you want edit not found")
            
            #edits value
            try:
                found[update_key] = new_value
            except:
                raise ValueError("Cant edit json file - update_key or new_value incorrect")
               
        #checks if data is dict type
        elif isinstance(data,dict):
            #edits value
            try:
                data[update_key] = new_value
            except:
                raise ValueError("Cant edit json file - update_key or new_value incorrect")
        else:
            raise ValueError("Wrong JSON structure")
        #Edits json file   
        with open(path, "w",encoding=encoding) as file:
            json.dump(data,file,ensure_ascii=ensure_ascii,indent=indent)

    
def add_key_value_to_json_file(path: str|Path, match_key: str, match_value, new_key: str, new_value, encoding:str= "utf-8", ensure_ascii:bool= True, indent: int=0) -> None:
        """
        Adds a new key-value pair to a dictionary identified by match_key and match_value.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key used to find the correct dictionary.
            match_value: Value of match_key to identify the dictionary.
            new_key (str): New key to add.
            new_value: Value for the new key.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).

        Raises:
            ValueError: If dictionary not found or key already exists.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path
        path = _validate_path(path)
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):

            #if length of list is equal to 0 raises exception
            if len(data) == 0:
                raise ValueError("Can't edit value - List of Dictionaries is empty")
            
            #trying to get dictionary by value
            found = next((dictionary for dictionary in data if dictionary.get(match_key) == match_value), None)
            
            #if ^^^^ didnt found dictionary rises exception
            if found is None:
                raise ValueError("Dictionary you want edit not found")
            
            #adds key value pair
            if found.get(new_key) is not None:
                raise ValueError("This key already exists - to edit it use edit_json_file() function")
            else:
                found[new_key] = new_value
        #checks if data is dict type
        if isinstance(data,dict):
            #adds key value pair
            if data.get(new_key) is not None:
                raise ValueError("This key already exists - to edit it use edit_json_file() function")
            else:
                data[new_key] = new_value

        #Edits json file   
        with open(path, "w",encoding=encoding) as file:
            json.dump(data,file,ensure_ascii=ensure_ascii,indent=indent)

    
def normalize_json_file(path: str|Path, encoding:str= "utf-8", ensure_ascii:bool= True, indent: int =0) -> None:
        """
        Converts a JSON file from a dict to a list of dictionaries.

        Args:
            path (str | Path): Path to JSON file.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            indent (int): Number of spaces for indentation (default 0).
        """
        #converts string path to Path 
        path = Path(path)
        if path.suffix.lower() != ".json":
            raise ValueError(f"Wrong file extension {path.suffix}")
        
        #if file doesn't exist raises new exception
        if not path.exists():
            raise FileNotFoundError(f"File {path} does not exist")
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        if isinstance(data,list):
            return
        elif isinstance(data,dict):
            new_data = [data]
        else:
            raise ValueError("Wrong JSON structure")
        with open(path,encoding=encoding,mode="w") as file:
            json.dump(new_data,file,ensure_ascii=ensure_ascii,indent=indent)
    
    
def create_json_file(path: str|Path, type_of_json: list|dict =list):
        """
        Creates an empty JSON file of type list or dict.

        Args:
            path (str | Path): Complete path including directories and file name.
            type_of_json (list | dict): Type of JSON file to create ([] or {}).
        
        Raises:
            ValueError: If type_of_json is invalid or extension is not .json.
        """
        #converts string path to Path 
        path = _validate_path(path, False)
        
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path,"w") as file:
            if type_of_json == list:
                file.write("[]")
            elif type_of_json == dict:
                file.write("{}")
            else:
                raise ValueError("Incorrect type_of_json")
     
    
def exists_in_json_file(path: str|Path, match_key: str, match_value, encoding:str= "utf-8") -> bool:
        """
        Checks if a dictionary exists in the JSON file.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key to identify dictionary.
            match_value: Value of match_key to identify dictionary.
            encoding (str): File encoding (default "utf-8").

        Returns:
            bool: True if dictionary exists, False otherwise.

        Raises:
            ValueError: If JSON structure is invalid.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path
        path = _validate_path(path)
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)

        if isinstance(data,list):
            return any(i.get(match_key) == match_value for i in data)
        
        elif isinstance(data,dict):
            if data.get(match_key) == match_value:
                return True
            else:
                return False
        else:
            raise ValueError("Wrong JSON structure")
   
def get_value_from_json_file(path: str|Path, match_key: str, match_value, check_key: str, encoding:str= "utf-8") -> Any:
        """
        Retrieves the value for a given key from a dictionary identified by match_key and match_value.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key to identify dictionary.
            match_value: Value of match_key to identify dictionary.
            check_key (str): Key whose value will be returned.
            encoding (str): File encoding (default "utf-8").

        Returns:
            Any: Value associated with check_key.

        Raises:
            ValueError: If dictionary or check_key not found.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path
        path = _validate_path(path)
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):
            found = next((i.get(check_key) for i in data if i.get(match_key) == match_value),None)
            if found is None:
                #if value not found in list raises exception
                raise ValueError("Value not found")
            else:
                return found
        elif isinstance(data,dict):
            if data.get(match_key) != match_value:
                raise ValueError("Value not found")
            if check_key not in data:
                raise ValueError("check_key not found")
            return data[check_key]
        else:
            raise ValueError("Wrong JSON Structure")
        
def get_max_from_json_file(path: str|Path, match_key: str, encoding:str= "utf-8", return_type: int|float|str = int) -> int|float|str:
        """
        Returns the maximum value for a given key in the JSON file.

        Works with int, float, and parsable numeric strings.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key to check for max value.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            return_type (int | float | str): Type of value to return (default int).

        Returns:
             int | float | str: Maximum value for the given key.

        Raises:
            ValueError: If no parsable values found or return_type is invalid.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path
        path = _validate_path(path)
        
       
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):
            #gets max value from float parsable values
            values = [float(i.get(match_key)) for i in data if _is_float_parsable(i.get(match_key))]
            if not values:
                raise ValueError("No parsable values found for match key")           
            maximum = max(values)
            
            #if return type is int it checks if float value is int parsable
            if return_type == int:
                if not _is_int_parsable(maximum):
                    raise ValueError("Can't return int type - not parsable")           
                else:
                    return int(maximum)
            
            #returns float
            if return_type == float:
                return float(maximum)
            
            #returns string
            if return_type == str:
                return str(maximum)
            
            #if return type is other than int string or float raises exception
            else:
                raise ValueError("return_type has to be int, float or str")
        

        #checks if data is dict type
        if isinstance(data,dict):
            
            #parses to float and
            maximum = data.get(match_key)
            if maximum is None:
                raise ValueError("Can't get max value")
            
            if _is_float_parsable(maximum):
                if return_type == int: #checks if return type is int
                    if not _is_int_parsable(maximum): #if return type is int it checks if float value is int parsable
                        raise ValueError("Can't return int type - not parsable")           
                    else:
                        return int(maximum)
                #returns float
                if return_type == float:
                    return float(maximum)
                #returns float
                if return_type == str:
                    return str(maximum)
            else:
                raise ValueError(f"Value under key '{match_key}' is not parsable")
   
def get_min_from_json_file(path: str|Path, match_key: str, encoding:str= "utf-8", return_type: int|float|str = int) -> int|float|str:
        """
        Returns the minimum value for a given key in the JSON file.

        Works with int, float, and parsable numeric strings.

        Args:
            path (str | Path): Path to JSON file.
            match_key (str): Key to check for min value.
            encoding (str): File encoding (default "utf-8").
            ensure_ascii (bool): If True, non-ASCII characters are escaped (default True).
            return_type (int | float | str): Type of value to return (default int).

        Returns:
            int | float | str: Minimum value for the given key.

        Raises:
            ValueError: If no parsable values found or return_type is invalid.
            FileNotFoundError: If file does not exist.
        """
        #converts string path to Path 
        path = _validate_path(path)
        
        #loads data from json file you want to edit
        data = read_json_file(path=path,encoding=encoding)
        
        #checks if data is list type
        if isinstance(data,list):
            #gets min value from float parsable values
            values = [float(i.get(match_key)) for i in data if _is_float_parsable(i.get(match_key))]
            if not values:
                raise ValueError("No parsable values found for match key")           
            minimum = min(values)
            
            #if return type is int it checks if float value is int parsable
            if return_type == int:
                if not _is_int_parsable(minimum):
                    raise ValueError("Can't return int type - not parsable")           
                else:
                    return int(minimum)
            
            #returns float
            if return_type == float:
                return float(minimum)
            
            #returns string
            if return_type == str:
                return str(minimum)
            
            #if return type is other than int string or float raises exception
            else:
                raise ValueError("return_type has to be int, float or str")
        

        #checks if data is dict type
        if isinstance(data,dict):
            
            #parses to float and
            minimum = data.get(match_key)
            if minimum is None:
                raise ValueError("Can't get min value")
            
            if _is_float_parsable(minimum):
                if return_type == int: #checks if return type is int
                    if not _is_int_parsable(minimum): #if return type is int it checks if float value is int parsable
                        raise ValueError("Can't return int type - not parsable")           
                    else:
                        return int(minimum)
                #returns float
                if return_type == float:
                    return float(minimum)
                #returns float
                if return_type == str:
                    return str(minimum)
            else:
                raise ValueError(f"Value under key '{match_key}' is not parsable")