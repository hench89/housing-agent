import sys, csv
from datetime import date
from agent import boliga, archive, transform, utils
import pandas as pd


def identify_missing_and_removed_ids(forsale_path, sold_path, estate_dir):
    estate_ids = archive.identify_estate_ids_already_downloaded(estate_dir)
    forsale_ids = archive.read_ids_from_list_file(forsale_path, 'forsale')
    sold_ids = archive.read_ids_from_list_file(sold_path, 'sold')
    all_list_ids = forsale_ids.union(sold_ids)
    missing_ids = utils.a_diff_b(all_list_ids, estate_ids)
    removed_ids = utils.a_diff_b(estate_ids, all_list_ids)
    missing_ids.remove(0)  # id 0 for estates without proper data
    return missing_ids, removed_ids


def merge_data_and_save_to_file(df1, df2, dir_path, filename):
    parquet_path = f'{dir_path}/{filename}.parquet'
    csv_path = f'{dir_path}/{filename}.csv'
    utils.create_dirs_for_file(csv_path)
    df = transform.add_missing_cols_to_dataframe(df1, df2, 'estate_id')
    df.to_parquet(parquet_path)
    df.to_csv(csv_path, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC, index=False)


def download_new_estate_data(ids, estate_dir):
    for idx, estate_id in enumerate(ids):
        idx_to_go = len(ids) - idx
        if (idx_to_go % 100) == 0:
            print(f'{idx_to_go} more to go..')
        data = boliga.get_estate_data(estate_id)
        data['fetched_date'] = str(date.today())
        estate_path = f'{estate_dir}/{estate_id}.gz'
        archive.save_dict(data, estate_path)


def download_new_list_data(zipcode, forsale_path, sold_path):
    apis = ['forsale', 'sold']
    paths = [forsale_path, sold_path]
    for path, api in zip(paths, apis):
        data = boliga.get_list_results(zipcode, api)
        archive.save_dict(data, path)


def update_archive(zipcode, forsale_path, sold_path, estate_dir):
    download_new_list_data(zipcode, forsale_path, sold_path)
    missing_ids, removed_ids = identify_missing_and_removed_ids(forsale_path, sold_path, estate_dir)
    if len(missing_ids) > 0:
        print(f'downloading {len(missing_ids)} new estate items')
        download_new_estate_data(missing_ids, estate_dir)
    if len(removed_ids) > 0:
        print(f'removing {len(removed_ids)} estate files')
        archive.delete_files(estate_dir, removed_ids)


def read_dataframes_and_concat(paths):
    raw_dfs = [archive.load_dataframe(p) for p in paths]
    clean_dfs = [transform.run_cleaning_steps(df) for df in raw_dfs]
    df = pd.concat(clean_dfs)
    return df


if __name__ == '__main__':

    zipcodes = [int(x) for x in sys.argv[1:] if x.isnumeric()]
    forsale_files = {z: f'./archive/{z}/forsale_raw.gz' for z in zipcodes}
    sold_files = {z: f'./archive/{z}/sold_raw.gz' for z in zipcodes}
    estate_dirs = {z: f'./archive/{z}/estate_raw' for z in zipcodes}

    for z in zipcodes:
        print(f'updating archive data for zipcode {z}')
        update_archive(z, forsale_files[z], sold_files[z], estate_dirs[z])

    df_forsale = read_dataframes_and_concat(forsale_files.values())
    df_sold = read_dataframes_and_concat(sold_files.values())
    df_estate = read_dataframes_and_concat(estate_dirs.values())

    merge_data_and_save_to_file(df_forsale, df_estate, './archive', 'forsale')
    merge_data_and_save_to_file(df_sold, df_estate, './archive', 'sold')
