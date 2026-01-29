import argparse
import sys
import json
from .engine import GuardrailsEngine, StrictPolicy
from .ml import OnnxJailbreakClassifier

def main():
    parser = argparse.ArgumentParser(description="SafeLLMKit CLI")
    parser.add_argument("prompt", type=str, help="Input prompt to validate")
    parser.add_argument("--onnx", type=str, help="Path to ONNX model", default=None)
    
    args = parser.parse_args()
    
    classifier = None
    if args.onnx:
        classifier = OnnxJailbreakClassifier(args.onnx)
        
    engine = GuardrailsEngine(StrictPolicy(), classifier)
    result = engine.validate_input(args.prompt)
    
    # Print JSON output
    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
