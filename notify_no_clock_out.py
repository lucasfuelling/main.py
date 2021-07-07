#!/usr/bin/env python
import sqlite3
from datetime import datetime
from datetime import timedelta
from sqlite3 import Error
import requests
import mariadb
import sys

token = "hSoXRRGQiiKDkmvptJTk5rph7UIv50ZqB2vb4IJ0MgK"


def line_notify_message(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
    return r.status_code


def connect_to_mariadb():
    try:
        conn = mariadb.connect(
            user="jiou99",
            password="jiou99",
            host="localhost",
            port=3306,
            database="attendance"
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    return conn


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def forget_clock_out():
    global token
    database = r"Timeclock.db"
    #conn = create_connection(database)
    conn = connect_to_mariadb()
    cur = conn.cursor()
    yesterday = datetime.now() - timedelta(days=1)
    sql = "SELECT username FROM attendance WHERE clockout is NULL AND clockday =?"
    par = (yesterday.strftime("%Y-%m-%d"),)
    cur.execute(sql, par)
    rows = cur.fetchall()
    for row in rows:
        line_notify_message(token, row[0] + " 忘記打卡")


if __name__ == '__main__':
    forget_clock_out()