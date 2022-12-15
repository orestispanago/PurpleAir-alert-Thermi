import datetime
from io import StringIO

import pandas as pd
import requests

from mailer import send_mail

READ_KEY = ""


def download_historical(sensor_id):
    url = (
        f"https://api.purpleair.com/v1/sensors/{sensor_id}/history/csv?"
        f"start_timestamp={start_date}&"
        f"end_timestamp={end_date}&"
        f"average=0&"
        f"fields=pm1.0_cf_1_a,"
        f"pm1.0_cf_1_b,"
        f"pm2.5_cf_1_a,"
        f"pm2.5_cf_1_b,"
        f"pm10.0_cf_1_a,"
        f"pm10.0_cf_1_b,"
        f"pm1.0_atm_a,"
        f"pm1.0_atm_b,"
        f"pm2.5_atm_a,"
        f"pm2.5_atm_b,"
        f"pm10.0_atm_a,"
        f"pm10.0_atm_b,"
        f"latitude,"
        f"longitude"
    )
    resp = requests.get(url, headers={"x-api-key": READ_KEY})
    print(resp.status_code)
    data = StringIO(resp.text)
    df = pd.read_csv(data, parse_dates=True, index_col="time_stamp")
    df.sort_index(inplace=True)
    return df


df_sl = pd.read_csv("Station_List_2_Dimotiko.csv")
df_sl = df_sl.set_index("SN")
end_date = datetime.datetime.utcnow()
start_date = (end_date - datetime.timedelta(minutes=15)).strftime(
    "%Y-%m-%dT%XZ"
)
end_date = end_date.strftime("%Y-%m-%dT%XZ")

for index, row in df_sl.iterrows():
    sensor_id = row["ID"]
    sensor_name = row["Name"]
    print(sensor_name, sensor_id)
    df = download_historical(sensor_id)
    avg = df[["pm2.5_cf_1_a", "pm2.5_cf_1_b"]].mean(axis=1)
    avg = avg.mean()
    # if avg>45:
    #     send_mail(f"TEST ipervasi ston stathmo {sensor_name}")
# df_all.to_csv(f"Data/raw_data/{sensor_name}_{start_date}_{end_date}.csv")
