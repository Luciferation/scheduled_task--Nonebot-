import json
import random
import re
import datetime
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import get_bot
import time
json_path = r'aqua/plugins/scheduled_task/tasks.json'  # windows


# json_path = sys.path[0] + r"/task.json" # linux


class Task:
    scheduler: AsyncIOScheduler = None
    is_scheduler_running: bool = False
    tasks_dict = {}
    the_max_tasks_number = 1000
    is_task_id_available = [1 for i in range(the_max_tasks_number)]
    bot = None

    class __KEY:
        something: str = "something"
        time_appointed: str = "time_appointed"
        time_formatted: str = "time_formatted"
        time_relative_hour: str = "time_relative_hour"
        time_relative_minute: str = "time_relative_minute"
        time_relative_second: str = "time_relative_second"
        year_relative: str = "year_relative"
        year_absolute: str = "year_absolute"
        month_relative: str = "month_relative"
        month_absolute: str = "month_absolute"
        day_relative: str = "day_relative"
        day_absolute: str = "day_absolute"
        time_12_rough: str = "time_12_rough"
        time_12_hour: str = "time_12_hour"
        time_12_minute: str = "time_12_minute"
        time_12_second: str = "time_12_second"
        time_24_hour: str = "time_24_hour"
        time_24_minute: str = "time_24_minute"
        arabic: str = "arabic"
        chinese_1000: str = "chinese_1000"
        chinese_100: str = "chinese_100"
        chinese_10: str = "chinese_10"
        chinese_ten: str = "chinese_ten"  # 用来判断是否有十这个汉字
        chinese_1: str = "chinese_1"

    value_of_chinese = {
        '一': 1,
        '二': 2,
        '两': 2,
        '三': 3,
        '四': 4,
        '五': 5,
        '六': 6,
        '七': 7,
        '八': 8,
        '九': 9
    }

    def __init__(self, time_appointed: datetime, task_dict: dict, owner_id: str, is_error_task: bool = False):
        self.time_appointed: datetime = time_appointed
        self.task_dict = task_dict
        self.something: str = "None"
        self.is_error_task = is_error_task
        self.owner_id = owner_id
        self.task_id = self.get_task_id()
        self.analysed = False
        self.analyse_error = False
        self.miss_error = False
        self.analyse_task_dict()
        if not self.is_error_task:
            self.add_to_dict()
            print(Task.tasks_dict)
            Task.store_tasks_in_json()

    def get_task_id(self) -> str:
        for i in range(Task.the_max_tasks_number):
            if Task.is_task_id_available[i] == 1:
                Task.is_task_id_available[i] = 0
                return str(i)
        else:
            self.is_error_task = True
            return str(-1)

    # 分析任务字典, 设置something, 和timeAppointed
    def analyse_task_dict(self):
        if self.is_error_task:
            return
        # 解析事件
        something = self.task_dict["something"]
        if something is None:
            self.is_error_task = True
            return
        else:
            self.something = something
        # 解析时间
        # 几小时/ 几分钟/ 几秒后
        # r"(?P<time_relative_hour>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))个?小时)?)"
        self.__analyse_relative_hours()
        # r"(?P<time_relative_minute>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))分钟)?)"
        self.__analyse_relative_minutes()
        # r"(?P<time_relative_second>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))秒)?)"
        self.__analyse_relative_seconds()
        # ----------------- ↑ 测试通过
        # ----------------- ↓ 完善中
        # + r"("  # 年
        # + r"(?P<year_relative>明年)"
        if not self.analysed:
            try:
                now = datetime.datetime.now()
                year = now.year
                month = now.month
                day = now.day
                hour = now.hour
                minute = now.minute
                second = now.second
                year_relative = self.task_dict[Task.__KEY.year_relative]
                if year_relative == '明年':
                    year = now.year + 1
                # + r"|"
                # + r"(?P<year_absolute>(\d*年))"
                year_absolute = self.task_dict[Task.__KEY.year_absolute]
                if year_absolute is not None:
                    year = int(year_absolute[:-1])
                # + r")?"
                # + r"("  # 月
                # + r"(?P<month_relative>下个月|下下个月)"
                month_relative = self.task_dict[Task.__KEY.month_relative]
                if month_relative is not None:
                    if month_relative[1] == '下':
                        month = now.month + 2
                    elif month_relative[0] == '下':
                        month = now.month + 1
                # + r"|"
                # + r"(?P<month_absolute>(0?[1-9]|1[0-2])月)"
                month_absolute = self.task_dict[Task.__KEY.month_absolute]
                if month_absolute is not None:
                    month = int(month_absolute[:-1])
                # + r")?"
                # + r"("  # 日
                # + r"(?P<day_relative>(今天|明天|后天|周[一二三四五六七]))"
                # + r"|"
                day_relative = self.task_dict[Task.__KEY.day_relative]
                if day_relative in ["今天", "明天", "后天"]:
                    day = {
                              "今天": 0,
                              "明天": 1,
                              "后天": 2
                          }[day_relative] + now.day
                else:
                    if day_relative is not None:
                        weekday = Task.value_of_chinese[day_relative[-1]] - 1
                        the_weekday = now.weekday()  # 周一是0, 周日是7
                        if weekday >= the_weekday:
                            day = now.day + (weekday - the_weekday)
                        else:
                            day = now.day + (weekday - the_weekday + 7)
                # + r"(?P<day_absolute>(0?[1-9]|[1-2][0-9]|3[0-1])日)"
                day_absolute = self.task_dict[Task.__KEY.day_absolute]
                if day_absolute is not None:
                    day = int(day_absolute[:-1])
                # 12小时制
                # + r"(?P<time_12_rough>(早上|中午|下午|晚上))"
                time_12_rough = self.task_dict[Task.__KEY.time_12_rough]
                if time_12_rough is not None:
                    hour = {
                        "早上": 7,
                        "中午": 12,
                        "下午": 17,
                        "晚上": 20
                    }[self.task_dict[Task.__KEY.time_12_rough]]
                    # + r"(?P<time_12_hour>(0?[0-9]|1[0-2])(点|时))?"
                    time_12_hour = self.task_dict[Task.__KEY.time_12_hour]
                    if time_12_hour is not None:
                        hour = int(time_12_hour[:-1])
                        if time_12_rough == '晚上':
                            hour += 12
                    # + r"(?P<time_12_minute>(0?[0-9]|[1-5][0-9])分)?"
                    time_12_minute = self.task_dict[Task.__KEY.time_12_minute]
                    if time_12_minute is not None:
                        minute = int(time_12_minute[:-1])
                # 24小时制
                # + r"(?P<time_24_hour>(0?[0-9]|1[0-9]|2[0-3])(点|时))"
                time_24_hour = self.task_dict[Task.__KEY.time_24_hour]
                if time_24_hour is not None:
                    hour = int(time_24_hour[:-1])
                    # + r"(?P<time_24_minute>(0?[0-9]|[1-5][0-9])分)"
                    time_24_minute = self.task_dict[Task.__KEY.time_24_minute]
                    if time_24_minute is not None:
                        minute = int(time_24_minute[:-1])
                print(year, month, day, hour, minute)
                self.time_appointed = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute,
                                                        second=second)
                if self.time_appointed < now:
                    self.is_error_task = True
                    self.miss_error = True
            except Exception as result:
                print("分析失败")
                self.is_error_task = True
                self.analyse_error = True

    def __analyse_relative_hours(self):
        self.__analyse_relative('hours')

    def __analyse_relative_minutes(self):
        self.__analyse_relative('minutes')

    def __analyse_relative_seconds(self):
        self.__analyse_relative('seconds')

    def __analyse_relative(self, time_type: str):
        if time_type == 'hours':
            time_relative = self.task_dict[self.__KEY.time_relative_hour]
        elif time_type == 'minutes':
            time_relative = self.task_dict[self.__KEY.time_relative_minute]
        elif time_type == 'seconds':
            time_relative = self.task_dict[self.__KEY.time_relative_second]
        else:
            return
        if time_relative is not None:
            self.analysed = True
            # print("分析完毕~")
            time_relative_dict = re.match(  # 十比较特殊 因为可以说十二, 但是不能说百二
                r"((?P<arabic>[0-9]?[0-9]?[0-9]?[0-9])|((((?P<chinese_1000>[一二两三四五六七八九])千)?((?P<chinese_100>[一二两三四五六七八九])百?(?P<chinese_10>[一二三四五六七八九])?(?P<chinese_ten>十))?(?P<chinese_1>[一二两三四五六七八九])?)))",
                time_relative
            ).groupdict()
            # print(time_relative_dict)
            arabic = time_relative_dict[self.__KEY.arabic]
            if arabic is not None:
                self.time_appointed += datetime.timedelta(**{time_type: int(arabic)})
            else:
                chinese_1000 = time_relative_dict[self.__KEY.chinese_1000]
                if chinese_1000 is not None:
                    self.time_appointed += datetime.timedelta(**{time_type: self.value_of_chinese[chinese_1000] * 1000})
                chinese_100 = time_relative_dict[self.__KEY.chinese_100]
                if chinese_100 is not None:
                    self.time_appointed += datetime.timedelta(**{time_type: self.value_of_chinese[chinese_100] * 100})
                chinese_10 = time_relative_dict[self.__KEY.chinese_10]
                if chinese_10 is not None:
                    self.time_appointed += datetime.timedelta(**{time_type: self.value_of_chinese[chinese_10] * 10})
                else:
                    ten = time_relative_dict[self.__KEY.chinese_ten]
                    if ten is not None:
                        self.time_appointed += datetime.timedelta(**{time_type: 10})
                chinese_1 = time_relative_dict[self.__KEY.chinese_1]
                if chinese_1 is not None:
                    self.time_appointed += datetime.timedelta(**{time_type: self.value_of_chinese[chinese_1]})

    @staticmethod
    async def send_msg(msg: str, owner_id: str):
        #  这里为了真实, 会根据信息长度, 停顿
        len_of_msg = len(msg)
        time_pause = (len_of_msg + 1) / 20
        if time_pause > 1:
            time_pause = 1
        time.sleep(time_pause)

        await Task.bot.call_api(
            "send_private_msg",
            **{
                "message": msg,
                "user_id": owner_id,
            },
        )

    @staticmethod
    async def send_remind(something: str, owner_id: str, task_id: str):
        msg = random.choice(
            [
                "该" + something + "了",
                "是不是该" + something + "了?",
                "已经到" + something + "的时候了"
            ]
        )
        await Task.send_msg(msg=msg, owner_id=owner_id)
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()

    async def send_the_remind(self):
        msg = random.choice(
            [
                "该" + self.something + "了",
                "是不是该" + self.something + "了?",
                "已经到" + self.something + "的时候了"
            ]
        )
        await Task.send_msg(msg=msg, owner_id=self.owner_id)
        self.pop_from_dict()
        Task.store_tasks_in_json()

    @staticmethod
    async def send_miss(timestamp: float, something: str, owner_id: str, task_id: str):
        the_time = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = random.choice(
            [
                the_time + something + "错过了" + " 没关系吗?",
            ]
        )
        await Task.send_msg(msg=msg, owner_id=owner_id)
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()

    @staticmethod
    async def send_analyse_error(owner_id: str, task_id: str):
        msg = random.choice(
            [
                "果咩, 契约解析失败",
                "听不懂诶, 果咩"
            ]
        )
        await Task.send_msg(msg=msg, owner_id=owner_id)
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()

    @staticmethod
    async def set_task(time_appointed: datetime, something: str, owner_id: str, task_id: str):
        if time_appointed < datetime.datetime.now():
            await Task.send_miss(timestamp=time_appointed.timestamp(), something=something, owner_id=owner_id,
                                 task_id=task_id)
        else:
            Task.set_scheduler()
            Task.scheduler.add_job(Task.send_remind, 'date', next_run_time=time_appointed,
                                   kwargs={'something': something, 'owner_id': owner_id, 'task_id': task_id})
            print("成功设置定时任务 " + something)
            if not Task.is_scheduler_running:
                Task.scheduler.start()
                Task.is_scheduler_running = True

    async def set_the_task(self):
        if not self.is_error_task:
            Task.set_scheduler()
            Task.scheduler.add_job(self.send_the_remind, 'date', next_run_time=self.time_appointed)
            print("成功设置定时任务 " + self.something)
            Task.scheduler.print_jobs()
            if not Task.is_scheduler_running:
                Task.scheduler.start()
                Task.is_scheduler_running = True
        else:
            if self.time_appointed < datetime.datetime.now():
                await Task.send_miss(timestamp=self.time_appointed.timestamp(), something=self.something,
                                     owner_id=self.owner_id,
                                     task_id=self.task_id)
            elif self.analyse_error:
                await Task.send_analyse_error(
                    owner_id=self.owner_id,
                    task_id=self.task_id
                )

    @staticmethod
    def set_scheduler():
        if Task.scheduler is None:
            Task.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')

    @staticmethod
    def add_task_to_dict(owner_id: str, task_id: str, something: str, timestamp: float, time_formatted: str):
        if owner_id not in Task.tasks_dict:
            Task.tasks_dict[owner_id] = {
                task_id: {
                    'something': something,
                    'time_appointed': timestamp,
                    'time_formatted': time_formatted
                }
            }
        else:
            Task.tasks_dict[owner_id][task_id] = {
                'something': something,
                'time_appointed': timestamp,
                'time_formatted': time_formatted
            }

    def add_to_dict(self):
        Task.add_task_to_dict(self.owner_id, self.task_id, self.something, self.time_appointed.timestamp(),
                              self.time_appointed.strftime("%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def pop_task_from_dict(owner_id: str, task_id: str):
        if owner_id in Task.tasks_dict:
            Task.tasks_dict[owner_id].pop(task_id)
            if len(Task.tasks_dict[owner_id]) == 0:
                Task.tasks_dict.pop(owner_id)

    def pop_from_dict(self):
        Task.pop_task_from_dict(owner_id=self.owner_id, task_id=self.task_id)

    @staticmethod
    def store_tasks_in_json():
        print("保存中~")
        with open(json_path, 'w', encoding='UTF-8') as f:
            json.dump(Task.tasks_dict, f, sort_keys=True, indent=4, ensure_ascii=False)
            print("保存完毕")
            f.close()

    @staticmethod
    def load_from_json():
        with open(json_path, 'r', encoding='UTF-8') as f:
            Task.tasks_dict = json.load(f)
            f.close()

    @staticmethod
    async def set_tasks_from_dict():
        tasks_dict = Task.tasks_dict
        now = datetime.datetime.now().timestamp()
        for owner_id in list(tasks_dict.keys()):  # 迭代字典时修改字典会出错,
            if owner_id in tasks_dict:
                tasks = tasks_dict[owner_id]
                for task_id in list(tasks.keys()):
                    task_info = tasks[task_id]
                    Task.is_task_id_available[int(task_id)] = 0
                    await Task.set_task(
                        time_appointed=datetime.datetime.fromtimestamp(task_info['time_appointed']),
                        something=task_info['something'],
                        owner_id=owner_id,
                        task_id=task_id
                    )

    @staticmethod
    async def init():
        Task.bot = get_bot()
        Task.load_from_json()
        Task.set_scheduler()
        await Task.set_tasks_from_dict()

        print("定时任务初始化~")

    @staticmethod  # 查询任务
    async def read(owner_id: str):
        msg = ""
        if owner_id in Task.tasks_dict:
            msg = "↑ 契约 ↑\n"
            for key, value in Task.tasks_dict[owner_id].items():
                msg += "<" + key + "> " + value[Task.__KEY.time_formatted] + "  " + value[Task.__KEY.something] + "\n"
            msg = msg[:-1]
        else:
            msg = "好像没有什么重要的事"
        # print(msg)
        await Task.send_msg(msg=msg, owner_id=owner_id)

    @staticmethod
    def delete(owner_id: str, task_id: str):
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()


error_task = Task(time_appointed=None, task_dict={}, is_error_task=True, owner_id="-1")


# 设置正则表达式
def get_match_rule():
    return (
            r"("  # 总
            + r"("  # 时间
            + r"("
            + r"("  # 几小时/ 几分钟/ 几秒后  # (([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?)
            + r"(?P<time_relative_hour>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(个?小?时|h|H))?)"
            + r"(?P<time_relative_minute>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(分钟?|m|M))?)"
            + r"(?P<time_relative_second>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(秒|s|S))?)"
            + r"后"
            + r")"
            + r"|"
            + r"("  # 年
            + r"(?P<year_relative>明年)"
            + r"|"
            + r"(?P<year_absolute>(\d*年))"
            + r")?"
            + r"("  # 月
            + r"(?P<month_relative>下个?月|下下个?月)"
            + r"|"
            + r"(?P<month_absolute>(0?[1-9]|1[0-2])月)"
            + r")?"
            + r"("  # 日
            + r"(?P<day_relative>(今天|明天|后天|周[一二三四五六七]))"
            + r"|"
            + r"(?P<day_absolute>(0?[1-9]|[1-2][0-9]|3[0-1])日)"
            + r")?"
            + r"("  # 12小时制
            + r"(?P<time_12_rough>(早上|中午|下午|晚上))"
            + r"(?P<time_12_hour>(0?[0-9]|1[0-2])(点|时))?"
            + r"(?P<time_12_minute>(0?[0-9]|[1-5][0-9])分)?"
            + r")?"
            + r"("  # 24小时制
            + r"(?P<time_24_hour>(0?[0-9]|1[0-9]|2[0-3])(点|时))?"
            + r"(?P<time_24_minute>(0?[0-9]|[1-5][0-9])分)?"
            + r")?"
            + r")"
            + r")"
            + r"("  # 事件
            + r"(提醒我|[和对跟]我说)?(?P<something>.*)"
            + r")"
            + r")"
    )


def get_match_rule2():
    return (
            r"("  # 总
            + r"("  # 时间
            + r"("
            + r"("  # 几小时/ 几分钟/ 几秒后  # (([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?)
            + r"(?P<time_relative_hour>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(个?小?时|h|H))?)"
            + r"(?P<time_relative_minute>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(分钟?|m|M))?)"
            + r"(?P<time_relative_second>((([0-9]?[0-9]?[0-9]?[0-9])|(([一二两三四五六七八九]千)?([一二两三四五六七八九]百)?([一二三四五六七八九]?十)?[一二两三四五六七八九]?))(秒|s|S))?)"
            + r")"
            + r"|"
            + r"("  # 年
            + r"(?P<year_relative>明年)"
            + r"|"
            + r"(?P<year_absolute>(\d*年))"
            + r")?"
            + r"("  # 月
            + r"(?P<month_relative>下个?月|下下个?月)"
            + r"|"
            + r"(?P<month_absolute>(0?[1-9]|1[0-2])月)"
            + r")?"
            + r"("  # 日
            + r"(?P<day_relative>(今天|明天|后天|周[一二三四五六七]))"
            + r"|"
            + r"(?P<day_absolute>(0?[1-9]|[1-2][0-9]|3[0-1])日)"
            + r")?"
            + r"("  # 12小时制
            + r"(?P<time_12_rough>(早上|中午|下午|晚上))"
            + r"(?P<time_12_hour>(0?[0-9]|1[0-2])(点|时))?"
            + r"(?P<time_12_minute>(0?[0-9]|[1-5][0-9])分)?"
            + r")?"
            + r"("  # 24小时制
            + r"(?P<time_24_hour>(0?[0-9]|1[0-9]|2[0-3])(点|时))?"
            + r"(?P<time_24_minute>(0?[0-9]|[1-5][0-9])分)?"
            + r")?"
            + r")"
            + r")"
            + r"("  # 事件
            + r"(提醒我|[和对跟]我说)(?P<something>.*)"
            + r")"
            + r")"
    )


class Calculator:
    match_rule: str = get_match_rule()  # 无需宣告
    match_rule_2: str = get_match_rule2()  # 无需宣告, 但要有关键词 和我说, 提醒我, 后
    pattern = re.compile(match_rule)

    @staticmethod  # 解析契约, 返回Task
    def get_task(task_str: str, owner_id: str) -> Task:
        result = Calculator.pattern.match(task_str)
        if result is None:
            return error_task
        else:
            print(result.groupdict())
            return Task(datetime.datetime.now(), result.groupdict(), owner_id)


if __name__ == '__main__':
    json_path = 'tasks.json'
    task1_str = "九千九百九十九时50m20S后提醒我手冲"
    task2_str = "30s后吃饭"
    print('*' * 100)
    task1 = Calculator.get_task(task_str=task1_str, owner_id='3367436163')
    task2 = Calculator.get_task(task_str=task2_str, owner_id='3367436163')
    print(Task.tasks_dict)
    Task.read("3367436163")
