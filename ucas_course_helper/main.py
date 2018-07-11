# -*- coding: utf-8 -*-
# @Date    : 2016/9/1
# @Author  : hrwhisper
from __future__ import print_function
import re
import time

import datetime

import requests

colleageData = {'01': '数学学院', '02': '物理学院', '03': '天文学院', '04': '化学学院', '05': '材料学院', '06': '生命学院', '07': '地球学院',
                '08': '资环学院',
                '09': '计算机学院', '10': '电子学院', '11': '工程学院', '12': '经管学院', '13': '公共管理学院', '14': '人文学院', '15': '外语系',
                '16': '中丹学院',
                '17': '国际学院', '18': '存济医学院', '19': '微电子学院', '20': '网络空间安全学院', '21': '未来技术学院', '22': '创新创业',
                '23': '马克思中心',
                '24': '心理学系', '25': '人工智能学院', '26': '纳米科学与技术学院', '27': '艺术中心', 'TY': '体育教研室'}

from LoginUCAS import LoginUCAS


class NoLoginError(Exception):
    pass


class NotFoundCourseError(Exception):
    pass


class NotSelectCourseTime(Exception):
    pass


class UcasCourse(object):
    def __init__(self):
        self.times = 0
        self.session = None
        self.headers = None
        self.jwxk_html = None
        self.course, self.beginTime = UcasCourse._read_course_info()
        self._init_session()

    def _init_session(self):
        t = LoginUCAS().login_sep()
        self.session = t.session
        self.headers = t.headers
        self.login_jwxk()

    @classmethod
    def _read_course_info(self):
        with open("./private.txt", encoding='UTF-8') as f:
            timeFloat = 0.0
            courses = []
            for i, line in enumerate(f):
                if i == 2:
                    beginTime = line.strip()
                    btime = time.strptime(beginTime, "%Y-%m-%d %H:%M:%S")
                    timeFloat = time.mktime(btime)
                if i < 3: continue
                courses.append(line.strip().split())
            print(courses)
        return courses, timeFloat

    def login_jwxk(self):
        # 从sep中获取Identity Key来登录选课系统，进入选课选择课学院的那个页面
        url = "http://sep.ucas.ac.cn/portal/site/226/821"
        r = self.session.get(url, headers=self.headers)
        # code = '1'
        try:
            code = re.findall(r'"http://jwxk.ucas.ac.cn/login\?Identity=(.*)"', r.text)[0]
        except IndexError:
            raise NoLoginError

        url = "http://jwxk.ucas.ac.cn/login?Identity=" + code
        self.headers['Host'] = "jwxk.ucas.ac.cn"
        self.session.get(url, headers=self.headers)
        url = 'http://jwxk.ucas.ac.cn/courseManage/main'
        r = self.session.get(url, headers=self.headers)
        self.jwxk_html = r.text

    def get_course(self):
        # 获取课程开课学院的id，以及选课界面HTML
        html = self.jwxk_html

        # print(html)

        print(self.course)
        print(self.course[0][0][:2])

        print(colleageData[self.course[0][0][:2]])
        # regular = r'<label for="id_([\S]+)">' + self.course[0][0][:2] + r'-'
        regular = r'<label for="id_([\S]+)">' + colleageData[self.course[0][0][:2]]

        # regular = '<label for="id_([\S]+)">' + self.college
        institute_id = re.findall(regular, html)[0]

        print(institute_id)
        print("开课学院:%s  学院deptIds:%s" % (colleageData[self.course[0][0][:2]], institute_id))
        url = 'http://jwxk.ucas.ac.cn' + \
              re.findall(r'<form id="regfrm2" name="regfrm2" action="([\S]+)" \S*class=', html)[0]
        post_data = {'deptIds': institute_id, 'sb': '0'}

        html = self.session.post(url, data=post_data, headers=self.headers).text
        return html, institute_id

    def select_course(self):
        if not self.course: return None
        # 选课，主要是获取课程背后的ID
        html, institute_id = self.get_course()
        if time.time() < self.beginTime or html.find('<label id="loginError" class="error">未开通选课权限</label>') != -1:
            raise NotSelectCourseTime
        url = 'http://jwxk.ucas.ac.cn' + \
              re.findall(r'<form id="regfrm" name="regfrm" action="([\S]+)" \S*class=', html)[0]
        sid = re.findall(r'<span id="courseCode_([\S]+)">' + self.course[0][0] + '</span>', html)
        if sid:
            sid = sid[0]
        else:
            raise NotFoundCourseError
        post_data = {'deptIds': institute_id, 'sids': sid}
        if self.course[0][1] == '1':
            post_data['did_' + sid] = sid

        html = self.session.post(url, data=post_data, headers=self.headers).text
        if html.find(u'选课成功') != -1:
            return self.course.pop(0)[0]
        else:  # 一般是课程已满
            self.course.append(self.course.pop(0))
            try:
                info = re.findall('<label id="loginError" class="error">(.+)</label>', html)[0]
                print(info)
            except Exception as e:
                print(e)
            return None

    def sleep(self, t=5):
        time.sleep(t)

    def start(self):
        while True:
            try:
                res = self.select_course()
                if res is not None:
                    print('课程编号为 {} 的选课成功'.format(res))
                elif not self.course:
                    print('全部选完')
                    exit(0)
                else:
                    self.sleep()
            except NoLoginError:
                self._init_session()
            except NotFoundCourseError:
                print('尝试选择课程编号为 {} 的时候出错，可能编号错误或者已被选上'.format(self.course.pop(0)[0]))
            except NotSelectCourseTime:
                self.times = self.times + 1
                timeDelay = self.beginTime - time.time()
                print('选课时间未到:%d,还有%d小时%d分钟%d秒' % (self.times, timeDelay / 3600, timeDelay / 60 % 60, timeDelay % 60))
                if timeDelay > 10 * 60:
                    timeSleep = 5 * 60
                elif timeDelay > 2 * 60:
                    timeSleep = 60
                elif timeDelay > 13:
                    timeSleep = 10
                else:
                    timeSleep = 1
                print("休眠%d秒" % timeSleep)
                self.sleep(timeSleep)
            except Exception as e:
                e.with_traceback()
                # e.with_traceback()
                print(e)
                self.sleep(2)
                self._init_session()


if __name__ == '__main__':
    # while datetime.datetime.now() < datetime.datetime(2017, 6, 1, 12, 10, 00):
    #     print('wait ',datetime.datetime.now())
    #     time.sleep(60)
    UcasCourse().start()
