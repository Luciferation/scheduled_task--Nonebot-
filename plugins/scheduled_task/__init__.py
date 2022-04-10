from nonebot import get_driver, on_regex, get_bot
from .config import Config
from nonebot.rule import to_me
from nonebot.adapters import Event
from .task import Calculator, Task
from nonebot import get_driver

global_config = get_driver().config
config = Config.parse_obj(global_config)

scheduledTask = on_regex(pattern=r"^(宣告)\b", rule=to_me(), priority=3, block=True)

driver = get_driver()


# 这个钩子函数会在bot连接上后运行

@driver.on_bot_connect
async def init():
    await Task.init()


@scheduledTask.handle()
async def handle1():
    await scheduledTask.pause("契约缔结开始 （・_・）")


@scheduledTask.handle()
async def handle2(event: Event):
    the_task = Calculator.get_task(task_str=event.get_plaintext(), owner_id=event.get_user_id())
    await scheduledTask.send(
        "<" + the_task.time_appointed.strftime("%Y-%m-%d %H:%M:%S") + " " + the_task.something + "> 契约缔结! \n ＯＫ(ゝω・´★)")
    await the_task.set_the_task()


scheduledTask2 = on_regex(Calculator.match_rule_2, rule=to_me(), priority=4, block=True)


@scheduledTask2.handle()
async def handle(event: Event):
    the_task = Calculator.get_task(task_str=event.get_plaintext(), owner_id=event.get_user_id())
    await scheduledTask.send(
        "<" + the_task.time_appointed.strftime("%Y-%m-%d %H:%M:%S") + " " + the_task.something + "> 契约缔结! \n ＯＫ(ゝω・´★)")
    await the_task.set_the_task()
