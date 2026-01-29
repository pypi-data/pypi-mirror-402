import pytest
import os
try:
    import onnxruntime
except ImportError:
    onnxruntime = None

from safellmkit import GuardrailsEngine, StrictPolicy, OnnxJailbreakClassifier

@pytest.mark.skipif(onnxruntime is None, reason="onnxruntime not installed")
def test_onnx_inference_flow():
    # Assuming user has a model file for testing, or we mock it.
    # Since we can't guarantee a model file in CI, checking if creating classifier works gracefully
    # or fails with "failed to load" is enough.
    
    # Mocking path that doesnt exist
    clf = OnnxJailbreakClassifier("dummy_path.onnx")
    # predict should return False, 0.0 without crash (due to logged error caught in init)
    # Actually code implementation catches Init error but sets session=None
    is_jb, prob = clf.predict("test")
    assert not is_jb
    assert prob == 0.0

    # If we had a real model we would test it. 
    # For now ensuring the engine accepts it and runs.
    engine = GuardrailsEngine(StrictPolicy(), classifier=clf)
    res = engine.validate_input("test")
    assert res is not None
