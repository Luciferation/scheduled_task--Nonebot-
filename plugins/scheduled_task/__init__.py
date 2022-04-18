from nonebot import get_driver, on_regex, get_bot
from .config import Config
from nonebot.rule import to_me
from nonebot.adapters import Event
from .task import Task
from nonebot import get_driver
import re

global_config = get_driver().config
config = Config.parse_obj(global_config)

driver = get_driver()


# 这个钩子函数会在bot连接上后运行
@driver.on_bot_connect
async def init():
    await Task.init()


scheduledTask_create1 = on_regex(pattern=r"^(宣告)\b", rule=to_me(), priority=3, block=True)


@scheduledTask_create1.handle()
async def handle1():
    await scheduledTask_create1.pause("契约缔结开始 （・_・）")


@scheduledTask_create1.handle()
async def handle2(event: Event):
    the_task = Task(task_str=event.get_plaintext(), owner_id=event.get_user_id())
    await scheduledTask_create1.send(
        "<" + the_task.time_appointed + " " + the_task.something + "> 契约缔结! \n ＯＫ(ゝω・´★)")
    await the_task.set_the_task()


scheduledTask2_create2 = on_regex(Task.match_rule, rule=to_me(), priority=4, block=True)


@scheduledTask2_create2.handle()
async def handle(event: Event):
    the_task = Task(task_str=event.get_plaintext(), owner_id=event.get_user_id())
    if the_task.type == Task.KEY.error_task:
        msg = "听不懂诶, 换种说法吧"
    else:
        msg = "<" + the_task.time_appointed + " " + the_task.something + "> 契约缔结! \n ＯＫ(ゝω・´★)"
    await the_task.set_the_task()
    await scheduledTask2_create2.send(msg)


scheduledTask_read = on_regex(pattern="(最近有什么事吗\??)|(契约查询)|(查询契约)", rule=to_me(), priority=3, block=True)


@scheduledTask_read.handle()
async def handle(event: Event):
    await Task.read(event.get_user_id())


scheduledTask_delete = on_regex(pattern="(忘记|不用提醒我|删除)(契约)?(?P<task_id>\d+)吧?了?", rule=to_me(), priority=3, block=True)


@scheduledTask_delete.handle()
async def handle(event: Event):
    result = re.match(pattern="(忘记|不用提醒我|删除)(契约)?(?P<task_id>\d+)吧?了?", string=event.get_plaintext())
    task_id = result.groupdict()['task_id']
    Task.delete(event.get_user_id(), task_id)
    await scheduledTask_delete.send("现在Aqua不记得" + "契约" + task_id + "是什么了")
