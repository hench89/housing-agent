import json, gzip, os
import pandas as pd



def save_dict(data, file_path: str):
    create_dirs_for_file(file_path)
    data = json.dumps(data).encode('utf-8')
    with gzip.open(file_path, 'wb') as f:
        f.write(data)


def load_dict(file_path: str):
    with gzip.open(file_path, 'rb') as f:
        file_content = f.read()
    json_data = json.loads(file_content)
    return json_data


def load_dataframe_from_file(file_path):
    d = load_dict(file_path)
    df = pd.DataFrame(d)
    return df


def load_dataframe_from_dir(dir_path):
    files = [f for f in os.listdir(dir_path)]
    data = [load_dict(f'{dir_path}/{f}') for f in files]
    loaded_dict = [d for d in data if isinstance(d, dict)]
    loaded_list = [l for l in data if isinstance(l, list)]  # if some files has list instead of dict
    all_dict = loaded_dict + [i for s in loaded_list for i in s]
    df = pd.DataFrame(all_dict)
    return df


def read_ids_from_list_file(file_path, api):
    id_col = 'id' if api == 'forsale' else 'estateId'
    with gzip.open(file_path, 'rb') as f:
        file_content = f.read()
    json_data = json.loads(file_content)
    estate_ids = [x[id_col] for x in json_data]
    return set(estate_ids)


def identify_estate_ids_already_downloaded(estate_root) -> list:
    if not os.path.exists(estate_root):
        return []
    files = [f for f in os.listdir(estate_root)]
    file_names = [os.path.splitext(f)[0] for f in files]
    numeric_files = [f for f in file_names if f.isnumeric()]
    files_as_int = [int(f) for f in numeric_files]
    return files_as_int


def delete_files(dir_path, file_names, file_format='gz'):
    files_to_remove = [f'{dir_path}/{f}.{file_format}' for f in file_names]
    for f in files_to_remove:
        os.remove(f)


def load_dataframe(path):
    if os.path.isdir(path):
        df = load_dataframe_from_dir(path)
    else:
        df = load_dataframe_from_file(path)
    return df


def create_dirs_for_file(file_path: str):
    abs_file_path = os.path.abspath(file_path)
    dir_name = os.path.dirname(abs_file_path)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
