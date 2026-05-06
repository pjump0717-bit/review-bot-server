import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Render 설정에서 가져오는 비밀 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# 데이터 저장소
receipts = []       # 영수증 보관함
issued_users = set() # 영수증을 이미 받아간 사용자 ID 저장 (중복 방지)

@app.route('/receipt', methods=['POST'])
def get_receipt():
    data = request.json
    user_id = data.get('userRequest', {}).get('user', {}).get('id') # 카톡 유저 고유 ID
    
    # 1. 이미 영수증을 받은 사람인지 확인
    if user_id in issued_users:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "이미 오늘자 영수증을 받으셨습니다! 내일 다시 이용해주세요."}}]}
        })

    # 2. 사용 가능한 영수증이 있는지 확인
    available = [r for r in receipts if not r['used']]
    
    if not available:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "현재 준비된 영수증이 없어요! 사장님께 문의해주세요."}}]}
        })
    
    # 3. 영수증 발급 프로세스
    selected = available[0]
    selected['used'] = True
    issued_users.add(user_id) # 해당 유저를 '발급 완료' 목록에 추가
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "확인했어요! 영수증을 전달해드릴게요."}},
                {"simpleImage": {"imageUrl": selected['url'], "altText": "영수증 이미지"}}
            ]
        }
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
            
            receipts.append({"id": len(receipts) + 1, "url": final_url, "used": False})
            
            chat_id = data["message"]["chat"]["id"]
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text=✅ 영수증 등록 성공!")
            
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
