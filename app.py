from flask import Flask, render_template, request, jsonify, redirect, url_for
# JWT 인증 사용 (pip install pyjwt)
import jwt
# MongoDB 사용
from pymongo import MongoClient
# 해시 함수 사용
import hashlib
# 토큰에 만료시간을 주기 위해 사용
from datetime import datetime, date
# 현재 날짜를 알기 위해 사용
import datetime as dt
# 크롤링 위한 함수 호출
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.todaymenu

# 템플릿이 변경되면 다시 로드한다.
app.config["TEMPLATES_AUTO_RELOAD"] = True

# jwt 암호화 키
SECRET_KEY = 'swjungle'

# JWT 확장 모듈을 flask 어플리케이션에 등록
# jwt = JWTManager(app)
# def create_token():


##금일 메뉴 dictionary 형태로 반환{'breakfirst' : menus_breakfirst_list,'lunch':menus_lunch_list, 'dinner' : menus_dinner_list}
def todayMenu(d_today_str):
    # url = 'https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=icc&stt_dt=2021-11-06'
    url = 'https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=icc&stt_dt='
    url_today = url + d_today_str

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(url_today,headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    times = ['breakfast','lunch','dinner']

    for time in times:
        selector1 = '#tab_item_1 > table > tbody > tr > td:nth-child('
        selector2 = ')'
        if time == 'breakfast':
            selector_time = '1'
            selector_final = selector1 + selector_time + selector2
            menus_breakfast = soup.select_one(selector_final).text
            menus_breakfast_list = menus_breakfast.replace("*","").replace("\t","").replace("\n","").replace("\r","_").split("_")
            for menu_breakfast in menus_breakfast_list:
                if(menu_breakfast == ""):
                    menus_breakfast_list.remove("")
        elif time == 'lunch':
            selector_time = '2'
            selector_final = selector1 + selector_time + selector2
            menus_lunch = soup.select_one(selector_final).text
            menus_lunch_list = menus_lunch.replace("*","").replace("\t","").replace("\n","").replace("\r","_").split("_")
            for menu_lunch in menus_lunch_list:
                if(menu_lunch == ""):
                    menus_lunch_list.remove("")
        else:
            selector_time = '3'
            selector_final = selector1 + selector_time + selector2
            menus_dinner = soup.select_one(selector_final).text
            menus_dinner_list = menus_dinner.replace("*","").replace("\t","").replace("\n","").replace("\r","_").split("_")
            for menu_dinner in menus_dinner_list:
                if(menu_dinner == ""):
                    menus_dinner_list.remove("")
        
    menus = {'breakfast' : menus_breakfast_list,'lunch':menus_lunch_list, 'dinner' : menus_dinner_list}
    return menus

##금일 날짜 str형태로 반환 2021-11-03
def strToday():
    d_today = dt.date.today()
    d_today_str = d_today.strftime('%Y-%m-%d')
    return d_today_str

##DB에서(all_menus) menus_receive와 동일한 메뉴들의 평균 평점
def averageRating(all_menus,menus_receive):
    count = 0
    total_rating = 0
    total_count = 0

    for i in range(len(all_menus)):
        for menu_receive in menus_receive:
            if menu_receive in all_menus[i]['menus']:
                count += 1
            else:
                continue
        if count >= 3:
            total_rating += all_menus[i]['rating']
            total_count += 1
            count = 0
        else:
            count = 0
            continue
    
    if total_count == 0:
        return 0
    else:
        return total_rating / total_count

#all_Info 에서 menus와 일치하는 정보를 리스트 형태로 반환 [{유저1_정보},{유저2_정보},,,]
def usersInfo(all_Info,menus):
    count = 0
    total_info =[]
    for i in range(len(all_Info)):
        for menu in menus:
            if menu in all_Info[i]['menus']:
                count += 1
            else:
                continue
        if count >= 3:
            show_info = {'userId': all_Info[i]['userId'],'postDate':all_Info[i]['postDate'],'rating':all_Info[i]['rating'],
            'comment' : all_Info[i]['comment']}
            total_info.append(show_info)
            count = 0
        else:
            count = 0
            continue    
    return total_info

def decode_token():
    token = request.cookies.get('token')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_find = db.users.find_one({'user_id': payload['id']})
        if user_find is not None:
            return {"result": "success", "data": payload['id']}
        else:
            return {"result": "failed", "msg": "유효하지 않은 사용자입니다."}
    except jwt.ExpiredSignatureError:
        return {"result": "failed", "msg": "로그인 시간이 만료되었습니다."}
    except jwt.DecodeError:
        return {"result": "failed", "msg": "로그인 정보가 존재하지 않습니다."}



@app.route('/')
def home():
   return render_template('login.html')

# 로그인
@app.route('/login')
def login():
   return render_template('login.html')

# 로그인 버튼 
@app.route('/api/login', methods=['POST'])
def api_login():
   # POST로 전달받은 아이디와 비밀번호
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']

   # print(id_receive, pw_receive)

   # 전달받은 비밀번호를 암호화하여 DB에 해당 아이디와 비밀번호가 있는지 조회
   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
   result = db.users.find_one({'userid': id_receive, 'password': pw_hash})

   print('db서치 결과 : ', result)

   # DB에 해당 아이디와 비밀번호가 있다면, jwt 토큰 생성 및 전달
   if result is not None:
      payload = {
         'id': id_receive,
         'exp': dt.datetime.utcnow() + dt.timedelta(seconds=60 * 60)
      }
      token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
      # print('token--------------', token)
      return jsonify({'result': 'success', 'token': token})

   else:
      return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 회원가입
@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/api/signup', methods=['POST'])
def api_signup():
   id_receive = request.form['id_give']
   pw_receive = request.form['pw_give']
   name_receive = request.form['name_give']
   email_receive = request.form['email_give']
   pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

   # id 중복 체크

   # password 동일 체크

   doc = {
      "userid" : id_receive,
      "password" : pw_hash,
      "username" : name_receive,
      "email" : email_receive  
   }

   print(doc)

   db.users.insert_one(doc)
   
   return jsonify({'result': 'success'})

def crawl_menu(month, date):
   pass

@app.route('/main')
def main():
   #DB에서 정보 가져오기
   all_Info = list(db.postInfo.find({},{'_id':False}))
   #금일 메뉴{아:[],점:[],저:[]}
   menus = todayMenu(strToday())
   
   #시간별 메뉴 리스트
   menus_breakfast = menus['breakfast']
   menus_lunch = menus['lunch']
   menus_dinner = menus['dinner']
   
   #금일 시간별 메뉴와 일치하는 DB상의 평점들의 평균값
   rating_breakfast = averageRating(all_Info,menus_breakfast)
   rating_lunch = averageRating(all_Info,menus_lunch)
   rating_dinner = averageRating(all_Info,menus_dinner)

   #금일 시간별 메뉴와 일치하는 DB상의 유저정보(id,코멘트,작성일,평점)
   usersInfo_breakfast = usersInfo(all_Info,menus_breakfast)
   usersInfo_lunch = usersInfo(all_Info,menus_lunch)
   usersInfo_dinner = usersInfo(all_Info,menus_dinner)
    
    
   token_receive = request.cookies.get('token')
   try:
      payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
         
      return render_template('main.html', showToday = strToday(), menusBreakfast = menus_breakfast,
    menusLunch = menus_lunch, menusDinner = menus_dinner, ratingBreakfirst = rating_breakfast, ratingLunch =rating_lunch,
    ratingDinner =rating_dinner, usersInfoBreakfirst = usersInfo_breakfast, usersInfoLunch = usersInfo_lunch,
    usersInfoDinner = usersInfo_dinner)
   except jwt.ExpiredSignatureError:
      return redirect(url_for("login"))
   except jwt.exceptions.DecodeError:
      return redirect(url_for("login"))

@app.route('/main/post', methods=['POST'])
def post_memo():
	# 1. 클라이언트로부터 데이터를 받기
    userId_receive = request.form['userId_give']
    postDate_receive = request.form['postDate_give']
    time_receive = request.form['time_give']
    menus_receive = request.form['menus_give']
    rating_receive = request.form['rating_give']
    comment_receive = request.form['comment_give']
    
    # 2. mongoDB 에 입력
    doc = {'userId': userId_receive,'postDate': postDate_receive,'time': time_receive,
    'menus': menus_receive,'rating': rating_receive,'comment': comment_receive}
		
    db.postInfo.insert_one(doc)

    return render_template('/main.html')




# @app.get('/main')
# def main():
#     decoded = decode_token()
#     if decoded['result'] != 'success':
#         return render_template('main.html', token_err_msg=decoded['msg'])
#     else:
#        print(decoded['msg']) 
#     user_info = db.users.find_one({'user_id': decoded['data']}, {'_id': False})
   
   

#     return render_template('login.html', page_name="home", user_info=user_info)


if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)