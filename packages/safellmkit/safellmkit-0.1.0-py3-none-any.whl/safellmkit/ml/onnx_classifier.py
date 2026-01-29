import logging
from typing import Optional, Tuple

try:
    import onnxruntime as ort
    import numpy as np
except ImportError:
    ort = None
    np = None

from .tokenizer import Md5HashTokenizer

class OnnxJailbreakClassifier:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session = None
        self.tokenizer = None
        
        if ort:
            try:
                self.session = ort.InferenceSession(model_path)
                self.tokenizer = Md5HashTokenizer()
            except Exception as e:
                logging.warning(f"Failed to load ONNX model: {e}")
        else:
            logging.warning("onnxruntime not installed. OnnxJailbreakClassifier disabled.")

    def predict(self, text: str) -> Tuple[bool, float]:
        """
        Returns (is_jailbreak, probability)
        """
        if not self.session or not self.tokenizer:
            return False, 0.0

        try:
            tokens = self.tokenizer.tokenize(text)
            # Reshape to (1, max_len)
            input_feed = {self.session.get_inputs()[0].name: tokens.reshape(1, -1)}
            output = self.session.run(None, input_feed)[0]
            probability = float(output[0][0])
            
            # Assuming output is probability of positive class (jailbreak)
            return probability >= 0.5, probability
        except Exception as e:
            logging.error(f"Inference failed: {e}")
            return False, 0.0
