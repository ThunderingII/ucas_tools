from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import UnexpectedAlertPresentException
import itchat
from o_exception import *
from selenium.webdriver.support.wait import WebDriverWait

import time


class OrderBus(object):
    def __init__(self):
        self._read_bus_info()
        # self._init_wx_chat()
        self._init_chrome()

    def _read_bus_info(self):
        with open("./config.txt", encoding='UTF-8') as f:
            bus_need_order = []
            for i, line in enumerate(f):
                if i == 0:
                    self.username = line.strip()
                if i == 1:
                    self.password = line.strip()
                if i == 2:
                    self.pathOfchromedriver = line.strip()
                if i == 3:
                    self.toWhoRemarkName = line.strip()
                if i == 4:
                    self.beginTime = line.strip().split()[0]
                    self.days = int(line.strip().split()[1])
                    self.nowStr = time.strftime('%Y-%m-%d')
                    # btime = time.strptime(beginTime, "%Y-%m-%d %H:%M:%S")
                    btime = time.strptime(self.nowStr + ' ' + self.beginTime, "%Y-%m-%d %H:%M:%S")
                    self.timeStart = time.mktime(btime)
                if i > 4:
                    if len(line.strip()) > 0:
                        bus_need_order.append(line.strip().split())
            print(bus_need_order)
            self.bus_need_order = bus_need_order

    def _init_wx_chat(self):
        itchat.auto_login()

        fs = itchat.get_friends()

        toWhoRemarkName = self.toWhoRemarkName
        toUserName = ''
        for f in fs:
            if f['RemarkName'] == toWhoRemarkName:
                toUserName = f['UserName']

        # 如果备注名找不到，就找昵称
        if len(toUserName) == 0:
            for f in fs:
                if f['NickName'] == toWhoRemarkName:
                    toUserName = f['UserName']

        if len(toUserName) == 0:
            raise NickNameNotFound('没有找到备注名为"%s"对应的用户' % toWhoRemarkName)

        baseResponse = itchat.send_msg(msg='this is a test msg from OrderBus', toUserName=toUserName)

        print(baseResponse)
        if baseResponse['BaseResponse']['Ret'] != 0:
            raise MsgSentError('信息发送失败，错误信息为：%s' % baseResponse)
        else:
            print('测试信息发送成功!')
        self.toUserName = toUserName

    def _init_chrome(self):
        # 初始化webDriver，配置其不显示图片
        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path='chromedriver.exe')

    def login_order_bus_page(self):
        try:
            driver = self.driver
            # 先从onestop.ucas.ac.cn上面登录，这个没有验证码
            driver.get('http://onestop.ucas.ac.cn');
            usernameInput = driver.find_element_by_id('menhuusername')
            usernameInput.clear()
            usernameInput.send_keys(self.username)
            passwordInput = driver.find_element_by_id('menhupassword')
            passwordInput.clear()
            passwordInput.send_keys(self.password)
            buttonOfLogin = driver.find_element_by_class_name('loginbtn')
            buttonOfLogin.click()

            # # 进入了选择信息界面，点击一卡通支付
            # # 一卡通支付的xpath路径
            main_metro = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'main-metro')))
            ayktzfs = main_metro.find_elements_by_tag_name('a')
            for i in ayktzfs:
                url = str(i.get_attribute('href'))
                if url.find('/portal/site/311/1800') > -1:
                    ActionChains(driver).move_to_element(i).perform()
                    i.click()
                    break

            bLogin = driver.find_element_by_id('submit_cnzz')
            bLogin.click()

            bcyy = driver.find_element_by_link_text('班车预约')
            bcyy.click()
        except UnexpectedAlertPresentException:
            alert = self.driver.switch_to.alert
            msg = alert.text
            alert.accept()
            raise LoginError('错误信息：%s' % msg)
        except Exception as e:
            raise UndefineError('页面出现未知错误，请重试!错误信息：%s' % str(e))

    def sentMsg(self, msg):
        baseResponse = itchat.send_msg(msg=msg, toUserName=self.toUserName)

        if baseResponse['BaseResponse']['Ret'] != 0:
            print('通知信息发送失败!')
        else:
            print('通知信息发送成功!')

    def refreshPage(self):
        oldUrl = self.driver.current_url
        try:
            self.driver.refresh()
        except Exception as e:
            raise PageChangedError(str(e))
        if oldUrl != self.driver.current_url:
            raise PageChangedError

    def moveFirstToLast(self):
        if len(self.bus_need_order) > 0:
            self.bus_need_order.append(self.bus_need_order.pop(0))

    def quit(self):
        self.driver.quit()

    def busOrder(self):
        driver = self.driver
        driver.get('http://payment.ucas.ac.cn/NetWorkUI/reservedBus514R001')
        if driver.current_url != 'http://payment.ucas.ac.cn/NetWorkUI/reservedBus514R001':
            raise UndefineError('登录信息丢失，重新登录')
        while len(self.bus_need_order) > 0:
            bus_info = self.bus_need_order[0]
            print(self.bus_need_order)
            # 让时间为某天的最后一秒，这样比较好计算
            order_time = time.strptime(bus_info[0] + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            timeDelay = 1
            choosBusLine = False
            delay = time.mktime(order_time) - self.days * 24 * 3600 - time.mktime(
                time.strptime(self.nowStr + ' 23:59:59', '%Y-%m-%d %H:%M:%S')) + self.timeStart

            try:
                self.select_bus_line(bus_info)
            except Exception as e:
                raise UndefineError('选择车次错误:%s' % e)

            while timeDelay > 0:
                timeDelay = delay - time.time()
                if timeDelay > 0:
                    print(
                        '班车开抢未到:%s,还有%d小时%d分钟%d秒' % (
                            self.beginTime, timeDelay / 3600, timeDelay / 60 % 60, timeDelay % 60))
                    if timeDelay > 10 * 60:
                        timeSleep = 5 * 60
                    elif timeDelay > 2 * 60:
                        timeSleep = 60
                    elif timeDelay > 33:
                        timeSleep = 10
                    else:
                        timeSleep = 1
                else:
                    timeSleep = 0

                if timeSleep > 10:  # 大于10秒的时候不断的刷新页面
                    self.refreshPage()
                else:
                    if not choosBusLine:  # 小于60秒的时候如果没有选择车次就开始选择车次
                        try:
                            self.select_bus_line(bus_info)
                            print('选择车次ok')
                            choosBusLine = True
                        except Exception as e:
                            print('选择车次错误:%s' % e)
                            self.refreshPage()
                if timeSleep > 0:
                    print("休眠%d秒" % timeSleep)
                    time.sleep(timeSleep)
            try:
                tdButton = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'tdButton')))
                ActionChains(driver).move_to_element(tdButton).perform()
                tdButton.click()

                # 确保页面跳转了再寻找新的button
                oldUrl = driver.current_url
                WebDriverWait(driver, 5).until(EC.url_changes(oldUrl))
                tdButton = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'tdButton')))
                ActionChains(driver).move_to_element(tdButton).perform()
                tdButton.click()

                # 等待结算页面加载
                bankLogos = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'bank-logo')))
                for bl in bankLogos:
                    print(bl.get_attribute('attr'))
                    # 03表示微信支付
                    if bl.get_attribute('attr').find('3') > -1:
                        bl.click()
            except UnexpectedAlertPresentException as e:
                # 吧错误的班次信息弹出来
                bus_err = self.bus_need_order.pop(0)
                err_msg = driver.switch_to.alert.text
                driver.switch_to.alert.accept()
                raise OrderError('预定车次错误:%s,错误信息为:%s' % (bus_err, err_msg))

            oldHandles = driver.window_handles

            # submitID
            submitID = driver.find_element_by_id('submitID')
            ActionChains(driver).move_to_element(submitID).perform()
            submitID.click()

            # 切换到新打开的界面
            WebDriverWait(driver, 5).until(EC.new_window_is_opened(oldHandles))
            driver.switch_to.window(driver.window_handles[1])

            # 移动到页面最下面
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

            driver.get_screenshot_as_file('pay.png')

            itchat.send_msg(msg='车次：%s预定成功，请付款!' % self.bus_need_order[0], toUserName=self.toUserName)
            baseResponse = itchat.send_image(fileDir='pay.png', toUserName=self.toUserName)
            if baseResponse['BaseResponse']['Ret'] != 0:
                raise ImgSentError('图片发送失败，错误信息为：%s' % baseResponse)

            # 关闭当前窗口
            driver.close()
            driver.switch_to.window(oldHandles[0])

            # 弹出购买成功的路径信息
            self.bus_need_order.pop(0)

    def select_bus_line(self, bus_info):
        driver = self.driver
        dataSelector = driver.find_element_by_id('date')
        dataSelector.click()
        WebDriverWait(driver, 3).until(
            EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, 'iframe')))
        # 切换到选择日期的frame上面
        wdayTable = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'WdayTable')))
        days = wdayTable.find_elements_by_tag_name('td')
        for we in days:
            onclickStr = we.get_attribute('onclick')
            if onclickStr is not None and onclickStr.find(bus_info[0][6:].replace('-', ',')) > -1:
                we.click()
                break
        driver.switch_to.default_content()
        busSelector = driver.find_element_by_id('routeS')
        busSelector.click()
        # 等待车次重新加载
        busOptions = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'option')))
        for option in busOptions:
            # if option.text.find('')
            print(option.text)
        Select(busSelector).select_by_visible_text(bus_info[1])
