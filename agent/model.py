
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)

import torch

MODEL_NAME = "CohereLabs/aya-expanse-8b"

def load_model():

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto"
    )

    model.eval()

    return model, tokenizer
