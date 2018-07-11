from order_bus import OrderBus
from o_exception import *
import traceback

if __name__ == '__main__':
    orderBus = OrderBus()
    shouldContinue = True
    while shouldContinue:
        try:
            orderBus.login_order_bus_page()
            orderBus.busOrder()
            break
        except LoginError as le:
            shouldContinue = False
            print(le)
        except NickNameNotFound as ne:
            shouldContinue = False
            print(ne)
        except OrderError as oe:
            print(oe)
            orderBus.sentMsg(str(oe))
        except UndefineError as ue:
            # 一旦不知道的错误，就全部重新登录
            orderBus.login_order_bus_page()
            orderBus.sentMsg(str(ue))
        except Exception as e:
            traceback.print_exc()
            orderBus.sentMsg('异常类：%s，错误信息：%s' % (e.__class__.__name__, str(e)))
    orderBus.quit()
