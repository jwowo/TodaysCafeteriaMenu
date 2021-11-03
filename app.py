from flask import Flask, render_template, request, jsonify, redirect, url_for
# JWT 인증 사용 (pip install pyjwt)
import jwt
# MongoDB 사용
from pymongo import MongoClient
# 해시 함수 사용
import hashlib
# 토큰에 만료시간을 주기 위해 사용
from datetime import datetime
# 현재 날짜를 알기 위해 사용
import datetime as dt

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

    today_month = datetime.today().month
    today_date = datetime.today().day

    today_date = '오늘은 ' + str(today_month) + '월' + str(today_date) + '일 입니다.'

    # 메뉴 크롤링
    crawl_menu(today_month, today_date)
    
    token_receive = request.cookies.get('token')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
          
        return render_template('main.html', today_date = today_date, breakfast_menus = ['잡곡밥','고추장찌개','치킨너겟&머스타드','야채무침','도시락김','배추김치','누룽지'], breakfast_comments = ['맛있어요', '그냥 그래요'], breakfast_avg_rating = 3.6)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login"))

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