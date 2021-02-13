from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def getCookie(account):
    #return readDict()#调试时直接读取本地cookie
    try:
        browser = webdriver.Chrome()
        wait = WebDriverWait(browser,10)
        browser.get('http://qzone.qq.com/?s_url=http://user.qzone.qq.com/470250642/')
        browser.switch_to_frame('login_frame')
        plogin = browser.find_element_by_css_selector("a[uin='%s']"%account)
        plogin.click()
        time.sleep(2)
        cookies = {}
        for cookie in browser.get_cookies():
            cookies[cookie['name']] = cookie['value']
        print("Get the cookie of QQ:%s successfully!(共%d个键值对)" % (account, len(cookies)))
        return cookies
    except:
        return {}
    finally:
        browser.quit()

def get_Gtk(cookie):
    """ 根据cookie得到GTK """
    hashes = 5381
    for letter in cookie['p_skey']:
        hashes += (hashes << 5) + ord(letter)
    return hashes & 0x7fffffff

def writeQQ(qq_list,file_name):
    with open(file_name,'w') as f:
        for qq in qq_list:
            f.write(qq)
            f.write('\n')
def writeDict(dict):#把字典变量写入本地
    with open('./dict.txt', 'w') as f:
        json.dump(dict, f)

def readDict():#读取本地的字典吧变量
    with open('dict.txt', 'r') as f:
        js = f.read()
    return json.loads(js)

def load_cookie():#获取新cookie写入本地，用于测试，免于多次重新取cookie
    writeDict(getCookie('2582450849'))

def braket_wife(str,star,bra):#从star开始，找到第一个括号的老婆
    count = 0
    index = star
    for i in str[star:]:
        if bra=='[':
            if i==']':
                count = count - 1
                if count == 0:
                    return index
            elif i=='[':
                count = count + 1
        elif bra=='{':
            if i=='}':
                count = count - 1
                if count == 0:
                    return index
            elif i=='{':
                count = count + 1
        elif bra=='(':
            if i==')':
                count = count - 1
                if count == 0:
                    return index
            elif i=='(':
                count = count + 1
        index = index + 1
    return -1#单身括号

#清空文件，便于调试
def empty_file():
    with open('./mood.txt','w') as f:
        f.write('')
    with open('./mood_json.txt','w') as f:
        f.write('')
    with open('./爬虫.html','w') as f:
        f.write('')