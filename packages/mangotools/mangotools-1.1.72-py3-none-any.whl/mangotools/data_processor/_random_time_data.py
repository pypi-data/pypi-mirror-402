# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description:
# @Time   : 2023-03-07 8:24
# @Author : 毛鹏
import random
from datetime import date, timedelta, datetime

import time
from faker import Faker


class RandomTimeData:
    """ 随机时间类型测试数据 """
    faker = Faker(locale='zh_CN')

    @classmethod
    def time_now_ymdhms(cls, minute=0) -> str:
        """当前年月日时分秒,参数：minute（默认0）"""
        target_time = datetime.now() + timedelta(days=int(minute))
        return target_time.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def time_random_utcnow(cls):
        """当前UTC时间字符串（YYYY-MM-DD HH:MM:SSZ）"""
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    @classmethod
    def time_now_ymd(cls, days=0):
        """当前年月日,参数：days（默认0）"""
        yesterday = datetime.now() + timedelta(days=int(days))
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        return yesterday_str

    @classmethod
    def time_now_hms(cls, minutes: int = 0) -> str:
        """当前时分秒，参数：minutes（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(minutes=int(minutes))
        return target_time.strftime('%H:%M:%S')

    @classmethod
    def time_now_ymd_h(cls, hours: int = 0) -> str:
        """当前年月日时，参数：hours（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(hours=int(hours))
        return target_time.strftime('%Y-%m-%d %H')

    @classmethod
    def time_now_ymd_hm(cls, minutes: int = 0) -> str:
        """当前年月日时分，参数：minutes（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(minutes=int(minutes))
        return target_time.strftime('%Y-%m-%d %H:%M')

    @classmethod
    def time_stamp(cls, minute=0) -> int:
        """几分钟后的时间戳, 参数：minute（默认0）"""
        return int(time.time() + 60 * int(minute)) * 1000

    @classmethod
    def time_next_minute(cls, minute=0) -> str:
        """几分钟后的年月日时分秒 参数：分钟（默认0）"""
        future_time = datetime.now() + timedelta(minutes=int(minute))
        return future_time.strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def time_now_year(cls, days: int = 0) -> str:
        """获取当前年份，参数：days（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(days=int(days))
        return target_time.strftime('%Y')

    @classmethod
    def time_now_month(cls, days: int = 0) -> str:
        """获取当前月份，参数：days（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(days=int(days))
        return target_time.strftime('%m')

    @classmethod
    def time_now_day(cls, days: int = 0) -> str:
        """获取当前日期，参数：days（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(days=int(days))
        return target_time.strftime('%d')

    @classmethod
    def time_now_hour(cls, hours: int = 0) -> str:
        """获取当前小时，参数：hours（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(hours=int(hours))
        return target_time.strftime('%H')

    @classmethod
    def time_now_minute(cls, minutes: int = 0) -> str:
        """获取当前分钟，参数：minutes（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(minutes=int(minutes))
        return target_time.strftime('%M')

    @classmethod
    def time_now_second(cls, seconds: int = 0) -> str:
        """获取当前秒，参数：seconds（默认0），可为正数（未来时间）或负数（过去时间）"""
        target_time = datetime.now() + timedelta(seconds=int(seconds))
        return target_time.strftime('%S')

    @classmethod
    def time_random_year(cls):
        """获取随机年份"""
        return cls.faker.year()

    @classmethod
    def time_random_month(cls):
        """获取随机月份"""
        return cls.faker.month()

    @classmethod
    def time_random_date(cls):
        """获取随机日期"""
        return cls.faker.date()

    @classmethod
    def time_now_int(cls) -> int:
        """获取当前时间戳整形"""
        return int(time.time()) * 1000

    @classmethod
    def time_future_date(cls):
        """未来的随机年月日"""
        return cls.faker.future_date()

    @classmethod
    def time_future_datetime(cls):
        """未来的随机年月日时分秒"""
        return cls.faker.future_datetime()

    @classmethod
    def time_today_date_00(cls):
        """获取今日00:00:00时间"""
        _today = date.today().strftime("%Y-%m-%d") + " 00:00:00"
        return str(_today)

    @classmethod
    def time_today_date_59(cls):
        """获取今日23:59:59时间"""
        _today = date.today().strftime("%Y-%m-%d") + " 23:59:59"
        return str(_today)

    @classmethod
    def time_after_week(cls):
        """获取一周后12点整的时间"""
        _time_after_week = (date.today() + timedelta(days=+6)).strftime("%Y-%m-%d") + " 00:00:00"
        return _time_after_week

    @classmethod
    def time_after_month(cls):
        """获取30天后的12点整时间"""
        _time_after_week = (date.today() + timedelta(days=+30)).strftime("%Y-%m-%d") + " 00:00:00"
        return _time_after_week

    @classmethod
    def time_random_year_str(cls):
        """随机年份字符串"""
        return str(cls.faker.year())

    @classmethod
    def time_random_month_str(cls):
        """随机月份字符串（01-12）"""
        return f"{random.randint(1, 12):02d}"

    @classmethod
    def time_random_day_str(cls):
        """随机日字符串（01-31）"""
        return f"{random.randint(1, 31):02d}"

    @classmethod
    def time_random_hour_str(cls):
        """随机小时字符串（00-23）"""
        return f"{random.randint(0, 23):02d}"

    @classmethod
    def time_random_minute_str(cls):
        """随机分钟字符串（00-59）"""
        return f"{random.randint(0, 59):02d}"

    @classmethod
    def time_random_second_str(cls):
        """随机秒字符串（00-59）"""
        return f"{random.randint(0, 59):02d}"

    @classmethod
    def time_random_ym(cls):
        """随机年月字符串（YYYY-MM）"""
        return f"{cls.faker.year()}-{random.randint(1, 12):02d}"

    @classmethod
    def time_random_ymd_str(cls):
        """随机年月日字符串（YYYY-MM-DD）"""
        return cls.faker.date()

    @classmethod
    def time_random_ymdhm_str(cls):
        """随机年月日时分字符串（YYYY-MM-DD HH:MM）"""
        dt = cls.faker.date_time()
        return dt.strftime('%Y-%m-%d %H:%M')

    @classmethod
    def time_random_ymdhms_str(cls):
        """随机年月日时分秒字符串（YYYY-MM-DD HH:MM:SS）"""
        dt = cls.faker.date_time()
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def time_random_hm_str(cls):
        """随机时分字符串（HH:MM）"""
        return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"

    @classmethod
    def time_random_hms_str(cls):
        """随机时分秒字符串（HH:MM:SS）"""
        return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

    @classmethod
    def time_random_timestamp_s(cls):
        """随机时间戳（秒）"""
        dt = cls.faker.date_time()
        return int(dt.timestamp())

    @classmethod
    def time_random_timestamp_ms(cls):
        """随机时间戳（毫秒）"""
        dt = cls.faker.date_time()
        return int(dt.timestamp() * 1000)

    @classmethod
    def time_random_timestamp_us(cls):
        """随机时间戳（微秒）"""
        dt = cls.faker.date_time()
        return int(dt.timestamp() * 1000000)

    @classmethod
    def time_random_iso8601(cls):
        """随机ISO8601时间字符串"""
        return cls.faker.iso8601()

    @classmethod
    def time_random_rfc3339(cls):
        """随机RFC3339时间字符串"""
        return cls.faker.date_time().isoformat()

    @classmethod
    def time_random_future_ymd(cls):
        """未来随机年月日字符串"""
        return cls.faker.future_date().strftime('%Y-%m-%d')

    @classmethod
    def time_random_past_ymd(cls):
        """过去随机年月日字符串"""
        return cls.faker.past_date().strftime('%Y-%m-%d')

    @classmethod
    def time_random_future_ymdhms(cls):
        """未来随机年月日时分秒字符串"""
        return cls.faker.future_datetime().strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def time_random_past_ymdhms(cls):
        """过去随机年月日时分秒字符串"""
        return cls.faker.past_datetime().strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def time_random_weekday(cls):
        """随机周几（中文）"""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return random.choice(weekdays)

    @classmethod
    def time_random_weekday_num(cls):
        """随机周几（数字1-7）"""
        return random.randint(1, 7)

    @classmethod
    def time_random_quarter(cls):
        """随机季度（Q1-Q4）"""
        return f"Q{random.randint(1, 4)}"

    @classmethod
    def time_random_12h(cls):
        """随机12小时制时间字符串（hh:MM:SS AM/PM）"""
        dt = cls.faker.date_time()
        return dt.strftime('%I:%M:%S %p')

    @classmethod
    def time_random_time_range_str(cls):
        """随机时间区间字符串（如'2023-01-01~2023-01-31'）"""
        start = cls.faker.date_this_year()
        end = cls.faker.future_date(end_date='+30d')
        return f"{start}~{end}"

    @classmethod
    def time_random_utc_offset(cls):
        """随机UTC偏移字符串（如+08:00）"""
        sign = random.choice(['+', '-'])
        hour = random.randint(0, 14)
        minute = random.choice([0, 30, 45])
        return f"{sign}{hour:02d}:{minute:02d}"

    @classmethod
    def time_random_rfc2822(cls):
        """随机RFC2822时间字符串"""
        return cls.faker.date_time().strftime('%a, %d %b %Y %H:%M:%S +0000')

    @classmethod
    def time_random_rfc850(cls):
        """随机RFC850时间字符串"""
        return cls.faker.date_time().strftime('%A, %d-%b-%y %H:%M:%S GMT')

    @classmethod
    def time_random_rfc1123(cls):
        """随机RFC1123时间字符串"""
        return cls.faker.date_time().strftime('%a, %d %b %Y %H:%M:%S GMT')

    @classmethod
    def time_random_rfc1036(cls):
        """随机RFC1036时间字符串"""
        return cls.faker.date_time().strftime('%A, %d-%b-%y %H:%M:%S GMT')

    @classmethod
    def time_random_rfc822(cls):
        """随机RFC822时间字符串"""
        return cls.faker.date_time().strftime('%a, %d %b %y %H:%M:%S +0000')

    @classmethod
    def time_random_rfc3339nano(cls):
        """随机RFC3339纳秒时间字符串"""
        dt = cls.faker.date_time()
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    @classmethod
    def time_cron_time(cls, time_parts) -> str:
        """秒级cron表达式,参数：time_parts"""
        seconds = int(time_parts[0])
        minutes = int(time_parts[1])
        hours = int(time_parts[2])
        current_date = datetime.now().date()
        date_obj = datetime(year=current_date.year,
                            month=current_date.month,
                            day=current_date.day,
                            hour=hours,
                            minute=minutes,
                            second=seconds)

        time_str_result = date_obj.strftime("%H:%M:%S")
        return time_str_result

    @classmethod
    def time_next_minute_cron(cls, minutes=1):
        """按周重复的cron表达式,参数：minutes（默认1）"""
        now = datetime.now() + timedelta(minutes=float(minutes))
        second = f"{now.second:02d}"  # 格式化为两位数
        minute = f"{now.minute:02d}"  # 格式化为两位数
        hour = f"{now.hour:02d}"  # 格式化为两位数
        day = "?"  # 日用问号表示不指定
        month = "*"  # 月用星号表示每个月
        weekday = str(date.today().weekday() + 2)
        return f"{second} {minute} {hour} {day} {month} {weekday}"

    @classmethod
    def time_random_cron(cls):
        """随机cron表达式（分 时 日 月 周）"""
        minute = random.randint(0, 59)
        hour = random.randint(0, 23)
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        week = random.randint(0, 6)
        return f"{minute} {hour} {day} {month} {week}"
