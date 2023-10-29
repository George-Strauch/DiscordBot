import requests
import pandas as pd
import os
import hashlib
from io import BytesIO
from base64 import b64encode
import datetime

WARN_URL = "https://www.twc.texas.gov/sites/default/files/oei/docs/warn-act-listings-2023-twc.xlsx"
SEEN_FILE = "data/seen_warn_entries.txt"


def get_warn():
    """
    Gets warn notice for texas
    https://www.dol.gov/agencies/eta/layoffs/warn
    :return: (string) formatted table of new, unseen layoffs
    """
    response = requests.get(WARN_URL)
    print(response.status_code)
    if response.status_code // 100 == 2:
        print("successfully retrieved warn data")
        # fname = "../data/warn.xls"
        # with open(fname, "wb") as writer:
        #     writer.write(response.content)
        return response.content
    else:
        print(f"Failed: {response.status_code}")
        return False


def clean(s):
    if not isinstance(s, str):
        return ""
    s = s.split(" (")[0]
    s = s.replace("  ", "")
    return s


def uid(data):
    data = data.encode("utf-8")
    data = b64encode(data)
    return str(hashlib.sha256(data).hexdigest())


def parse(data, previous_hash_file=None):
    _new = []
    previous = []
    if previous_hash_file:
        if os.path.exists(previous_hash_file):
            with open(previous_hash_file, 'r') as fp:
                previous = fp.readlines()
                previous = [x.replace("\n", "") for x in previous]
        else:
            with open(previous_hash_file, 'w') as fp:
                fp.writelines([""])
                previous = []

    df = pd.read_excel(data)
    layoffs = {}
    for i, row in df.iterrows():
        notice_date = str(row["NOTICE_DATE"]).split(" ")[0]
        lo_date = str(row["LayOff_Date"]).split(" ")[0]
        n = str(row["TOTAL_LAYOFF_NUMBER"]).ljust(3)
        company = clean(row["JOB_SITE_NAME"])
        city = row["CITY_NAME"].upper()
        s = f'[{notice_date}]  | n={n}  |  date=[{lo_date}]  |  {company}'
        h = uid(s)
        if h in previous:
            continue
        else:
            _new.append(h+"\n")
        if city not in layoffs:
            layoffs[city] = [s]
        else:
            layoffs[city].append(s)

    with open(previous_hash_file, 'a') as fp:
        fp.writelines(_new)

    if len(layoffs.keys()) > 0:
        layoff_str = "WARN NOTICES:"
        for city, los in layoffs.items():
            layoff_str += "\n" + city
            for l in los:
                layoff_str += f"\n\t{l}"
        print(len(layoff_str))
        if len(layoff_str) > 2000:
            return f"Many new warn notices, check {WARN_URL}"
        layoff_str = layoff_str.replace("\n", "\n\t")
    else:
        layoff_str = "No new notices"

    now = str(datetime.datetime.now()).split(" ")[0]
    return f"[{now}] {layoff_str}"


def get_new_warn_data():
    data = get_warn()
    data = BytesIO(data)
    return parse(data=data, previous_hash_file=SEEN_FILE)


if __name__ == '__main__':
    SEEN_FILE = f"../{SEEN_FILE}"
    print(get_new_warn_data())
