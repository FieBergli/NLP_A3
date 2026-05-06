from model_utils import analyze_text, get_prompt_a, get_prompt_b, get_prompt_c, load_model


tokenizer, model = load_model()

TEST_SET = [
    "Carrie was always naive and gullible.",
    "She was never promoted as a woman in finance.",
]


for sentence in TEST_SET:
    result_a = analyze_text(sentence, tokenizer, model, get_prompt_a())
    result_b = analyze_text(sentence, tokenizer, model, get_prompt_b())
    result_c = analyze_text(sentence, tokenizer, model, get_prompt_c())
    
    print(f"\nSentence: {sentence}")
    print(f"  A: {result_a['category']} ({result_a['confidence']})")
    print(f"  B: {result_b['category']} ({result_b['confidence']})")
    print(f"  C: {result_c['category']} ({result_c['confidence']})")