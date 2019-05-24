import tkinter as tk
from tkinter import *
import tkinter.messagebox
from re import split, compile
from urllib import parse
import requests
from bs4 import BeautifulSoup
from time import time, sleep, strftime, localtime
from threading import Thread, Event
from traceback import format_exc
from Logger import Logger


url = 'http://sxd.xyhero.com/index.php'
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

INDEX = 0

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

        main_info = requests.get(url='%s%s' % (url, zhujiao_tag.attrs['href']), headers=headers)
        info_soup = BeautifulSoup(main_info.text, "html.parser")
        info_tag = (info_soup.find(text=compile("名字.*"))).parent.findNext('br').previous
        xianyuan_tag = (info_soup.find(text=compile("仙缘：.*"))).parent.findNext('br').previous
        age_tag = (info_soup.find(text=compile(".*年")))
        level_tag = (info_soup.find(text=compile("等级：.*"))).parent.findNext('br').previous

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

        login_window.destroy()
        main_window = tk.Tk()
        main_window.title('五行修真辅助')
        main_window.geometry('600x400')

        frame_info = tk.Frame(main_window, width=300, height=245)
        frame_info.place(x=0, y=0)
        frame_battle = tk.Frame(main_window, width=300, height=245)
        frame_battle.place(x=300, y=0)

        var_message = tk.StringVar()
        list_message = tk.Listbox(main_window, listvariable=var_message, width=600, height=155)
        list_message.place(x=0, y=245)

        label_name = tk.Label(frame_info, text='名字:%s' % info_tag)
        label_name.pack()

        label_xianyuan = tk.Label(frame_info, text='仙缘:%s' % xianyuan_tag)
        label_xianyuan.pack()

        label_age = tk.Label(frame_info, text='寿命:%s' % age_tag)
        label_age.pack()

        label_level = tk.Label(frame_info, text='等级:%s' % level_tag)
        label_level.pack()

        def refresh(name, xianyuan, age, level):
            # global label_name, label_xianyuan, label_age, label_level
            refresh_info = requests.get(url='%s%s' % (url, zhujiao_tag.attrs['href']), headers=headers)
            refresh_soup = BeautifulSoup(refresh_info.text, "html.parser")
            name.config(text='名字:%s' % (refresh_soup.find(text=compile("名字.*"))).parent.findNext('br').previous)
            xianyuan.config(text='仙缘:%s' % (refresh_soup.find(text=compile("仙缘：.*"))).parent.findNext('br').previous)
            age.config(text='寿命:%s' % (refresh_soup.find(text=compile(".*年"))))
            level.config(text='等级:%s' % (refresh_soup.find(text=compile("等级：.*"))).parent.findNext('br').previous)

        button_refresh = tk.Button(frame_info, text='刷新', command=lambda :refresh(label_name, label_xianyuan, label_age, label_level)).pack()

        label_common = tk.Label(frame_battle, text='怪物代码:').place(x=0, y=0)

        # common输入
        var_common = tk.StringVar()
        entry_common_code = tk.Entry(frame_battle, textvariable=var_common)
        entry_common_code.place(x=80, y=0)

        var_xy = tk.BooleanVar()
        var_xy.set(True)
        checkbutton_xy = tk.Checkbutton(frame_battle, text='自动触发奇遇', variable=var_xy)
        checkbutton_xy.place(x=100, y=30)

        def start_battle(button, entry):
            global t, INDEX
            if button['text'] == '挂机':
                entry.config(state='readonly')
                button['text'] = '停止'
                INDEX = 0
                t = Job()
                t.start()

            elif button['text'] == '停止':
                entry.config(state='normal')
                button['text'] = '挂机'
                list_message.delete(0, END)
                t.stop()

        button_battle = tk.Button(frame_battle, text='挂机',
                                  command=lambda: start_battle(button_battle, entry_common_code))

        button_battle.place(x=135, y=60)

        # var_info = tk.StringVar()
        # label_info = tk.Label(text_message, textvariable=var_info)
        # label_info.pack()

        class Job(Thread):

            def __init__(self):
                super(Job, self).__init__()
                self.__flag = Event()  # 用于暂停线程的标识
                self.__flag.set()  # 设置为True
                self.__running = Event()  # 用于停止线程的标识
                self.__running.set()  # 将running设置为True

            def run(self):
                while self.__running.isSet():
                    self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
                    start_time = time()

                    global INDEX
                    if var_xy.get() is True:
                        data['xyqy'] = 1
                    elif 'xyqy' in data.keys():
                        del data['xyqy']
                    try:
                        guaji_res = requests.post(url='%s%s%s' % (url, '?common=', var_common.get()), data=data,
                                                  headers=headers)
                        battle_soup = BeautifulSoup(guaji_res.text, "html.parser")
                        fail_tag = battle_soup.find(text=compile("战斗失败·除魔失败.*"))
                        if fail_tag is not None:
                            global fail
                            fail += 1
                            if INDEX < 9:
                                INDEX += 1
                            else:
                                list_message.delete(0)
                            list_message.insert(END, (strftime("%Y-%m-%d %H:%M:%S--", localtime()) + '战斗失败！\n'))
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
                                Logger('../LOG/error.log', level='error').logger.error('ERROR201:' + str(battle_soup))
                            else:
                                global success
                                success += 1
                                if INDEX < 9:
                                    INDEX += 1
                                else:
                                    list_message.delete(0)
                                list_message.insert(END, (strftime("%Y-%m-%d %H:%M:%S--", localtime()) + purchase_char + '\n'))
                                log.logger.info(purchase_char)
                        age_tag = battle_soup.find(text=compile(".*年.*"))
                        if age_tag is not None:
                            label_age.config(text='寿命:' + age_tag)
                    except Exception as e:
                        Logger('../LOG/error.log', level='error').logger.error('ERROR209:' + format_exc())
                    finally:
                        pass
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

        t = Job()

        requests.adapters.DEFAULT_RETRIES = 5

        main_window.mainloop()
    except Exception as ex:
        tkinter.messagebox.showerror('error', '应该是账号或者密码错误。。。')
        Logger('../LOG/error.log', level='error').logger.error('ERROR221:' + format_exc())


login = tk.Button(login_window, text='登录', command=login)

login.place(x=130, y=75)
    
login_window.mainloop()
