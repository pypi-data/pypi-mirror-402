import mxupy as mu

from pathlib import Path


class ASR():

    def __init__(self):
        super().__init__()
        # 第一次则创建识别器
        if not hasattr(self, 'voice_recognizer'):
            self.voice_recognizer = self.create_recognizer()

    def create_recognizer(self):
        """
            加载语音识别模型

        Returns:
            recognizer：识别器
        """
        import sherpa_onnx
        path = "./models/sherpa-onnx-paraformer-zh-2024-03-09/"
        model = path + "model.onnx"
        tokens = "tokens.txt"
        rule_fsts = "itn_zh_number.fst"

        if (not Path(model).is_file() or not Path(tokens).is_file() or not Path(rule_fsts).is_file()):
            raise ValueError("""
                    Please download model files from
                    https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models
                """)
        return sherpa_onnx.OfflineRecognizer.from_paraformer(
            paraformer=model,
            tokens=tokens,
            debug=True,
            rule_fsts=rule_fsts,
        )

    def recognize(self, file_path):
        """
            识别语音

        Args:
            file_path (str): 语音文件路径

        Returns:
            IM: 识别结果
        """
        import soundfile as sf
        im = mu.IM()

        if not Path(file_path).is_file():
            return mu.IM(False, '文件不存在', code=404)

        recognizer = self.voice_recognizer
        stream = recognizer.create_stream()

        audio, sample_rate = sf.read(file_path, dtype="float32", always_2d=True)
        # 仅使用第一个通道
        audio = audio[:, 0]

        recognizer = self.voice_recognizer
        stream = recognizer.create_stream()
        stream.accept_waveform(sample_rate, audio)
        recognizer.decode_stream(stream)
        q = stream.result.text
        im.data = q

        return im