import tkinter as tk
from tkinter import messagebox
from re import split, compile
from urllib import parse
import requests
from bs4 import BeautifulSoup
from time import time, sleep, strftime, localtime
from threading import Thread, Event
import logging
from logging import handlers
from traceback import format_exc

url = 'http://sxd.xyhero.com/index.php'


class Logger(object):
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }  # 日志级别关系映射

    def __init__(self, filename='../LOG/battle.log', level='debug', when='D', back_count=8, fmt='[%(asctime)s:%(message)s]'):
        self.logger = logging.getLogger(filename)

        # 实例化TimedRotatingFileHandler
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=back_count, encoding='utf-8')
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时
        # D 天
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨

        # 设置日志格式
        format_str = logging.Formatter(fmt)
        # 设置文件里写入的格式
        th.setFormatter(format_str)
        # 设置日志级别
        self.logger.setLevel(self.level_relations.get(level))
        # 往文件里写入#指定间隔时间自动生成文件的处理器
        self.logger.addHandler(th)


log = Logger()


login_window = tk.Tk()
login_window.title('五行修真辅助')
login_window.geometry('300x120')

tk.Label(login_window, text='账号:').place(x=20, y=15)
tk.Label(login_window, text='密码:').place(x=20, y=45)

# 账号
uid = tk.StringVar()
userId = tk.Entry(login_window, textvariable=uid)
userId.place(x=80, y=15)

# 密码
userPass = tk.StringVar()
password = tk.Entry(login_window, textvariable=userPass, show='*')
password.place(x=80, y=45)


success = 0
fail = 0

def login():

    # 拼接url并登陆
    textmod = {'id': uid.get(), 'pass': userPass.get(), 'login': '%B5%C7%C2%BC'}
    textmod = parse.urlencode(textmod)
    res = requests.get(url='%s%s%s' % (url, '?', textmod))

    try:

        # 获取cookie
        cookie_value = ''
        set_cookie = res.headers['Set-Cookie']
        array = split('[;,]', set_cookie)
        cookie_value += array[0] + ';'
        array1 = split('=', array[0])
        cookie_value += ' NO=' + array1[1]
        headers = {'Cookie': cookie_value}

        # 主角代码
        zhujiao_soup = BeautifulSoup(res.text, "html.parser")
        zhujiao_tag = zhujiao_soup.find(name='a', text='人物状态')
        zhujiao_char = 'char_' + zhujiao_tag.attrs['href'].split('=')[1]

        # 道徒代码
        daotu = requests.get(url='%s%s' % (url, '?menu=daotutudi'), headers=headers)
        daotu_soup = BeautifulSoup(daotu.text, "html.parser")
        daotu_tag = daotu_soup.find_all('div', class_='carpet0')
        daotu_char = []
        for tag in daotu_tag:
            daotu_char.append('char_' + tag.contents[1].attrs['href'].split('=')[1])

        # 组装form表单
        data = dict()
        data[zhujiao_char] = 1
        for char in daotu_char:
            data[char] = 1
        data['monster_battle'] = 2
        data['xyqy'] = 1

        login_window.destroy()
        main_window = tk.Tk()
        main_window.title('五行修真辅助')
        main_window.geometry('600x400')

        label_common = tk.Label(main_window, text='怪物代码:')
        label_common.place(x=180, y=50)
        # common输入
        var_common = tk.StringVar()
        common = tk.Entry(main_window, textvariable=var_common)
        common.place(x=250, y=50)

        def start_battle():
            common.config(state='readonly')
            success = 0
            fail = 0
            global t
            t = Job(char_common=var_common.get(), data=data, headers=headers)
            t.start()

        def stop_battle():
            common.config(state='normal')
            log.logger.info('战斗成功率 = %.1f' % ((success / (success + fail)) * 100) + '%')
            global t
            t.stop()

        hit = tk.Button(main_window, text='挂机', command=start_battle)
        hit.place(x=250, y=70)
        cancel = tk.Button(main_window, text='停止', command=stop_battle)
        cancel.place(x=300, y=70)

        var_age = tk.StringVar()
        var_info = tk.StringVar()
        label_age = tk.Label(main_window, textvariable=var_age)
        label_age.place(x=300, y=110)
        label_info = tk.Label(main_window, textvariable=var_info)
        label_info.place(x=300, y=130)

        class Job(Thread):

            def __init__(self, char_common, data, headers):
                super(Job, self).__init__()
                self.__flag = Event()  # 用于暂停线程的标识
                self.__flag.set()  # 设置为True
                self.__running = Event()  # 用于停止线程的标识
                self.__running.set()  # 将running设置为True
                self.char_common = char_common
                self.data = data
                self.headers = headers

            def run(self):
                while self.__running.isSet():
                    self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
                    start_time = time()
                    guaji_req(self.char_common, self.data, self.headers)
                    end_time = time()
                    if (end_time - start_time) < 3:
                        log.logger.info("延时:%.2fs" % (3 - (end_time - start_time)))
                        sleep(3 - (end_time - start_time) + 0.01)
                    else:
                        log.logger.info('超时:%.2fs' % (end_time - start_time - 3))

            def pause(self):
                self.__flag.clear()  # 设置为False, 让线程阻塞

            def resume(self):
                self.__flag.set()  # 设置为True, 让线程停止阻塞

            def stop(self):
                self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
                self.__running.clear()  # 设置为False
                log.logger.info('stop')

        t = Job(char_common=var_common.get(), data=data, headers=headers)

        requests.adapters.DEFAULT_RETRIES = 5

        def guaji_req(char_common, data, headers):
            try:

                guaji_res = requests.post(url='%s%s%s' % (url, '?common=', char_common), data=data, headers=headers)
                battle_soup = BeautifulSoup(guaji_res.text, "html.parser")
                fail_tag = battle_soup.find(text=compile("战斗失败·除魔失败.*"))
                if fail_tag is not None:
                    global fail
                    fail += 1
                    var_info.set(strftime("%Y-%m-%d %H:%M:%S--", localtime()) + '战斗失败！')
                    log.logger.info('战斗失败·除魔失败')
                else:
                    exp_tag = battle_soup.find(text=compile("获得经验 : .*"))
                    if not exp_tag:
                        exp_tag = ''
                    else:
                        exp_tag += ','
                    money_tag = battle_soup.find(text=compile("获得银两 : .*"))
                    if not money_tag:
                        money_tag = ''
                    else:
                        money_tag += ','
                    zhenqi_tag = battle_soup.find(text=compile("获得真气 : .*"))
                    if not zhenqi_tag:
                        zhenqi_tag = ''
                    purchase_char = (exp_tag + money_tag + zhenqi_tag).replace('\n', '')
                    if len(purchase_char) < 4:
                        Logger('../LOG/error.log', level='error').logger.error('ERROR201:' + battle_soup)
                    else:
                        global success
                        success += 1
                        var_info.set(strftime("%Y-%m-%d %H:%M:%S--", localtime()) + purchase_char)
                        log.logger.info(purchase_char)
                age_tag = battle_soup.find(text=compile(".*年.*"))
                if age_tag is not None:
                    var_age.set('剩余寿命:' + age_tag)
            except Exception as e:
                Logger('../LOG/error.log', level='error').logger.error('ERROR209:' + format_exc(e))
            finally:

                label_age.place(x=200, y=110)
                label_info.place(x=100, y=130)

        main_window.mainloop()
    except Exception as ex:
        messagebox.showerror('error', '应该是账号或者密码错误。。。')
        Logger('../LOG/error.log', level='error').logger.error('ERROR221:' + format_exc(ex))


login = tk.Button(login_window, text='登录', command=login)

login.place(x=130, y=75)
    
login_window.mainloop()
