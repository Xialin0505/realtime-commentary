from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
import tempfile
import os
from TTS.api import TTS
import torch
from threading import Lock

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # ✅ 显式允许前端跨域访问

# 初始化模型
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/en/ek1/tacotron2", progress_bar=False, gpu=(device == "cuda"))

# 全局线程锁，防止并发调用模型报错
tts_lock = Lock()

@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' parameter"}), 400

        text = data["text"]

        # 临时文件保存语音
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()

        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_file.name)
            except Exception as error:
                app.logger.error("Failed to delete temp file: %s", error)
            return response

        # 🔒 使用锁串行化调用模型
        with tts_lock:
            tts.tts_to_file(text=text, file_path=temp_file.name)

        return send_file(
            temp_file.name,
            mimetype="audio/wav",
            as_attachment=False  # ✅ 不强制下载，前端可以 Blob 播放
        )

    except Exception as e:
        app.logger.error("TTS error: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)