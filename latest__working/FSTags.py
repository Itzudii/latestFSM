from llama_cpp import Llama
from FS.fileReader import universal_reader  # uncomment when you need it
import logging

logger = logging.getLogger("FS")

class TagGenerator:
    def __init__(self):
        self.llm = Llama(
            model_path=r"model\\qwen2.5-1.5b-instruct-q8_0.gguf",  # raw string → no escape warning
            n_ctx=8192,  # much safer value
            n_threads=8,
            n_gpu_layers=0,  # set >0 if you get GPU acceleration later
            verbose=False,  # reduces console spam
        )


    def generate_tags_txt(self, text: str) -> list[str]:
        
        # Safety limit – 1.5B model loses focus on very long inputs
        text = text.strip()[:2000]

        # Proper Qwen2.5 chat format + very strict instructions
        prompt = f"""<|im_start|>system
You are a tag extraction machine. Your ONLY allowed output is exactly four lowercase one-word tags separated by comma and space.

Rules you must NEVER break:
- Exactly 4 tags
- Each tag = one single word
- All lowercase
- Separated only by ", "
- NO other text, NO sentence, NO "here are", NO "tags:", NO explanation, NO newline

Perfect examples (copy this style exactly):
python, flask, web, development
ai, neat, game, flappybird
stock, lstm, prediction, finance
javascript, canvas, library, snake
resume, skills, projects, developer

Now process this text and output only the four tags:<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant"""
        logger.info("tag genration start")
        output = self.llm(
            prompt,
            max_tokens=45,  # enough for 4 words + commas + small safety margin
            temperature=0.07,  # almost deterministic
            top_p=0.70,
            top_k=20,
            repeat_penalty=1.12,
            stop=["\n", "<|im_end|>", ":", "sure", "here", "The", "Output", "tags"],
        )

        logger.info("tag genration complete")
        raw = output["choices"][0]["text"].strip()

        logger.info(f"Raw model output:{repr(raw)}")  # ← this is the most important line for debugging

        # Robust cleaning
        cleaned = raw.lower().strip(" .,:;[]{}()\"'")

        # Remove common unwanted prefixes (model sometimes ignores rules slightly)
        prefixes_to_strip = [
            "here are",
            "the tags are",
            "four tags",
            "tags:",
            "output:",
            "keywords:",
            "semantic tags",
            "extracted tags",
        ]
        for p in prefixes_to_strip:
            if cleaned.startswith(p):
                cleaned = cleaned[len(p) :].lstrip(" :,-")

        # Split and take first 4 valid words
        parts = [
            w.strip() for w in cleaned.split(",") if w.strip() and len(w.strip()) > 0
        ]

        if len(parts) >= 4:
            return parts[:4]
        elif len(parts) > 0:
            return (parts + ["unknown"] * 4)[:4]
        else:
            return ["unknown", "unknown", "unknown", "unknown"]

    def generate_tags_path(self, path):
        txt = universal_reader(path)

        tags = self.generate_tags_txt(txt)
        return tags

if __name__ == "__main__":
    # For quick testing (replace with your real file reading later)
    sample_text = """
    Uditya Patel - Software Developer
    Skills: Python, Flask, JavaScript, HTML, CSS, Pygame, Java
    Projects: Stock Prediction (LSTM), Flappy Bird AI (NEAT), Car Rental Website (Flask)
    """

    txt = universal_reader("main.py")
    # print("Input text length:", len(txt))

    gen = TagGenerator()
    tags = gen.generate_tags(txt)
    print("Final tags:", tags)
    print("Joined:", ", ".join(tags))
