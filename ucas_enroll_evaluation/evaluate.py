# @file evaluate.py
# @brief enroll & evaluate
# @author scusjs@foxmail.com, my@imcmy.me
# @version 0.2.01
# @date 2017-1-3

import requests
from configparser import RawConfigParser
from bs4 import BeautifulSoup
from CollegeCode import CollegeCode
import time

debug = False


class UCASEvaluate:
    def __init__(self):
        self.__readCoursesId()

        cf = RawConfigParser()
        cf.read('config', encoding='utf-8')
        self.username = cf.get('info', 'username')
        self.password = cf.get('info', 'password')
        self.enroll = cf.getboolean('action', 'enroll')
        self.evaluate = cf.getboolean('action', 'evaluate')
        self.idle = cf.get('idle', 'time')
        print('Hi, username: ' + self.username)
        print('Password: ' + '*' * len(self.password))

        self.loginPage = 'http://sep.ucas.ac.cn'
        self.loginUrl = self.loginPage + '/slogin'
        self.courseSystem = self.loginPage + '/portal/site/226/821'
        self.courseBase = 'http://jwxk.ucas.ac.cn'
        self.courseIdentify = self.courseBase + '/login?Identity='
        self.courseSelected = self.courseBase + '/courseManage/selectedCourse'
        # self.courseSelectionBase = self.courseBase + '/courseManage/main'
        self.courseSelectionBaseFirst = 'http://sep.ucas.ac.cn/portal/site/226/821'
        self.courseSelectionBase = self.courseBase + '/notice/view/1'
        self.courseCategory = self.courseBase + '/courseManage/selectCourse?s='
        self.courseSave = self.courseBase + '/courseManage/saveCourse?s='

        self.studentCourseEvaluateUrl = 'http://jwjz.ucas.ac.cn/Student/DeskTopModules/'
        self.selectCourseUrl = 'http://jwjz.ucas.ac.cn/Student/DesktopModules/Course/SelectCourse.aspx'

        self.evaluateIndex = 'http://jwxk.ucas.ac.cn/evaluate/52576'
        self.evaluateBase = 'http://jwxk.ucas.ac.cn/evaluate/evaluate/'
        self.evaluateSave = 'http://jwxk.ucas.ac.cn/evaluate/save/{}?s={}'
        self.merit = cf.get('comment', 'merit')
        self.flaw = cf.get('comment', 'flaw')
        self.suggest = cf.get('comment', 'suggest')

        self.enrollCount = {}
        self.evaluateCount = {}
        self.headers = {
            'Host': 'sep.ucas.ac.cn',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        }

        self.s = requests.Session()
        loginPage = self.s.get(self.loginPage, headers=self.headers)
        self.cookies = loginPage.cookies

    def networkUnstable(self, response):
        if response.status_code != requests.codes.ok:
            if response.status_code == requests.codes.moved_permanently:
                self.login()
                print('Relogin')
            return True
        return False

    def login(self):
        while True:
            postdata = {
                'userName': self.username,
                'pwd': self.password,
                'sb': 'sb'
            }
            status = self.s.post(self.loginUrl, data=postdata, headers=self.headers)

            response = self.s.get('http://sep.ucas.ac.cn/appStore')
            print('login code %d' % response.status_code)

            if status.status_code != requests.codes.ok:
                continue
            if 'sepuser' in self.s.cookies.get_dict():
                return True

            return False

    def __readCoursesId(self):
        coursesFile = open('./courseid', 'r')
        self.coursesId = {}
        for line in coursesFile.readlines():
            line = line.strip().replace(' ', '').split(':')
            courseId = line[0]
            isDegree = False
            if len(line) == 2 and line[1] == 'on':
                isDegree = True
            self.coursesId[courseId] = isDegree

    def enrollCourses(self, idle=3):
        try:
            idle = abs(int(self.idle))
        except:
            print('Idle Error and use the default idle time %d secs.' % idle)
        while True:
            response = self.s.get(self.courseSelectionBase)
            if self.networkUnstable(response):
                continue
            break
        while True:
            response = self.s.get(self.courseSystem, headers=self.headers)
            if self.networkUnstable(response):
                continue
            print('Course System')
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        if debug:
            print(response.text)
            exit()
        try:
            identity = str(soup).split('Identity=')[1].split('"'[0])[0]
            coursePage = self.courseIdentify + identity
            while True:
                response = self.s.get(coursePage)
                if self.networkUnstable(response):
                    continue
                response = self.s.get(self.courseSelected)
                if self.networkUnstable(response):
                    continue
                print('Course Selected')
                break
            if debug:
                print(response.text)
                exit()

            while True:
                for eachCourse in self.coursesId:
                    if eachCourse in response.text:
                        print("Course " + eachCourse + " has been selected.")
                        self.enrollCount[eachCourse] = 0
                        continue
                    if (eachCourse in self.enrollCount and
                            self.enrollCount[eachCourse] == 0):
                        continue
                    self.enrollCount[eachCourse] = 1
                    result = self.__enrollCourse(eachCourse,
                                                 self.coursesId[eachCourse])
                    if result:
                        self.enrollCount[eachCourse] = 0
                    time.sleep(idle)

                for enroll in self.enrollCount:
                    if self.enrollCount[enroll] == 0:
                        self.coursesId.pop(enroll)
                self.enrollCount.clear()
                if not self.coursesId:
                    return
        except KeyboardInterrupt:
            print("Bye")
        except Exception as exception:
            print("System error")
            print(exception)
            exit()

    def __enrollCourse(self, courseId, isDegree):
        print('Enroll ' + courseId + ' Start')
        while True:
            response = self.s.get(self.courseSelectionBase)
            if self.networkUnstable(response):
                continue
            break
        if debug:
            print(response.text)
            exit()

        soup = BeautifulSoup(response.text, 'html.parser')
        labels = [(label.contents[0][:2], label['for'][3:])
                  for label in soup.find_all('label')[2:]]
        categories = dict()
        for label in labels:
            if label[0] in categories:
                categories[label[0]] += ',' + label[1]
            else:
                categories[label[0]] = label[1]
        # categoryId = categories[courseId[:2]]
        categoryId = categories[CollegeCode[courseId[:2]]]
        identity = soup.form['action'].split('=')[1]

        postdata = {
            'deptIds': categoryId,
            'sb': 0
        }
        categoryUrl = self.courseCategory + identity
        while True:
            response = self.s.post(categoryUrl, data=postdata)
            if self.networkUnstable(response):
                continue
            break
        if debug:
            print(response.text)
            exit()

        soup = BeautifulSoup(response.text, 'html.parser')
        courseTable = soup.body.form.table.find_all('tr')[1:]
        courseDict = dict([(c.span.contents[0], c.span['id'].split('_')[1])
                           for c in courseTable])

        if courseId in courseDict:
            postdata = {
                'deptIds': categoryId,
                'sids': courseDict[courseId]
            }
            if isDegree:
                postdata['did_' + courseDict[courseId]] = courseDict[courseId]

            courseSaveUrl = self.courseSave + identity
            while True:
                response = self.s.post(courseSaveUrl, data=postdata)
                if self.networkUnstable(response):
                    continue
                break
            if debug:
                print(response.text)
                exit()
            tmp = BeautifulSoup(response.text, 'html.parser')
            flag = tmp.find('div', attrs={'id': 'messageBoxError'})
            if 'hide' in flag['class']:
                print('[Success] ' + courseId)
                return True
            else:
                print('[Fail] ' + courseId)
                return False
        else:
            print("No such course")
            return True

    def evaluateCourses(self):
        try:
            idle = abs(int(self.idle))
        except:
            print('Idle Error and use the default idle time %d secs.' % idle)
        while True:
            response = self.s.get(self.courseSelectionBaseFirst)

            print('*' * 40)

            if self.networkUnstable(response):
                continue
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        for link in links:
            if '这里' in link.text:
                url = link['href']
                response = self.s.get(url)
                print('result:%d \t request:%s' % (response.status_code, url))
                print('-*' * 20)
        while True:
            print(self.evaluateIndex)
            # print(self.courseBase + self.evaluateIndex)
            response = self.s.get(self.evaluateIndex)

            print(response.text)
            if self.networkUnstable(response):
                continue
            break
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', attrs={'class': 'btn'})
            self.evaluateCourseIds = []
            for link in links:
                self.evaluateCourseIds.append(link['href'].split('/')[-1])
            while True:
                for courseId in self.evaluateCourseIds:
                    if (courseId in self.evaluateCount and
                            self.evaluateCount[courseId] == 0):
                        continue
                    self.evaluateCount[courseId] = 1
                    result = self.__evaluateCourse(courseId)
                    if result:
                        self.evaluateCount[courseId] = 0
                    time.sleep(idle)

                for enroll in self.evaluateCount:
                    if self.evaluateCount[enroll] == 0:
                        self.evaluateCourseIds.remove(enroll)
                self.evaluateCount.clear()
                if not self.evaluateCourseIds:
                    return
        except KeyboardInterrupt:
            print("Bye")
        except Exception as exception:
            print("System error")
            print(exception)
            exit()

    def __evaluateCourse(self, courseId):
        while True:
            response = self.s.get(self.evaluateBase + courseId)
            if self.networkUnstable(response):
                continue
            break
        s = response.text.split('?s=')[-1].split('"')[0]
        soup = BeautifulSoup(response.text, 'html.parser')
        radios = soup.find_all('input', attrs={'type': 'radio'})
        value = radios[0]['value']
        data = {}
        for radio in radios:
            data[radio['name']] = value
        data['starFlag'] = 5
        data['merit'] = self.merit
        data['flaw'] = self.flaw
        data['suggest'] = self.suggest
        while True:
            response = self.s.post(self.evaluateSave.format(courseId, s), data=data)
            if self.networkUnstable(response):
                continue
            break
        tmp = BeautifulSoup(response.text, 'html.parser')
        flag = tmp.find('div', attrs={'id': 'messageBoxError'})
        if 'hide' in flag['class']:
            print('[Success] ' + courseId)
            return True
        else:
            print('[Fail] ' + courseId)
            return False


if __name__ == "__main__":
    ucasEvaluate = UCASEvaluate()

    if not ucasEvaluate.login():
        print('Login error. Please check your username and password.')
        exit()
    print('Login success')

    if ucasEvaluate.enroll:
        print('Enrolling start')
        ucasEvaluate.enrollCourses()
        print('Enrolling finish')

    if ucasEvaluate.evaluate:
        print('Evaluating start')
        ucasEvaluate.evaluateCourses()
        print('Evaluating finish')
