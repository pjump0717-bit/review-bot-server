import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Render 설정에서 가져오는 비밀 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
MY_ID = os.environ.get('MY_TELEGRAM_ID')

# 영수증 보관함 (메모리에 저장 - 서버 재시작 시 초기화되므로 나중에 DB 연결 권장)
receipts = []

@app.route('/receipt', methods=['POST'])
def get_receipt():
    # 사용 가능한 영수증 필터링
    available = [r for r in receipts if not r['used']]
    
    if not available:
        return jsonify({
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "현재 준비된 영수증이 없어요! 사장님께 문의해주세요."}}]}
        })
    
    selected = available[0]
    selected['used'] = True
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": f"확인했어요! 영수증을 전달해드릴게요. (남은 수량: {len(available)-1}장)"}},
                {"simpleImage": {"imageUrl": selected['url'], "altText": "영수증 이미지"}}
            ]
        }
    })

# 텔레그램에서 보낸 사진을 수집하는 전용 주소
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    if "message" in data and str(data["message"]["from"]["id"]) == MY_ID:
        if "photo" in data["message"]:
            # 가장 해상도가 높은 사진의 file_id 가져오기
            file_id = data["message"]["photo"][-1]["file_id"]
            
            # 텔레그램 API로 파일 경로 가져오기
            file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
            file_path = file_info["result"]["file_path"]
            final_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            
            # 영수증 목록에 추가
            receipts.append({"id": len(receipts) + 1, "url": final_url, "used": False})
            
            # 나스님께 확인 답장 쏘기
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={MY_ID}&text=✅ 영수증 등록 완료! (현재 총 {len(receipts)}장)")
            
    return "OK", 200

@app.route('/verify', methods=['POST'])
def verify_review():
    # 리뷰 인증 접수 시 텔레그램으로 알림만 우선 발송
    data = request.json
    user_id = data['userRequest']['user']['id']
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={MY_ID}&text=🔔 새 리뷰 인증 요청이 왔습니다! 대시보드를 확인하세요.")
    
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": "리뷰가 접수되었습니다! 사장님이 확인 후 1,000원을 보내드릴게요."}}]}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
