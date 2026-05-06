import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# Render 설정에서 가져오는 비밀 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# 데이터 저장소 (서버 재시작 시 초기화됨)
receipts = []       # 영수증 보관함
reviews = []        # 손님이 보낸 리뷰 인증샷 목록
issued_users = set() # 영수증을 이미 받아간 사용자 ID

# --- 관리자 페이지 HTML 템플릿 ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>나스 사장님 관리자 대시보드</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; background: #f4f4f9; }
        .card { background: white; padding: 15px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; color: white; font-weight: bold; }
        .btn-pay { background: #28a745; }
        .btn-reject { background: #dc3545; }
        img { max-width: 100%; border-radius: 5px; margin-top: 10px; }
        .badge { background: #eee; padding: 3px 8px; border-radius: 20px; font-size: 0.8em; }
    </style>
</head>
<body>
    <h2>🚀 리뷰 관리 대시보드</h2>
    <p>현재 남은 영수증: <strong>{{ receipt_count }}장</strong></p>
    <hr>
    {% for review in reviews %}
    <div class="card">
        <div><span class="badge">ID: {{ review.user_id[:8] }}...</span></div>
        <img src="{{ review.image_url }}" alt="리뷰 인증샷">
        <div style="margin-top: 10px;">
            <button class="btn btn-pay" onclick="alert('송금 기능 준비 중')">송금 승인</button>
            <button class="btn btn-reject" onclick="alert('반려 처리되었습니다.')">반려</button>
        </div>
    </div>
    {% else %}
    <p>아직 들어온 리뷰 인증샷이 없습니다.</p>
    {% endfor %}
</body>
</html>
"""

@app.route('/admin')
def admin_page():
    available_count = len([r for r in receipts if not r['used']])
    return render_template_string(ADMIN_HTML, reviews=reviews, receipt_count=available_count)

@app.route('/receipt', methods=['POST'])
def get_receipt():
    data = request.json
    user_id = data.get('userRequest', {}).get('user', {}).get('id')
    
    # 중복 발급 방지 문구 수정
    if user_id in issued_users:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "이미 영수증을 받으셨습니다!"}}]}
        })

    available = [r for r in receipts if not r['used']]
    if not available:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "현재 준비된 영수증이 없어요! 사장님께 문의해주세요."}}]}
        })
    
    selected = available[0]
    selected['used'] = True
    issued_users.add(user_id)
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "확인했어요! 영수증을 전달해드릴게요."}},
                {"simpleImage": {"imageUrl": selected['url'], "altText": "영수증 이미지"}}
            ]
        }
    })

@app.route('/submit-review', methods=['POST'])
def submit_review():
    data = request.json
    user_id = data.get('userRequest', {}).get('user', {}).get('id')
    image_url = data.get('action', {}).get('params', {}).get('photo')
    reviews.append({"user_id": user_id, "image_url": image_url, "status": "pending"})
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": "리뷰 인증이 완료되었습니다! 사장님 확인 후 송금해드릴게요."}}]}
    })

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if "message" in data and "photo" in data["message"]:
        file_id = data["message"]["photo"][-1]["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
        if "result" in file_info:
            file_path = file_info["result"]["file_path"]
            final_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            
            # 영수증 추가
            receipts.append({"id": len(receipts) + 1, "url": final_url, "used": False})
            
            # 남은 수량 계산
            available_count = len([r for r in receipts if not r['used']])
            
            # 텔레그램 답장에 남은 수량 표시
            chat_id = data["message"]["chat"]["id"]
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text=✅ 영수증 등록 성공! (남은 수량: {available_count}장)")
            
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
