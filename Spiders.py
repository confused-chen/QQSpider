import Methods
import requests
from threading import Thread,Semaphore
import re
import json
import sys
class Mood_Spider(object):
    def __init__(self,message):
        self.msg = message
        self.sem = Semaphore(1)#写入爬虫.html的锁
        self.sem_mood = Semaphore(1)#写入./mood.txt的锁
        self.sem_mood_json = Semaphore(1)#写入./mood_json.txt的锁
    def beginer(self):
        for qq in self.msg.target_list:
            t = Thread(target = self.spider,args = (qq,))
            t.start()
    def spider(self,target_qq):
        for page in range(0,10):
            url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?uin=%s&ftype=0&sort=0&' \
                  'pos=%d&num=20&replynum=100&g_tk=%s&callback=_preloadCallback&code_version=1&' \
                  'format=jsonp&need_private_comment=1&g_tk=%s'%(target_qq,page*20,self.msg.gtk,self.msg.gtk)
            r = self.msg.s_com.get(url)
            text = r.text
            if len(text)<1000:#少于1000个字符，说明这一页没有说说
                break
            self.sem.acquire()
            with open('./爬虫.html','a',encoding='utf-8') as f:
                f.write('QQ:%s   page:%d'%(target_qq,page))
                f.write(text)
                f.write('------------------------end--------------------------\n\n\n\n\n\n\n\n\n')
            self.sem.release()

            star = text.find('"msglist":[')
            end = Methods.braket_wife(text,star,'[') + 1
            page_source = text[star:end]#一页的内容

            #解析每条说说的内容
            moods = []
            for mood_text in self.get_mood(page_source):
                mood = self.analysis_mood(mood_text,target_qq)
                moods.append(mood)
                self.sem_mood.acquire()
                self.write_mood(mood)#可视化写入本地
                self.sem_mood.release()

            self.sem_mood_json.acquire()
            with open('./mood_json.txt', 'a') as f:
                json.dump(moods, f)#以json形式写入本地
            self.sem_mood_json.release()

    #把一页说说，拆成每一条
    def get_mood(self, text):
        mood_list = []
        star = 0
        end = 0
        while True:
            star = end
            star = text.find('{"certified"', star)
            if star < 0:
                break
            end = Methods.braket_wife(text, star, '{') + 1
            mood_list.append(text[star:end])
        return mood_list

    #把一条说说的评论拆成一个一个的评论集合
    def get_comment(self,comments):
        star = 0
        end = 0
        comment_list = []
        while True:
            star = end
            star = comments.find('{"IsPasswordLuckyMoneyCmtRight"',star)
            if star<0:
                break
            end = Methods.braket_wife(comments, star, '{') + 1
            comment_list.append(comments[star:end])
        return comment_list

    #解析一条说说的内容
    def analysis_mood(self,mood,qq):
        mood_dict = {}

        star = mood.find('"commentlist":[')
        if star>0:
            end = Methods.braket_wife(mood,star,'[') + 1
            comments = mood[star:end]  # 一条说说的所有评论
        else:
            comments = ''
        discuss_list = []
        for comment in self.get_comment(comments):
            discuss_list.append(self.analysis_comment(comment))

        if 'has_more_con":1' in mood:
            tid = re.findall('"tid":"(.*?)"', mood)[0]
            url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?&g_tk=%s'%self.msg.gtk
            data = {
                'tid' : tid,
                'uin' : qq,
                't1_source': '1',
                'not_trunc_con': '1',
                'hostuin': self.msg.account,
                'code_version': '1',
                'format': 'fs',
                'qzreferrer': 'https://user.qzone.qq.com/%s?ADUIN=%s'
                              '&ADTAG=CLIENT.'
                              'QQ.5689_FriendTip.0&ADPUBNO=26978&source=namecardhoverstar' % (qq, self.msg.account)
            }
            r = self.msg.s_com.post(url, data)
            text = r.text
            if '该条内容已被删除' in text:
                pass
            else:
                mood = text


        mood = mood.replace(comments,'')
        mood_dict['content'] = re.findall('"content":"(.*?)","createTime', mood)[0].replace('\\n','\n')
        mood_dict['time'] = re.findall('"createTime":"(.*?)","created_time', mood)[0]
        name = re.findall('},"name":"(.*?)","pic', mood)
        #正常name可以找到，如果是说说被折叠，获取折叠得到的内容以上正则匹配不到
        if name:
            mood_dict['name'] = name[0]
        else:
            mood_dict['name'] = re.findall('msgTotal.*?,"name":"(.*?)","pic', mood)[0]
        mood_dict['phone'] = re.findall('"source_name":"(.*?)","source_url', mood)[0]  # 手机型号
        pic_total = re.findall('"pictotal":(\d+)', mood)
        if pic_total:
            mood_dict['pic_num'] = pic_total[0]
        mood_dict['comment_num'] = len(discuss_list)

        #评论太多可能会被折叠，该网址直通无折叠版本
        if mood_dict['comment_num'] > 8:
            tid = re.findall('"tid":"(.*?)"',mood)[0]
            url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?u' \
                  'in=%s&tid=%s&t1_source=undefined&ftype=0&sort=0&pos=0&num=20' \
                  '&g_tk=%s&callback=_preloadCallback&' \
                  'code_version=1&format=jsonp&need_private_comment=1&g_tk=%s'%(qq,tid,self.msg.gtk,self.msg.gtk)
            # url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msgdetail_v6?' \
            #       'uin=1334994417&tid=f165924ffa94b35f8dad0700&t1_source=undefined&ftype=0&sort=0&pos=0&num=20' \
            #       '&g_tk=2089793980&callback=_preloadCallback&code_version=1&format=jsonp&need_private_comment=1&g_tk=2089793980'
            r = self.msg.s_com.get(url)
            text = r.text
            star_comment = text.find('"commentlist":[')
            end_comment = Methods.braket_wife(text,0,'[')
            comments = text[star_comment:end_comment]
            discuss_list = []
            for comment in self.get_comment(comments):
                discuss_list.append(self.analysis_comment(comment))
            mood_dict['comment_num'] = len(discuss_list)

        mood_dict['transpond_num'] = re.findall('"fwdnum":(\d+)', mood)[0]  # 转发数
        if 'rt_certified' in mood:  # 该说说是转发别人的
            origin = {}
            star = mood.find('rt_certified')
            tra = mood[star:]
            origin['content'] = re.findall('"content":"(.*?)"},"rt_createTime', tra)[0].replace('\\n','\n')
            origin['time'] = re.findall('"rt_createTime":"(.*?)","rt_fwdnum', tra)[0]
            origin['name'] = re.findall('"rt_uinname":"(.*?)"', tra)[0]
            origin['phone'] = re.findall('"rt_source_name":"(.*?)"', tra)[0]
            origin['qq'] = re.findall('"rt_uin":(\d+)', tra)[0]
            origin['comment_num'] = re.findall('"rt_cmtnum":(\d+)', tra)[0]
            origin['transpond_num'] = re.findall('"rt_fwdnum":(\d+)', tra)[0]
            mood_dict['origin'] = origin
        mood_dict['discuss_list'] = discuss_list
        return mood_dict

    def analysis_comment(self,comment):
        discuss = {}
        response = ''
        star = comment.find('[{"abledel')
        if star>0:#有回复的评论
            end = Methods.braket_wife(comment, star, '[') + 1
            response = comment[star:end]
        comment = comment.replace(response, '')  # 不含回复的评论
        com = {}
        com['content'] = re.findall('"content":"(.*?)"', comment)[0]
        com['time'] = re.findall('"createTime2":"(.*?)"', comment)[0]  # 创建时间
        com['name'] = re.findall('"name":"(.*?)"', comment)[0]
        com['qq'] = re.findall('"uin":(\d+)', comment)[0]
        discuss['comment'] = com
        if response:
            discuss['response'] = self.analysis_response(response)
        return discuss

    #解析评论
    def analysis_response(self,response):
        response_list = []
        star_response = 0
        end_response = 0
        while True:  # 解析一个评论集的每条回复的结构
            res = {}
            star_response = end_response
            star_response = response.find('{"abledel"', star_response)
            if star_response < 0:
                break
            end_response = Methods.braket_wife(response, star_response, '{') + 1
            response_one = response[star_response:end_response]
            target = {}
            tmp = re.findall('"content":"(.*?)"', response_one)[0]
            #有些神奇的存在明明@了某个人，源码却未显示
            try:
                target_content = re.findall('@{uin.*?:1}', tmp)[0]
                target['name'] = re.findall('nick:(.*?),who', target_content)[0]
                target['qq'] = re.findall('uin:(\d+),nick', target_content)[0]
            except:
                target_content =''
                target['name'] = ''
                target['qq'] = ''
            res['content'] = tmp.replace(target_content, '')
            res['time'] = re.findall('"createTime2":"(.*?)"', response_one)[0]
            res['name'] = re.findall('"name":"(.*?)"', response_one)[0]
            res['qq'] = re.findall('"uin":(\d+)', response_one)[0]
            res['target'] = target
            response_list.append(res)
        return response_list

    def write_mood(self,mood):
        with open('./mood.txt','a',encoding = 'utf-8') as f:
            phone = ''
            if mood['phone']:
                phone = '用' + mood['phone'] + '手机'
            pic = ''
            if 'pic_num' in mood:
                pic = '含' + mood['pic_num'] + '张图片的'
            f.write('%s在%s%s发表了%s说说:\n%s\n这条说说有%s评论和%s转发'%(mood['name'],mood['time'],phone,pic,mood['content'],
                                                           mood['comment_num'],mood['transpond_num']))
            if 'origin' in mood:
                origin = mood['origin']
                phone = ''
                if origin['phone']:
                    phone = '用' + origin['phone'] + '手机'
                f.write(',这条说说是转发了%s(%s)在%s%s发表的有%s评论和%s转发的说说，原文是:\n%s'%(origin['name'],origin['qq'],origin['time'],
                                                        phone,origin['comment_num'],origin['transpond_num'],origin['content']))
            if mood['discuss_list']:
                discuss_list = mood['discuss_list']
                for discuss in discuss_list:
                    comment = discuss['comment']
                    f.write('\n%s(%s)[%s]:%s'%(comment['name'],comment['qq'],comment['time'],comment['content']))
                    if 'response' in discuss:
                        for res in discuss['response']:
                            f.write('\n\t%s(%s)[%s]回复%s(%s):%s'%(res['name'],res['qq'],res['time'],res['target']['name'],
                                                                res['target']['qq'],res['content']))

            f.write('\n\n\n\n\n\n')













class Information_Spider(object):#根据SpiderMessage构造的msg爬取个人信息
    def __init__(self,message):
        self.msg = message
        self.hash_gender = {0: 'Unknown', 1: '男', 2: '女'}
        self.hash_constellation = {0: '白羊座', 1: '金牛座', 2: '双子座', 3: '巨蟹座', 4: '狮子座', 5: '处女座', 6: '天秤座', 7: '天蝎座',
                                   8: '射手座', 9: '魔羯座', 10: '水瓶座', 11: '双鱼座'}
        self.hash_bloodtype = {0: 'Unknown', 1: 'A', 2: 'B', 3: 'O', 4: 'AB', 5: 'Others'}
        self.hash_marriage = {0: 'Unknown', 1: '单身', 2: '已婚', 3: '保密', 4: '恋爱中', 5: '已订婚', 6: '分居', 7: '离异'}
        self.sem = Semaphore(1) #线程互斥
    def beginer(self):
        for qq in self.msg.target_list:
            t = Thread(target = self.spider,args = (qq,))
            t.start()
    def spider(self,target_qq):

        url = 'https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?' \
              'uin=%s&vuin=%s&fupdate=1&g_tk=%s' % (target_qq, self.msg.account, self.msg.gtk)
        r = self.msg.s_com.get(url)

        text = r.text
        if '您无权访问' in text:
            return
        if '非法操作' in text:
            return
        person_info = {}
        person_info['昵称'] = re.findall('"nickname":"(.*?)"',text)[0]
        person_info['空间名称'] = re.findall('"spacename":"(.*?)"',text)[0]
        person_info['空间签名'] = re.findall('"desc":"(.*?)"', text)[0]
        person_info['性别'] = self.hash_gender[int(re.findall('"sex":(\d)', text)[0])]
        person_info['星座'] = self.hash_constellation[int(re.findall('"constellation":(\d+)', text)[0])]
        person_info['年龄'] = re.findall('"age":(\d+)', text)[0]
        person_info['出生年'] = re.findall('"birthyear":(\d+)', text)[0]
        person_info['生日'] = re.findall('"birthday":"(.*?)"', text)[0]
        person_info['血型'] = self.hash_bloodtype[int(re.findall('"bloodtype":(\d)', text)[0])]
        person_info['居住国'] = re.findall('"country":"(.*?)"', text)[0]
        person_info['居住省'] = re.findall('"province":"(.*?)"', text)[0]
        person_info['居住市'] = re.findall('"city":"(.*?)"', text)[0]
        person_info['家乡国'] = re.findall('"hco":"(.*?)"', text)[0]
        person_info['家乡省'] = re.findall('"hp":"(.*?)"', text)[0]
        person_info['家乡市'] = re.findall('"hc":"(.*?)"', text)[0]
        person_info['婚恋状态'] = self.hash_marriage[int(re.findall('"marriage":(\d)', text)[0])]
        person_info['职业'] = re.findall('"career":"(.*?)"', text)[0]
        person_info['公司'] = re.findall('"company":"(.*?)"', text)[0]
        person_info['公司国'] = re.findall('"cco":"(.*?)"', text)[0]
        person_info['公司省'] = re.findall('"cp":"(.*?)"', text)[0]
        person_info['公司市'] = re.findall('"cc":"(.*?)"', text)[0]
        person_info['公司地址'] = re.findall('"cb":"(.*?)"', text)[0]

        #模拟手机空间爬取留言数，pc端找不到留言数
        url = 'https://h5.qzone.qq.com/mqzone/profile?hostuin=%s&no_topbar=1&srctype=10&stat=&g_f=2000000209'%target_qq
        r = self.msg.s_pho.get(url)
        text = r.text
        person_info['日志'] = re.findall('"blog":(\d+)', text)[0]
        person_info['留言'] = re.findall('"message":(\d+)', text)[0]
        person_info['相片'] = re.findall('"pic":(\d+)', text)[0]
        person_info['说说'] = re.findall('"shuoshuo":(\d+)', text)[0]

        self.sem.acquire()
        with open('./info.txt','a') as f:
            for key in person_info:
                f.write(key+':'+person_info[key])
                f.write('\n')
            f.write('-------------end-------------\n')
        self.sem.release()

