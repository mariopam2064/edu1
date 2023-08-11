from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, render_template,request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication 
from dotenv import load_dotenv
from pymongo import MongoClient
import feedparser as fp
import pandas as pd
import requests,time,re,json,os,schedule,smtplib

app = Flask(__name__)

def substitution(city='seoul',response = False):
    en_city = ["seoul","anyang","yongin","goyang","chuncheon"]
    ko_city = ['서울','안양','용인','고양','춘천']
    dict = {}
    for i in range(5):
        dict[en_city[i]] = ko_city[i]
    if response:
        return dict
    else:
        return dict[city]

def description_re(data):
    for num, desc in enumerate(data['Description']):
        data['Description'][num] = data['Description'][num].split('\n')
    return data
# Slack channel to send the message to
def sendSlackWebhook(file_path):
    SLACK_API_TOKEN = "xoxb-5580084376135-5632964908816-5Je72LI651Yrjd4HDMAsKnPu"
    client = WebClient(token=SLACK_API_TOKEN)
    try:
        response = client.files_upload(
            channels="#python_날씨예보",
            file=file_path,
            title=f"뉴스 경보"  
        )
        print(f"정상적으로 보냄")
    except SlackApiError as e:
        print(f"오류 발생 {e}")


#1.온도를 체크하고 (날씨 및 시간정보 포함) 일정 온도 이상일 시 비고에 폭염주의보 등의 정보 포함하기.
def temp_check(city):
    api_key = "6af05e28af0837330d371271e5474617"
    temp = {} #딕셔너리 형태로 도시와 각 도시마다 온도 값 저장
    for cities in city :
        url = f"http://api.openweathermap.org/data/2.5/weather?q={cities}&appid={api_key}&units=metric"
        response = requests.get(url)
        weather_data = response.json()
        temp[cities] = [weather_data["main"]["temp"], weather_data['main']['humidity']]
    return temp
def alarm_check(temp_dict):
    alarm= [] #리스트에 알람 저장
    issue = False
    for key, value in temp_dict.items():
        value = value[0]
        key = substitution(key)
        if value >= 25 and value <30 :
            alarm.append(f"{key}의 현재 온도가 야외 활동 하기 좋은 날씨에요")
        elif value >= 30 and value <33 :
            issue= True
            alarm.append(f"{key}의 현재 온도가 30도가 넘어요 조심하세요")
        elif value >= 33 and value <35:
            alarm.append(f"{key}의 현재 온도가 33도가 넘어요. 장시간 야외 활동은 위험합니다.")
            issue = True
        elif value >= 35 :
            alarm.append(f"{key}의 현재온도가 35도가 넘어요 조심하세요. 너무 더워요. 실내에서 휴식하고 야외활동은 자제하세요")
            issue  = True
    return issue, alarm

def rss_crawling_news(issue):
    '''
    issue = TRUE OR False    
    ---> True : return file_path    False : return False
    '''
    #예시 서울 경기도.
    url_list =['http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=109',
               'http://www.kma.go.kr/weather/forecast/mid-term-rss3.jsp?stnId=105'
    ]
    now = datetime.now().strftime('%Y-%m-%d_%H')
    
    file_path = f'./save/{now}_weather_news.xlsx'
    if issue:
        titles = []
        links = []
        descriptions = []
        authors = []
        for url in url_list:
            feed = fp.parse(url)
            for entry in feed.entries:  
                titles.append(entry.title)
                links.append(entry.link)
                description = entry.wf
                description = description.replace('<br>','\n')
                description = description.replace('<br />','\n')
                descriptions.append(description)
                authors.append(entry.author)
        data = {
            'Title' :titles,
            'Link' : links,
            'Description' : descriptions,
            'Author' : authors,
            }
        df = pd.DataFrame(data)  #표형식의 행과 열로 변환 시킴.
        df.to_excel(file_path, index = False)
        return file_path,data
        pass
    else:
        return False


def mail_send(file):
    load_dotenv()
    SECRET_ID = os.getenv("ID")
    SECRET_PASS = os.getenv("PASS")

    smtp = smtplib.SMTP('smtp.naver.com', 587)
    smtp.ehlo()
    smtp.starttls()

    smtp.login(SECRET_ID,SECRET_PASS)

    myemail = 'myidfly@naver.com'
    youremail = 'myidfly@naver.com'

    msg = MIMEMultipart()

    msg['Subject'] ="오늘의 날씨 정보입니다."
    msg['From'] = myemail
    msg['To'] = youremail

    text = """
    오늘의 날씨 정보입니다.
    감사합니다.
    """
    contentPart = MIMEText(text) 
    msg.attach(contentPart) 

    Today_weather_file = file
    with open(Today_weather_file, 'rb') as f : 
        etc_part = MIMEApplication( f.read() )
        etc_part.add_header('Content-Disposition','attachment', filename=Today_weather_file)
        msg.attach(etc_part)

    smtp.sendmail( myemail,youremail,msg.as_string() )
    smtp.quit()

def save_to_mongodb(df, collection_name):
    try:
        # MongoDB에 연결
        client = MongoClient('mongodb://localhost:27017')
        db = client['날씨정보']
        collection = db[collection_name]

        # DataFrame을 dict로 변환하고, dict를 MongoDB에 삽입
        data_dict = df.to_dict(orient='records')
        collection.insert_many(data_dict)
        print("날씨정보가 MongoDB에 저장되었습니다.")
    except Exception as e:
        print("Error:", e)

def read_excel(file_path, collection_name):
    try:
        # 엑셀 파일을 DataFrame으로 읽기
        df = pd.read_excel(file_path)
        # DataFrame을 MongoDB에 저장
        save_to_mongodb(df, collection_name)
    except Exception as e:
        print("Error:", e)


@app.route('/')
def index():
    city = ["seoul","anyang","yongin","goyang","chuncheon"] #스터디 조원들이 사는 도시들
    result_temp_check = temp_check(city)
    issue, result_alarm_check = alarm_check(result_temp_check)
    if issue:
        file_path,data=rss_crawling_news(issue)
        data = description_re(data)
        df =pd.read_excel(file_path)
        table_html = df.to_html()
        if file_path:
            sendSlackWebhook(file_path)
            now=datetime.now().strftime('%Y-%m-%d_%H')
            collection_name = f'{now} 날씨정보'
            read_excel(file_path, collection_name)
            mail_send(file_path)
        return render_template('news.html',table=table_html,data=data)   #줄바꿈기호 미해결.
    else:
        city_ko = substitution(response =True)   #영문-한글 딕셔너리
        return render_template('index.html' ,alarm_check = result_alarm_check, 
                               temp_check=result_temp_check, city_ko=city_ko)
    pass


if __name__=='__main__':
    app.run(debug=True) 
    pass