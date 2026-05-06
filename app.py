from flask import Flask, request, jsonify

app = Flask(__name__)

# 임시 데이터베이스 (나중에 구글 시트 등으로 연동 가능)
# 여기에 나스님이 준비한 영수증 이미지 주소(URL)를 넣으시면 됩니다.
receipts = [
    {"id": 1, "url": "https://your-image-link-1.com/image.jpg", "used": False},
    {"id": 2, "url": "https://your-image-link-2.com/image.jpg", "used": False},
]

@app.route('/receipt', methods=['POST'])
def get_receipt():
    # '영수증이 없어요' 버튼을 눌렀을 때 실행됨
    available = [r for r in receipts if not r['used']]
    if not available:
        return jsonify({"version": "2.0", "template": {"outputs": [{"simpleText": {"text": "현재 남은 영수증이 없어요! 사장님께 채팅으로 문의해주세요."}}]}})
    
    selected = available[0]
    selected['used'] = True # 사용됨 처리
    
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": "여기 영수증입니다! 리뷰 작성 후 스크린샷을 보내주세요."}},
                {"simpleImage": {"imageUrl": selected['url'], "altText": "영수증 이미지"}}
            ]
        }
    })

@app.route('/verify', methods=['POST'])
def verify_review():
    # '리뷰 작성했어요' 버튼 후 사진을 보냈을 때 실행됨
    # (여기에 나중에 Gemini AI 판별 로직이 들어갑니다)
    return jsonify({
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": "리뷰 인증샷이 접수되었습니다! AI가 확인 중이니 잠시만 기다려주세요."}}]}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
