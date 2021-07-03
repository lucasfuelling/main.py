#!/usr/bin/env python
import sqlite3
from datetime import datetime
from datetime import timedelta
from sqlite3 import Error
import time
import csv
from threading import Thread
import requests

thread_running = True


def line_notify_message(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
    return r.status_code


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


def insert_user(conn, namechip):
    cur = conn.cursor()
    sql = ''' INSERT INTO users(Name,ChipNo) VALUES(?,?)'''
    cur.execute(sql, namechip)
    conn.commit()
    print("輸入ok")


def update_user(conn, namechip):
    cur = conn.cursor()
    sql = '''UPDATE users SET name =? WHERE chipno=?'''
    cur.execute(sql, namechip)
    conn.commit()
    print("輸入ok")


def user_exists(conn, mychip):
    cur = conn.cursor()
    sql = "SELECT userid FROM users WHERE chipno=?"
    par = (mychip,)
    cur.execute(sql, par)
    if cur.fetchone():
        return bool(True)
    else:
        return bool(False)


def user_clocked(conn, mychip):
    cur = conn.cursor()
    todays_date = datetime.now().strftime("%Y-%m-%d")
    sql = "SELECT userid FROM attendance INNER JOIN users USING(userid) WHERE clockout is NULL AND chipno=? AND day =?"
    par = (mychip, todays_date)
    cur.execute(sql, par)
    if cur.fetchone():
        return bool(True)
    else:
        return bool(False)


def short_clock_in_time(conn, mychip):
    cur = conn.cursor()
    todays_date = datetime.now().strftime("%Y-%m-%d")
    one_minutes_ago = datetime.now() - timedelta(minutes=1)
    sql = "SELECT clockin FROM attendance INNER JOIN users USING(userid) WHERE (clockout >= ? OR clockin >= ?) AND " \
          "chipno=? AND day =? "
    par = (one_minutes_ago.strftime("%H:%M"), one_minutes_ago.strftime("%H:%M"), mychip, todays_date)
    cur.execute(sql, par)
    if cur.fetchone():
        return bool(True)
    else:
        return bool(False)


def add_user(conn):
    mychip = input("新员工 \n请放卡:")
    if user_exists(conn, mychip):
        yesno = input("User exists\n覆蓋名字?[1=是/0=否]:")
        if yesno == "1":
            new_name = input("輸入新名字:")
            update_user(conn, (new_name, mychip))
    else:
        name = input("輸入名字:")
        insert_user(conn, (name, mychip))


def attendance_come(conn, mychip):
    if not short_clock_in_time(conn, mychip):
        par = (mychip,)
        come_time = datetime.now().strftime("%H:%M")
        todays_date = datetime.now().strftime("%Y-%m-%d")
        cur = conn.cursor()
        sql = "SELECT userid, name FROM users WHERE chipno = ?"
        cur.execute(sql, par)
        userid, name = cur.fetchone()
        sql = "INSERT INTO attendance(userid, username, day, clockin)" \
              "VALUES (?,?,?,?)"
        par = (userid, name, todays_date, come_time)
        cur.execute(sql, par)
        conn.commit()
        print(name + " " + come_time + " " + "上班")
        if datetime.now() > datetime.now().replace(hour=8, minute=0):
            token = "hSoXRRGQiiKDkmvptJTk5rph7UIv50ZqB2vb4IJ0MgK"
            msg = name + " 上班 " + come_time
            line_notify_message(token, msg)
    else:
        print("已打卡了")


def attendance_go(conn, mychip):
    if not short_clock_in_time(conn, mychip):
        par = (mychip,)
        go_time = datetime.now().strftime("%H:%M")
        todays_date = datetime.now().strftime("%Y-%m-%d")
        cur = conn.cursor()
        sql = "SELECT userid, name FROM users WHERE chipno = ?"
        cur.execute(sql, par)
        userid, name = cur.fetchone()
        sql = "UPDATE attendance SET clockout = ? WHERE userid = ? AND clockout is NULL AND day = ?"
        par = (go_time, userid, todays_date)
        cur.execute(sql, par)
        conn.commit()
        print(name + " " + go_time + " " + "下班")
    else:
        print("已打卡了")


def export_data(conn):
    month = datetime.now().month
    year = datetime.now().year - 1911
    str_year = str(year)
    str_month = str(month).zfill(2)
    cur = conn.cursor()
    csv_writer = csv.writer(open("打卡-" + str_year + "-" + str_month + ".csv", "w", encoding='utf-8-sig', newline=''))
    sql = "SELECT username, day, clockin, clockout FROM attendance WHERE strftime('%m', day) = ? ORDER BY userid ASC, " \
          "day ASC "
    par = (str_month,)
    cur.execute(sql, par)
    rows = cur.fetchall()
    csv_writer.writerow(["Name", "Date", "Come", "Go"])
    csv_writer.writerows(rows)


def reader():
    global thread_running
    database = r"Timeclock.db"
    conn = create_connection(database)
    mychip = input()
    thread_running = False
    if user_exists(conn, mychip) or mychip == "0":
        if mychip != "0":
            if user_clocked(conn, mychip):
                attendance_go(conn, mychip)
                export_data(conn)
            else:
                attendance_come(conn, mychip)
        else:
            add_user(conn)
    else:
        print("沒有找到用戶")
    time.sleep(1)


def show_time():
    global thread_running
    while thread_running:
        now = datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M"))
        time.sleep(60)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    while True:
        thread_running = True
        t1 = Thread(target=show_time)
        t2 = Thread(target=reader)
        t1.start()
        t2.start()
        t2.join()
