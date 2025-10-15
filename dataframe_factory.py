import os
import sys

import polars as pl

## Hardcode file arguments for dev
##file_path = 'my_file.ext'

## Use System arguments to trigger file from cmd
file_path = sys.argv[1]

## Use enviroment variables in production
#file_path =os.environ.get('FILE_PATH')

## Get File Extension
def get_file_extension(file_path: str) -> str:
    return os.path.splittext(file_path)


# Specific File Extension handlers
def csv_to_df(file_path: str, **kwargs) -> pl.DataFrame:
    try:
        if not file_path:
            return f"No Filepath provided"
        else:
            df = pl.read_csv(file_path, **kwargs)
            return df
    except Exception as e:
        print(f'There was an error running {__name__}: {e}')
    
def json_to_df(file_path: str, **kwargs) -> pl.DataFrame:
    try:
        if not file_path:
            return f"No Filepath provided"
        else:
            df = pl.read_json(file_path, **kwargs)
            return df
    except  Exception as e:
        print(f'There was an error running {__name__}: {e}')

def excel_to_df(file_path: str, **kwargs) ->pl.DataFrame:
    try:
        if not file_path:
            return f"No Filepath provided"
        else:
            df = pl.read_excel(file_path, **kwargs)
            return df
    except Exception as e:
        print(f'There was an error running {__name__}: {e}')

## The Dataframe Factory
def datafrane_factory(file_path: str, **kwargs) -> pl.DataFrame:
    file_extension = get_file_extension(file_path)

    match file_extension:
        case 'csv':
            df = csv_to_df(file_path, **kwargs)
        case 'json':
            df = json_to_df(file_path, **kwargs)
        case 'xls' | 'xlsx':
            df = excel_to_df(file_path, **kwargs)
        case _:
            print(f'The extension type {file_extension} is not compatible with Polars DataFrames')


if __name__ == "__main__":