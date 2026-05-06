import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Render 설정에서 가져오는 비밀 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# 영수증 보관함 (전역 변수)
receipts = []

@app.route('/receipt', methods=['POST'])
def get_receipt():
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

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    # 보안 체크를 잠시 해제하고 모든 사진을 수용합니다.
    if "message" in data and "photo" in data["message"]:
        file_id = data["message"]["photo"][-1]["file_id"]
        
        # 텔레그램에서 파일 경로 가져오기
        file_info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}").json()
        if "result" in file_info:
            file_path = file_info["result"]["file_path"]
            final_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            
            # 목록에 추가
            receipts.append({"id": len(receipts) + 1, "url": final_url, "used": False})
            
            # 보낸 사람에게 확인 답장 (선택 사항)
            chat_id = data["message"]["chat"]["id"]
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text=✅ 영수증 등록 성공! (현재 총 {len(receipts)}장)")
            
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
