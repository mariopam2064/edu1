from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime

url = 'https://www.weather.go.kr/w/weather/warning/status.do'

headers = {
'User-Agent': 'Mozilla/5.0',                    #모질라는 브라우저 명 보통 휴대폰과 pc 구분
'Content-Type': 'text/html; charset=utf-8'      #요청하는 데이터 종류
}

req = requests.get(url,headers=headers)
if req.status_code ==200:
    print('요청 성공')
    soup = BeautifulSoup(req.text,'lxml')   #pip install lxml    <---- parser library

 
#weather-warning > div:nth-child(3) > div
display_board = '#weather-warning > div:nth-child(2) > div:nth-child(1) >p.tit'
warning_text='#weather-warning > div:nth-child(2) > div:nth-child(1) > div > div.tab-fild > div.right-flid > div > div > div > div:nth-child(1) > p'
tab01 = '#weather-warning > div:nth-child(2) > div:nth-child(1) > div'
#tags  = soup.select(warning_text)
#print(tags)
temp = soup.find_all('p', class_='tit')
print(temp)





        
       