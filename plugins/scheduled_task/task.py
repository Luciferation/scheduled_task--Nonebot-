import json
import random
import re
import datetime
from dateutil.relativedelta import relativedelta
import jionlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import get_bot
import time

# 改成自己的路径
json_path = r'aqua/plugins/scheduled_task/tasks.json'  # windows



class Task:
    scheduler: AsyncIOScheduler = None
    is_scheduler_running: bool = False
    tasks_dict = {}
    the_max_tasks_number = 1000
    is_task_id_available = [1 for i in range(the_max_tasks_number)]
    bot = None
    match_rule = r"(?P<time>(.*)?)(提醒我|[和对跟]我说)(?P<something>(.*))"

    class KEY:
        # 任务
        something: str = "something"
        time_appointed: str = "time_appointed"
        time_delta: str = "time_delta"
        # 任务类型
        point_tasks: str = "point_tasks"
        period_tasks: str = "period_tasks"
        error_task: str = "error_task"
        un_analysed_task: str = "un_analysed_task"
        # 时间
        time: str = "time"
        time_point: str = "time_point"
        time_period: str = "time_period"
        type: str = "type"
        delta: str = 'delta'
        point: str = 'point'

    # 获得bot, 从json加载任务字典, 获得scheduler并启动, 从字典中设置任务
    @staticmethod
    async def init():
        Task.bot = get_bot()
        Task.load_from_json()
        Task.set_scheduler()
        await Task.set_tasks_from_dict()
        print("定时任务初始化~")

    @staticmethod
    async def set_tasks_from_dict():
        tasks_dict = Task.tasks_dict
        for owner_id in list(tasks_dict.keys()):
            if Task.KEY.point_tasks in tasks_dict[owner_id]:
                point_tasks = tasks_dict[owner_id][Task.KEY.point_tasks]
                for task_id in list(point_tasks.keys()):
                    task_info = point_tasks[task_id]
                    Task.is_task_id_available[int(task_id)] = 0
                    await Task.set_point_task(
                        owner_id=owner_id,
                        task_id=task_id,
                        something=task_info[Task.KEY.something],
                        time_appointed=task_info[Task.KEY.time_appointed]
                    )
            if owner_id in list(tasks_dict.keys()) and Task.KEY.period_tasks in tasks_dict[owner_id]:
                period_tasks = tasks_dict[owner_id][Task.KEY.period_tasks]
                for task_id in list(period_tasks.keys()):
                    task_info = period_tasks[task_id]
                    Task.is_task_id_available[int(task_id)] = 0
                    await Task.set_period_task(
                        owner_id=owner_id,
                        task_id=task_id,
                        something=task_info[Task.KEY.something],
                        time_appointed=task_info[Task.KEY.time_appointed],
                        time_delta=task_info[Task.KEY.time_delta]
                    )

    def __init__(self, owner_id: str, task_str: str):
        self.owner_id = owner_id
        self.type = Task.KEY.un_analysed_task
        self.task_id = self.get_task_id()

        result = re.match(pattern=Task.match_rule, string=task_str)
        try:
            if result is not None:
                self.something = result[Task.KEY.something]
                # 不指定时间则默认每天早上8点提醒
                if result[Task.KEY.time] == '':
                    self.__init__(owner_id, "每天早上8点提醒我" + self.something)
                else:
                    self.time_dict: dict = jionlp.parse_time(result[Task.KEY.time])
                    print(self.time_dict)
                    if self.time_dict[Task.KEY.type] == 'time_point':
                        self.type = Task.KEY.point_tasks
                        self.time_appointed = self.time_dict[Task.KEY.time][0]
                    elif self.time_dict[Task.KEY.type] == 'time_period':
                        self.type = Task.KEY.period_tasks
                        if self.time_dict[Task.KEY.time][Task.KEY.point] is None:
                            self.time_appointed = datetime.datetime.now().isoformat()
                        else:
                            self.time_appointed = self.time_dict[Task.KEY.time][Task.KEY.point][Task.KEY.time][0]
                        self.time_delta = self.time_dict[Task.KEY.time][Task.KEY.delta]
                    print(self.task_id, self.owner_id, self.something, self.time_dict, self.type)
                    self.add_to_dict()
                    Task.store_tasks_in_json()
                    print(self.something, "解析成功")
        except ValueError as result:
            self.type = Task.KEY.error_task
            self.error_info = result
            print("解析失败", result)
        except Exception:
            self.type = Task.KEY.error_task
            self.error_info = "Aqua出错了, 但是不知道为什么"
            print("不知道怎么了")

    def get_task_id(self) -> str:
        for i in range(Task.the_max_tasks_number):
            if Task.is_task_id_available[i] == 1:
                Task.is_task_id_available[i] = 0
                return str(i)
        else:
            self.type = Task.KEY.error_task
            return str(-1)

    # 分析任务字典, 设置something, 和timeAppointed

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
    async def send_point_remind(something: str, owner_id: str, task_id: str):
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

    @staticmethod
    async def send_period_remind(something: str, owner_id: str):
        await Task.send_msg(msg=something, owner_id=owner_id)

    @staticmethod
    async def send_miss(time_appointed: str, something: str, owner_id: str, task_id: str, msg: str = ""):
        if msg == "":
            msg = random.choice(
                [
                    time_appointed + something + "错过了" + " 没关系吗?",
                ]
            )
        await Task.send_msg(msg=msg, owner_id=owner_id)
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()

    @staticmethod
    async def set_point_task(owner_id: str, task_id: str, something: str, time_appointed: str):
        datetime_appointed = datetime.datetime.fromisoformat(time_appointed)
        if datetime_appointed < datetime.datetime.now():
            await Task.send_miss(time_appointed=time_appointed, something=something, owner_id=owner_id,
                                 task_id=task_id)
        else:
            Task.scheduler.add_job(Task.send_point_remind, 'date', next_run_time=datetime_appointed, id=task_id,
                                   kwargs={'something': something, 'owner_id': owner_id, 'task_id': task_id})
            print("成功设置定时任务 " + something)

    @staticmethod
    async def set_period_task(owner_id: str, task_id: str, something: str, time_appointed: str, time_delta: dict):
        datetime_appointed = datetime.datetime.fromisoformat(time_appointed)
        cnt = 0
        time_delta = {
            'years': 0 if 'year' not in time_delta else int(time_delta['year']),
            'months': 0 if 'month' not in time_delta else int(time_delta['month']),
            'days': 0 if 'day' not in time_delta else int(time_delta['day']),
            'hours': 0 if 'hour' not in time_delta else int(time_delta['hour']),
            'minutes': 0 if 'minute' not in time_delta else int(time_delta['minute']),
            'seconds': 0 if 'second' not in time_delta else int(time_delta['second']),
        }
        time_delta = relativedelta(**time_delta)
        while datetime_appointed < datetime.datetime.now():
            # datetime_appointed = datetime.datetime(
            #     year=datetime_appointed.year + int(time_delta['years']),
            #     month=datetime_appointed.month + int(time_delta['months']),
            #     day=datetime_appointed.day + int(time_delta['days']),
            #     hour=datetime_appointed.hour + int(time_delta['hours']),
            #     minute=datetime_appointed.minute + int(time_delta['minutes']),
            #     second=datetime_appointed.second + int(time_delta['seconds']),
            # )
            datetime_appointed = datetime_appointed + time_delta
            cnt += 1
            if cnt == 100:
                await Task.send_miss(
                    time_appointed, something, owner_id, task_id,
                    msg="<period_task " + something + "> 缔结失败, 再试一次就好了"
                )
                break
        else:
            Task.scheduler.add_job(
                Task.scheduler.add_job, 'date', next_run_time=datetime_appointed,
                kwargs={
                    'func': Task.send_period_remind,
                    'trigger': 'cron',
                    'id': task_id,
                    **{
                        'year': f'*/{time_delta.years}' if time_delta.years != 0 else None,
                        'month': f'*/{time_delta.months}' if time_delta.months != 0 else None,
                        'day': f'*/{time_delta.days}' if time_delta.days != 0 else None,
                        'hour': f'*/{time_delta.hours}' if time_delta.hours != 0 else None,
                        'minute': f'*/{time_delta.minutes}' if time_delta.minutes != 0 else None,
                        'second': f'*/{time_delta.seconds}' if time_delta.seconds != 0 else None
                    },
                    'kwargs': {'something': something, 'owner_id': owner_id}
                }
            )

    async def set_the_task(self):
        if self.type == Task.KEY.point_tasks:
            await Task.set_point_task(self.owner_id, self.task_id, self.something, self.time_appointed)
        elif self.type == Task.KEY.period_tasks:
            await Task.set_period_task(self.owner_id, self.task_id, self.something, self.time_appointed,
                                       self.time_delta)
        elif self.type == Task.KEY.error_task:
            Task.is_task_id_available[int(self.task_id)] = 1
            # print(self.error_info.__str__())
            await Task.send_msg(
                # re.match(r"\'(?P<un_analysed_text>(.*)+?)\'", self.error_info.__str__()).groupdict()['un_analysed_text'],
                self.error_info.__str__(),
                owner_id=self.owner_id
            )

    @staticmethod
    def set_scheduler():
        Task.scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        Task.scheduler.start()

    def add_to_dict(self):
        if self.owner_id not in Task.tasks_dict:
            if self.type == Task.KEY.point_tasks:
                Task.tasks_dict[self.owner_id] = {
                    self.type: {
                        self.task_id: {
                            Task.KEY.something: self.something,
                            Task.KEY.time_appointed: self.time_appointed
                        }
                    }
                }
            elif self.type == Task.KEY.period_tasks:
                Task.tasks_dict[self.owner_id] = {
                    self.type: {
                        self.task_id: {
                            Task.KEY.something: self.something,
                            Task.KEY.time_appointed: self.time_appointed,
                            Task.KEY.time_delta: self.time_dict[Task.KEY.time][Task.KEY.delta]
                        }
                    }
                }
        else:
            tasks_of_the_owner = Task.tasks_dict[self.owner_id]
            if self.type in tasks_of_the_owner:
                if self.type == Task.KEY.point_tasks:
                    tasks_of_the_owner[self.type][self.task_id] = {
                        Task.KEY.something: self.something,
                        Task.KEY.time_appointed: self.time_appointed
                    }
                elif self.type == Task.KEY.period_tasks:
                    tasks_of_the_owner[self.type][self.task_id] = {
                        Task.KEY.something: self.something,
                        Task.KEY.time_appointed: self.time_appointed,
                        Task.KEY.time_delta: self.time_delta
                    }
            else:
                if self.type == Task.KEY.point_tasks:
                    tasks_of_the_owner[self.type] = {
                        self.task_id: {
                            Task.KEY.something: self.something,
                            Task.KEY.time_appointed: self.time_appointed
                        }
                    }
                elif self.type == Task.KEY.period_tasks:
                    tasks_of_the_owner[self.type] = {
                        self.task_id: {
                            Task.KEY.something: self.something,
                            Task.KEY.time_appointed: self.time_appointed,
                            Task.KEY.time_delta: self.time_delta
                        }
                    }

    @staticmethod
    def pop_task_from_dict(owner_id: str, task_id: str):
        if owner_id in Task.tasks_dict:
            if Task.KEY.point_tasks in Task.tasks_dict[owner_id]:
                if task_id in Task.tasks_dict[owner_id][Task.KEY.point_tasks]:
                    Task.tasks_dict[owner_id][Task.KEY.point_tasks].pop(task_id)
                    Task.is_task_id_available[int(task_id)] = 1
                    if len(Task.tasks_dict[owner_id][Task.KEY.point_tasks]) == 0:
                        Task.tasks_dict[owner_id].pop(Task.KEY.point_tasks)
            if Task.KEY.period_tasks in Task.tasks_dict[owner_id]:
                if task_id in Task.tasks_dict[owner_id][Task.KEY.period_tasks]:
                    Task.tasks_dict[owner_id][Task.KEY.period_tasks].pop(task_id)
                    Task.is_task_id_available[int(task_id)] = 1
                    if len(Task.tasks_dict[owner_id][Task.KEY.period_tasks]) == 0:
                        Task.tasks_dict[owner_id].pop(Task.KEY.period_tasks)
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
        try:
            with open(json_path, 'r', encoding='UTF-8') as f:
                Task.tasks_dict = json.load(f)
                f.close()
        except FileNotFoundError:
            pass

    @staticmethod  # 查询任务
    async def read(owner_id: str):
        if owner_id in Task.tasks_dict:
            msg = "↑ 契约 ↑\n"
            if Task.KEY.point_tasks in Task.tasks_dict[owner_id]:
                msg += "<" + Task.KEY.point_tasks + ">\n"
                for task_id, task_info in Task.tasks_dict[owner_id][Task.KEY.point_tasks].items():
                    msg += "<" + task_id + "> " + task_info[Task.KEY.time_appointed] \
                           + "\n  " + task_info[Task.KEY.something] + "\n"
            if Task.KEY.period_tasks in Task.tasks_dict[owner_id]:
                msg += "<" + Task.KEY.period_tasks + ">\n"
                for task_id, task_info in Task.tasks_dict[owner_id][Task.KEY.period_tasks].items():
                    msg += "<" + task_id + "> " + task_info[Task.KEY.time_appointed] \
                           + "  " + str(task_info[Task.KEY.time_delta]) + "\n  " + task_info[Task.KEY.something] + "\n"
            msg = msg[:-1]
        else:
            msg = "好像没有什么重要的事"
        await Task.send_msg(msg=msg, owner_id=owner_id)

    @staticmethod
    def delete(owner_id: str, task_id: str):
        Task.scheduler.remove_job(task_id)
        Task.pop_task_from_dict(owner_id, task_id)
        Task.store_tasks_in_json()


if __name__ == '__main__':
    json_path = 'tasks1.json'

    print('*' * 100)
    id = '3367436163'
    tasks_list = {
        "每周一晚上提醒我吃饭",
        "30分钟后提醒我第二次打卡",
        "4月20日早上提醒我晚上有实验",
        "每天晚上10点和我说晚安"
    }
    for task in tasks_list:
        Task(task_str=task, owner_id=id)

    Task.pop_task_from_dict(id, '0')
    Task.pop_task_from_dict(id, '1')
    Task.pop_task_from_dict(id, '2')
    Task.pop_task_from_dict(id, '3')
    Task.store_tasks_in_json()
