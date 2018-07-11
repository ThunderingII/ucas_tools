# UCAS_enroll_evaluation: 中国科学院大学自动刷课、评教脚本

<font color="red">评教功能经过本人修改已经很好使了，原项目地址:https://github.com/scusjs/ucas_enroll_evaluation</font>

## 环境依赖
运行环境：Python 3.3-3.5

依赖 `BeautifulSoup` 和 `Requests`，通过如下命令可安装

```
bash> pip install beautifulsoup4pipipipsh
bash> pip install requests
```



## 信息配置
在目录下新建 `config` 文件并填入用户名密码及期望动作，格式如下：

```
[info]
username =
password =

[action]
enroll = true
evaluate = false

[idle]
time = 3
```

其中

- enroll设置为true表示选课
- evaluate设置为true表示评教
- time代表每次请求的时间间隔，0代表无间隔，默认为3，单位为秒，且必须为非负整数

在目录下新建 `courseid` 文件并填入课程，格式如下：

```
091M5023H:on
091M4002H
```

其中

- 课程编号:on #表示该课程选择为学位课
- 课程编号 #表示普通选课

以上例子表示091M5023H作为学位课选课，091M4002H只进行普通选课

## 执行
配置完成后直接执行脚本即可。

```
bash> python3 evaluate.py
bash> Login success
bash> Enrolling start
bash> [Success] 091M5042H
bash> Enrolling finish
```

## 问题及解决方式
Ubuntu系统下脚本可能会出现“No such course”的错误，即使填入的courseid是正确的，可以通过如下方法来修复：

```
bash> sudo locale-gen en_US.UTF-8  
bash> export LC_ALL=en_US.UTF-8
bash> python3 evaluate.py
``` 

