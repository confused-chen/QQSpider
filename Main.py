import SpiderMessage
import Spiders
import Methods

Methods.empty_file()
with open('./MyQQ.txt','r') as f:
    account = f.readline()
    account = account.strip()
msg = SpiderMessage.message(account)
sp = Spiders.Mood_Spider(msg)
sp.beginer()
# import Methods
# Methods.load_cookie()
