# 国科大选课助手说明 #

## 项目说明
本项目修改自：https://github.com/scusjs/ucas_enroll_evaluation

因为原项目在使用的时候出现了问题，本着有轮子就用的精神，我查看了原项目的代码，修改了源代码不可用的地方，加入了定时自动抢课的功能，这样我们只需要抢课的那天上午挂着就行了，剩下的全部交给脚本吧！

## 使用方法 ##
修改private.txt后，在控制台执行
- python main.py

### private文件说明
private.txt中，各行表示意义如下：

1. 第一行为登录选课系统的账号
2. 第二行为密码
3. 第三行为开始选课的时间，格式固定请不要随便更改格式
3. 第四行及以后每一行为一门课以及是否为学位课（0为否1为是）

如下面的为选择编号为091M4044H（且为学位课）和091M5002H（且为非学位课）

```
091M4044H 1
091M5002H 0
```

### 注意 ###
程序假设课程不冲突，每5S尝试选课一次


## 环境说明

- python 3.5.2
- requests 2.11
- 可选环境：
  - Tesseract-OCR
  - PIL

### 环境安装方法
- pip install requests
- pip install Pillow
- 登录网址默认为 http://onestop.ucas.ac.cn/home/index ，如果为 sep.ucas.as.cn 那么需要在安装如下环境：
  - Tesseract-OCR
    - windows下安装：http://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-setup-3.05.00dev.exe
      - 安装时候勾选Registry settings
    - Linux  \  MAC OS X安装见 https://github.com/tesseract-ocr/tesseract/wiki


## 更新说明

- 提升用户体验
- 支持验证码识别
- 最近更新优化了选课逻辑，提升效率
