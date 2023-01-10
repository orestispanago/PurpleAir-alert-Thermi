import datetime
import fnmatch
from io import StringIO

import numpy as np
import pandas as pd
import requests

from mailer import send_mail

READ_KEY = ""


def download_historical(sensor_id, start="", end=""):
    url = (
        f"https://api.purpleair.com/v1/sensors/{sensor_id}/history/csv?"
        f"start_timestamp={start}&"
        f"end_timestamp={end}&"
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


def nan_where_cf_less_than_atm(df, cf_cols, atm_cols):
    for cf_col, atm_col in zip(cf_cols, atm_cols):
        df[df[cf_col] < df[atm_col]] = np.nan


def nan_particle_order(df):
    # Implement QC based on pm1>pm2.5>pm10
    # sensor A
    df[df["pm1.0_cf_1_a"] > df["pm2.5_cf_1_a"]] = np.nan
    df[df["pm1.0_cf_1_a"] > df["pm10.0_cf_1_a"]] = np.nan
    df[df["pm2.5_cf_1_a"] > df["pm10.0_cf_1_a"]] = np.nan
    # sensor B
    df[df["pm1.0_cf_1_b"] > df["pm2.5_cf_1_b"]] = np.nan
    df[df["pm1.0_cf_1_b"] > df["pm10.0_cf_1_b"]] = np.nan
    df[df["pm2.5_cf_1_b"] > df["pm10.0_cf_1_b"]] = np.nan


def nan_where_negative(df, cf_cols):
    for cf_col in cf_cols:
        df[df[cf_col] < 0] = np.nan


def apply_calibration_factor(df):
    df["pm1.0_cf_1_a"] = df["pm1.0_cf_1_a"] * 0.52 - 0.18
    df["pm1.0_cf_1_b"] = df["pm1.0_cf_1_b"] * 0.52 - 0.18
    df["pm2.5_cf_1_a"] = df["pm2.5_cf_1_a"] * 0.42 + 0.26
    df["pm2.5_cf_1_b"] = df["pm2.5_cf_1_b"] * 0.42 + 0.26
    df["pm10.0_cf_1_a"] = df["pm10.0_cf_1_a"] * 0.45 + 0.02
    df["pm10.0_cf_1_b"] = df["pm10.0_cf_1_b"] * 0.45 + 0.02
    # Correct calibrated data when pm1<0
    df.loc[df["pm1.0_cf_1_a"] < 16, "pm1.0_cf_1_a"] = df["pm1.0_cf_1_a"] + 0.18
    df.loc[df["pm1.0_cf_1_b"] < 16, "pm1.0_cf_1_b"] = df["pm1.0_cf_1_b"] + 0.18


def quality_control(df):
    df_cols = list(df)
    cf_cols = fnmatch.filter(df_cols, "*cf*")
    atm_cols = fnmatch.filter(df_cols, "*atm*")
    nan_where_cf_less_than_atm(df, cf_cols, atm_cols)
    nan_particle_order(df)
    nan_where_negative(df, cf_cols)
    nan_particle_order(df)


sensors = pd.read_csv("Station_List_2_Dimotiko.csv", index_col="SN")
utc_now = datetime.datetime.utcnow()
start_date = (utc_now - datetime.timedelta(minutes=15)).strftime("%Y-%m-%dT%XZ")
end_date = utc_now.strftime("%Y-%m-%dT%XZ")
local_datetime = pd.to_datetime(utc_now, utc=True).tz_convert("Europe/Athens")
local_datetime_formatted = local_datetime.strftime("%d/%m/%Y %X")

df_all = pd.DataFrame(columns=["Τοπική Ώρα", "Σταθμός", "PM2.5 (μg/m³)"])
for index, row in sensors.iterrows():
    sensor_id = row["ID"]
    sensor_name = row["Name"]
    print(sensor_name, sensor_id)
    df = download_historical(sensor_id, start=start_date, end=end_date)
    quality_control(df)

    if sensor_name == "2o Dhmotiko Thermis":
        df["pm2.5"] = df["pm2.5_cf_1_b"]
    else:
        df["pm2.5"] = df[["pm2.5_cf_1_a", "pm2.5_cf_1_b"]].mean(axis=1)
        ratio = abs(df["pm2.5_cf_1_a"] - df["pm2.5_cf_1_b"]) / df["pm2.5"]
        df["pm2.5"][ratio > 0.2] = np.nan
    avg = round(df["pm2.5"].mean(), 1)

    df_all = df_all.append(
        {
            "Τοπική Ώρα": local_datetime_formatted,
            "Σταθμός": sensor_name,
            "PM2.5 (μg/m³)": avg,
        },
        ignore_index=True,
    )
if (df_all["PM2.5 (μg/m³)"] > 10).any():
    send_mail(df_all.to_html(index=False))
