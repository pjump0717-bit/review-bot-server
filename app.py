import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Render 설정에서 가져오는 비밀 정보
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
MY_ID = os.environ.get('MY_TELEGRAM_ID')

# 영수증 보관함 (임시 데이터)
receipts = []

# [기능 1] 영수증 요청 처리
@app.route('/receipt', methods=['POST'])
def get_receipt():
    available = [r for r in receipts if not r['used']]
    if not available:
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "현재 남은 영수증이 없어요! 사장님께 문의해주세요."}}]}})
    
    selected = available[0]
    selected['used'] = True
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [
            {"simpleText": {"text": "영수증입니다! 리뷰 작성 후 스크린샷을 보내주세요."}},
            {"simpleImage": {"imageUrl": selected['url'], "altText": "영수증"}}
        ]}
    })

# [기능 2] 기타 문의사항 텔레그램으로 전달
@app.route('/verify', methods=['POST'])
def handle_verify():
    data = request.json
    user_msg = data['userRequest']['utterance'] # 고객이 보낸 말
    
    # 텔레그램으로 나스님께 알림 쏘기
    msg = f"🔔 [새로운 문의/인증]\n내용: {user_msg}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={MY_ID}&text={msg}"
    requests.get(url)

    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": "접수되었습니다! 사장님이 확인 후 답변드릴게요."}}]}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
