import requests
import Methods
class message(object):#根据账号，取得爬虫需要的信息
    def __init__(self,account):
        self.thread_num = 3#爬取的目标qq数
        self.account = account#提供cookie的账号
        self.cookie = Methods.getCookie(account)
        self.gtk = Methods.get_Gtk(self.cookie)
        self.target_list = []
        #电脑和手机的请求头
        self.headers = {'computer':{'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'},
                        'phone':{'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36'}}
        #电脑版的会话和手机版的会话
        self.s_com = requests.session()
        self.s_com.cookies.update(self.cookie)
        self.s_com.headers.update(self.headers['computer'])
        self.s_pho = requests.session()
        self.s_pho.cookies.update(self.cookie)
        self.s_pho.headers.update(self.headers['phone'])
        with open('./targetQQ.txt','r') as f:
            for str in f.readlines():
                str = str.strip()
                if str:
                    self.target_list.append(str)#待爬的qq列表
        if len(self.target_list) > self.thread_num:
            Methods.writeQQ(self.target_list[self.thread_num:],'./targetQQ.txt')
            self.target_list = self.target_list[0:self.thread_num]
        else:
            self.thread_num_information = len(self.target_list)
