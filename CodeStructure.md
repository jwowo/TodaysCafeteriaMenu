### 프로젝트 구조

'''
|__ static/
        |__ image/
                |__ logo.jpg       -> 로고 이미지

        |__ css/
                |__ star-rating.css         -> 리뷰 별점 표시를 위한 
                |__ star-rating.min.css     -> css 파일
                
        |__ js  
                |__ star-rating.js          -> 리뷰 별점 표시를 위한
                |__ star-rating.min.js      -> js 파일

        |__ themes/
                |__ krajee-fa/              -> 리뷰 별점 표시를 위한
                |__ krajee-fas/             -> themes 파일
                |__ krajee-gly/
                |__ krajee=uni/


|__ templates/
        |__ login.html      -> 로그인 페이지
        |__ signup.html     -> 회원가입 페이지
        |__ main.html       -> 메인 페이지 및 시간대별 메뉴 모달 페이지

|__ app.py/                 -> flask를 통한 서버 및 클라이언트 연결, MongoDB와 연동

'''