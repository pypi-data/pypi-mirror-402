import hashlib
import re
import numpy as np

class Md5HashTokenizer:
    def __init__(self, vocab_size=8192, max_len=64):
        self.vocab_size = vocab_size
        self.max_len = max_len

    def tokenize(self, text: str) -> np.ndarray:
        # Preprocessing matching Kotlin/JS logic
        lower = text.lower()
        cleaned = re.sub(r'[^a-z0-9\s]', '', lower)
        words = cleaned.split()
        
        tokens = np.zeros(self.max_len, dtype=np.int64)
        count = min(len(words), self.max_len)
        
        for i in range(count):
            word = words[i]
            # Stable MD5 hashing
            h = hashlib.md5(word.encode("utf-8")).hexdigest()
            # Take first 8 hex chars (32 bits)
            val = int(h[:8], 16)
            # Modulo
            token = (val % self.vocab_size) + 1
            tokens[i] = token
            
        return tokens
