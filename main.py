from mailer import send_mail
import fnmatch
import logging
import logging.config
import os
import traceback
from datetime import datetime, timedelta
from io import StringIO

import numpy as np
import pandas as pd
import requests


dname = os.path.dirname(__file__)
os.chdir(dname)

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)

logger = logging.getLogger(__name__)

READ_KEY = ""
PM25_ALERT_THRESHOLD = 10
SENSORS_FILE = "Station_List_2_Dimotiko.csv"
INTERVAL_MINUTES = 15


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
    logger.debug(
        f"Sensor ID: {sensor_id}, Response status: {resp.status_code}")
    data = StringIO(resp.text)
    df = pd.read_csv(data, parse_dates=True, index_col="time_stamp")
    logger.info(f"Retrieved {len(df)} records for sensor id: {sensor_id}")
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


def calc_pm25(df, sensor_name):
    if sensor_name == "2o Dhmotiko Thermis":
        df["pm2.5"] = df["pm2.5_cf_1_b"]
    else:
        df["pm2.5"] = df[["pm2.5_cf_1_a", "pm2.5_cf_1_b"]].mean(axis=1)
        ratio = abs(df["pm2.5_cf_1_a"] - df["pm2.5_cf_1_b"]) / df["pm2.5"]
        df["pm2.5"][ratio > 0.2] = np.nan


def characterize_air_quality(pm_value):
    if pm_value < 10:
        return "Καλή"
    elif pm_value >= 10 and pm_value < 20:
        return "Ικανοποιητική"
    elif pm_value >= 20 and pm_value < 25:
        return "Μέτρια"
    elif pm_value >= 25 and pm_value < 50:
        return "Κακή"
    elif pm_value >= 50:
        return "Πολύ κακή"


def main():
    sensors = pd.read_csv(SENSORS_FILE, index_col="SN")
    utc_now = pd.to_datetime(datetime.utcnow(), utc=True)
    start_date = (utc_now - timedelta(minutes=INTERVAL_MINUTES)).strftime(
        "%Y-%m-%dT%XZ"
    )
    end_date = utc_now.strftime("%Y-%m-%dT%XZ")
    local_datetime = utc_now.tz_convert(
        "Europe/Athens").strftime("%d/%m/%Y %X")
    df_pm25 = pd.DataFrame(
        columns=[
            "Τοπική Ώρα",
            "Σταθμός",
            "PM2.5 (μg/m³)",
            "Κατάσταση ποιότητας αέρα",
        ]
    )
    for index, row in sensors.iterrows():
        sensor_id = row["ID"]
        sensor_name = row["Name"]
        df = download_historical(sensor_id, start=start_date, end=end_date)
        quality_control(df)
        calc_pm25(df, sensor_name)
        avg = round(df["pm2.5"].mean(), 1)
        air_quality = characterize_air_quality(avg)
        df_pm25.loc[len(df_pm25), df_pm25.columns] = (
            local_datetime,
            sensor_name,
            avg,
            air_quality,
        )
    if (df_pm25["PM2.5 (μg/m³)"] > PM25_ALERT_THRESHOLD).any():
        send_mail(df_pm25.to_html(index=False))
    else:
        logger.info("PM2.5 below threshold. Mail not sent.")
    logger.debug(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        main()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
