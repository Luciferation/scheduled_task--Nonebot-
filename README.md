# Aqua插件 一 定时提醒1.0

```python
由于功能太多, 只好逐个做起
定时任务又是最实用的功能, 所以先做它
TODO
	支持模糊语句 √
	支持任务自动存储至本地json, 防止丢失任务 √
    支持汉语数字 (暂时只实现了如"九千九百九十九时50m20S后提醒我手冲"之类的"后"字句)(详情见正则表达式) 待完善
	查询任务 待做
    删改任务 待做
```

## 安装插件

![](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410112538636.png)

## 两种触发方式

### 一 无命令触发

```python
时间 + 提醒我|[和对跟]我说 + 事件
# 因为无需命令, 为了防止误触发, 所以 提醒我|[和对跟]我说 是必须的
```

![image-20220410105120344](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410105120344.png)

![image-20220410105220494](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410105220494.png)![](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410105607224.png)

```python
# 正则表达式 (如下)
```

![image-20220410111148046](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410111148046.png)

### 二 有命令触发

```python
宣告
时间 + 提醒我|[和对跟]我说 + 事件
# 因为有命令, 不容易误触发, 所以 提醒我|[和对跟]我说 可有可无
```

![image-20220410165236419](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410165236419.png)

```python
# 正则表达式如下
```

![image-20220410111624013](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410111624013.png)

## 数据存储

```python
任务存储是自动进行的
	插件在bot运行并成功建立连接后, 会从Task.json载入任务
    有新任务时会自动, 写入json
    任务执行完毕后, 会自动从json中删除
(结构如下图)
```

![image-20220410111734984](C:\Users\Lucifer\AppData\Roaming\Typora\typora-user-images\image-20220410111734984.png)

