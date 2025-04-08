from flask import Flask, request, send_file, jsonify, after_this_request
import tempfile
import os
import threading  # Import the threading module for locks
from TTS.api import TTS
import torch

app = Flask(__name__)

# Initialize TTS model (example using the ek1 tacotron2 model)
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS(model_name="tts_models/en/ek1/tacotron2", progress_bar=False, gpu=(device=="cuda"))

# Create a global lock for TTS synthesis
synthesis_lock = threading.Lock()

@app.route('/synthesize', methods=['POST'])
def synthesize():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "必须传入 'text' 参数"}), 400

        text = data["text"]

        # Create a temporary file to save the generated audio
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_file.close()  # Close file so that TTS can write to it

        # Use after_this_request hook to ensure the temporary file is deleted after the response is sent
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_file.name)
            except Exception as error:
                app.logger.error("删除临时文件时出错: %s", error)
            return response

        # Lock around the TTS synthesis to ensure only one request accesses the TTS engine at a time
        with synthesis_lock:
            tts.tts_to_file(text=text, file_path=temp_file.name)

        return send_file(
            temp_file.name, 
            mimetype="audio/wav", 
            as_attachment=True, 
            download_name="output.wav"
        )
    
    except Exception as e:
        app.logger.error("语音合成过程中出错: %s", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)