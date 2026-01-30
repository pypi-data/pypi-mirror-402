from datetime import date, datetime, timedelta, timezone
import calendar
import random
from zoneinfo import ZoneInfo


class DateUtils:
    """日期生成与处理工具类"""

    # ==================== 1. 获取当前日期/时间 ====================
    @staticmethod
    def get_current_date() -> date:
        """获取当前日期（date对象，仅年月日）"""
        return date.today()

    @staticmethod
    def get_current_datetime(tz: str | None = None) -> datetime:
        """获取当前datetime对象（可选时区）
        :param tz: 时区标识（如"Asia/Shanghai"、"America/New_York"）
        """
        if tz:
            return datetime.now(ZoneInfo(tz))
        return datetime.now()

    @staticmethod
    def get_current_datetime_to_str() -> str:
        """获取当前datetime对象（可选时区）
        """
        return str(DateUtils.get_current_datetime())


    @staticmethod
    def get_utc_now() -> datetime:
        """获取UTC标准时间（带时区信息）"""
        return datetime.utcnow().replace(tzinfo=timezone.utc)

    # ==================== 2. 生成指定日期/时间 ====================
    @staticmethod
    def get_specified_date(year: int, month: int, day: int) -> date | None:
        """生成指定日期（date对象），无效日期返回None"""
        try:
            return date(year, month, day)
        except ValueError as e:
            print(f"❌ 无效日期：{year}-{month}-{day}，错误：{e}")
            return None

    @staticmethod
    def get_specified_datetime(
        year: int, month: int, day: int,
        hour: int = 0, minute: int = 0, second: int = 0,
        tz: str | None = None
    ) -> datetime | None:
        """生成指定datetime对象（可选时区），无效参数返回None"""
        try:
            dt = datetime(year, month, day, hour, minute, second)
            if tz:
                dt = dt.replace(tzinfo=ZoneInfo(tz))
            return dt
        except ValueError as e:
            print(f"❌ 无效日期时间：{year}-{month}-{day} {hour}:{minute}:{second}，错误：{e}")
            return None

    @staticmethod
    def str_to_date(date_str: str, format_str: str = "%Y-%m-%d") -> date | None:
        """字符串转date对象
        :param date_str: 日期字符串（如"2025-01-01"）
        :param format_str: 字符串格式（默认"%Y-%m-%d"）
        """
        try:
            return datetime.strptime(date_str, format_str).date()
        except ValueError as e:
            print(f"❌ 日期字符串格式错误：{date_str}，预期格式：{format_str}，错误：{e}")
            return None

    # ==================== 3. 生成日期范围 ====================
    @staticmethod
    def get_last_n_days(n: int, include_today: bool = True) -> list[date]:
        """获取近N天的日期列表
        :param include_today: 是否包含今天（默认True）
        """
        today = date.today()
        if include_today:
            return [today - timedelta(days=i) for i in range(n)]
        return [today - timedelta(days=i+1) for i in range(n)]

    @staticmethod
    def get_date_range(
        start_date: date | str,
        end_date: date | str,
        format_str: str = "%Y-%m-%d"
    ) -> list[date]:
        """获取起止日期之间的所有日期（包含两端）"""
        # 处理字符串输入
        if isinstance(start_date, str):
            start_date = DateUtils.str_to_date(start_date, format_str)
        if isinstance(end_date, str):
            end_date = DateUtils.str_to_date(end_date, format_str)

        if not start_date or not end_date or start_date > end_date:
            print("❌ 起止日期无效或起始日期大于结束日期")
            return []

        delta = end_date - start_date
        return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

    @staticmethod
    def get_days_in_month(year: int, month: int) -> list[date]:
        """获取指定年月的所有日期"""
        try:
            days_count = calendar.monthrange(year, month)[1]  # 获取当月天数
            return [date(year, month, day) for day in range(1, days_count + 1)]
        except ValueError as e:
            print(f"❌ 无效年月：{year}-{month}，错误：{e}")
            return []

    # ==================== 4. 生成随机日期 ====================
    @staticmethod
    def get_random_date(
        start_date: date | str,
        end_date: date | str,
        format_str: str = "%Y-%m-%d"
    ) -> date | None:
        """生成指定范围内的随机日期"""
        date_range = DateUtils.get_date_range(start_date, end_date, format_str)
        if not date_range:
            return None
        return random.choice(date_range)

    @staticmethod
    def get_random_datetime(
        start_dt: datetime | str,
        end_dt: datetime | str,
        format_str: str = "%Y-%m-%d %H:%M:%S"
    ) -> datetime | None:
        """生成指定范围内的随机datetime"""
        # 处理字符串输入
        if isinstance(start_dt, str):
            try:
                start_dt = datetime.strptime(start_dt, format_str)
            except ValueError:
                print(f"❌ 起始时间格式错误：{start_dt}")
                return None
        if isinstance(end_dt, str):
            try:
                end_dt = datetime.strptime(end_dt, format_str)
            except ValueError:
                print(f"❌ 结束时间格式错误：{end_dt}")
                return None

        if start_dt >= end_dt:
            print("❌ 起始时间大于等于结束时间")
            return None

        delta = end_dt - start_dt
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start_dt + timedelta(seconds=random_seconds)

    # ==================== 5. 日期计算 ====================
    @staticmethod
    def add_days(base_date: date | datetime, days: int) -> date | datetime:
        """日期加N天"""
        return base_date + timedelta(days=days)

    @staticmethod
    def subtract_days(base_date: date | datetime, days: int) -> date | datetime:
        """日期减N天"""
        return base_date - timedelta(days=days)

    @staticmethod
    def get_month_start(year: int | None = None, month: int | None = None) -> date:
        """获取指定年月的月初日期（默认当前年月）"""
        year = year or date.today().year
        month = month or date.today().month
        return date(year, month, 1)

    @staticmethod
    def get_month_end(year: int | None = None, month: int | None = None) -> date:
        """获取指定年月的月末日期（默认当前年月）"""
        year = year or date.today().year
        month = month or date.today().month
        days_count = calendar.monthrange(year, month)[1]
        return date(year, month, days_count)

    @staticmethod
    def get_quarter_start(year: int | None = None, quarter: int | None = None) -> date:
        """获取指定年季度的起始日期（默认当前年当前季度）
        :param quarter: 季度（1-4）
        """
        year = year or date.today().year
        quarter = quarter or (date.today().month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        return date(year, start_month, 1)

    # ==================== 6. 日期格式化 ====================
    @staticmethod
    def date_to_str(date_obj: date | datetime, format_str: str = "%Y-%m-%d") -> str:
        """日期/时间对象转字符串"""
        return date_obj.strftime(format_str)

    # ==================== 7. 时区转换 ====================
    @staticmethod
    def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """转换时区
        :param dt: 原始时间对象（若无时区信息，需指定from_tz）
        :param from_tz: 原始时区
        :param to_tz: 目标时区
        """
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=ZoneInfo(from_tz))
        return dt.astimezone(ZoneInfo(to_tz))

# ==================== 原有基础功能（省略，保持之前的方法） ====================
    # （注：若需完整代码，需包含之前的get_current_date、get_specified_date等方法）

    # ==================== 新增：时间戳相关功能 ====================
    @staticmethod
    def get_current_timestamp(precision: str = "millisecond") -> int:
        """获取当前时间戳
        :param precision: 精度（"second"=秒级，"millisecond"=毫秒级）
        :return: 时间戳整数
        """
        now = datetime.now()
        if precision == "millisecond":
            return int(now.timestamp() * 1000)
        return int(now.timestamp())

    @staticmethod
    def get_utc_timestamp(precision: str = "second") -> int:
        """获取当前UTC时间戳
        :param precision: 精度（"second"=秒级，"millisecond"=毫秒级）
        :return: UTC时间戳整数
        """
        utc_now = datetime.utcnow()
        if precision == "millisecond":
            return int(utc_now.timestamp() * 1000)
        return int(utc_now.timestamp())

    @staticmethod
    def timestamp_to_datetime(
        timestamp: int,
        precision: str = "second",
        tz: str | None = None
    ) -> datetime | None:
        """时间戳转datetime对象（支持时区）
        :param timestamp: 时间戳（整数）
        :param precision: 时间戳精度（"second"=秒级，"millisecond"=毫秒级）
        :param tz: 时区（如"Asia/Shanghai"，None则为本地时区）
        :return: datetime对象（带时区信息，若指定tz）
        """
        try:
            # 转换毫秒级时间戳为秒级
            ts = timestamp / 1000 if precision == "millisecond" else timestamp
            dt = datetime.fromtimestamp(ts)
            # 设置时区
            if tz:
                dt = dt.replace(tzinfo=ZoneInfo(tz))
            return dt
        except ValueError as e:
            print(f"❌ 无效时间戳：{timestamp}，错误：{e}")
            return None

    @staticmethod
    def datetime_to_timestamp(
        dt: datetime,
        precision: str = "second"
    ) -> int | None:
        """datetime对象转时间戳
        :param dt: datetime对象（若带时区，会自动转换为UTC时间戳）
        :param precision: 精度（"second"=秒级，"millisecond"=毫秒级）
        :return: 时间戳整数
        """
        try:
            ts = dt.timestamp()
            return int(ts * 1000) if precision == "millisecond" else int(ts)
        except ValueError as e:
            print(f"❌ 无效datetime对象：{dt}，错误：{e}")
            return None

    @staticmethod
    def timestamp_to_str(
        timestamp: int,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        precision: str = "second",
        tz: str | None = None
    ) -> str | None:
        """时间戳转格式化字符串
        :param timestamp: 时间戳（整数）
        :param format_str: 输出格式（默认"%Y-%m-%d %H:%M:%S"）
        :param precision: 时间戳精度（"second"=秒级，"millisecond"=毫秒级）
        :param tz: 时区（如"Asia/Shanghai"）
        :return: 格式化日期字符串
        """
        dt = DateUtils.timestamp_to_datetime(timestamp, precision, tz)
        if dt:
            return dt.strftime(format_str)
        return None

    @staticmethod
    def str_to_timestamp(
        date_str: str,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        precision: str = "second",
        tz: str | None = None
    ) -> int | None:
        """格式化字符串转时间戳
        :param date_str: 日期字符串（如"2025-01-01 12:00:00"）
        :param format_str: 输入格式（默认"%Y-%m-%d %H:%M:%S"）
        :param precision: 输出精度（"second"=秒级，"millisecond"=毫秒级）
        :param tz: 时区（如"Asia/Shanghai"，None则为本地时区）
        :return: 时间戳整数
        """
        try:
            dt = datetime.strptime(date_str, format_str)
            if tz:
                dt = dt.replace(tzinfo=ZoneInfo(tz))
            return DateUtils.datetime_to_timestamp(dt, precision)
        except ValueError as e:
            print(f"❌ 日期字符串格式错误：{date_str}，错误：{e}")
            return None

    @staticmethod
    def get_random_timestamp(
        start_ts: int,
        end_ts: int,
        precision: str = "second"
    ) -> int | None:
        """生成指定时间戳范围内的随机时间戳
        :param start_ts: 起始时间戳
        :param end_ts: 结束时间戳
        :param precision: 精度（"second"=秒级，"millisecond"=毫秒级）
        :return: 随机时间戳
        """
        if start_ts >= end_ts:
            print("❌ 起始时间戳大于等于结束时间戳")
            return None
        # 毫秒级需处理范围
        multiplier = 1000 if precision == "millisecond" else 1
        random_ts = random.randint(start_ts * multiplier, end_ts * multiplier)
        return random_ts if precision == "millisecond" else random_ts // multiplier