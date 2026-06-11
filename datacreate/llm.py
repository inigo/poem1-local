import ollama

MODEL = "gemma4:31b"

PROMPT_TEMPLATE = (
    "Write very short poems for a clock display, one for each minute. "
    "Each poem should be 1-2 lines long and clearly include its assigned time in natural language, "
    "not just as digits. "
    "Please produce {count} poems, for {start_time} to {end_time}. "
    "The output format should be [24-hour time in digits]: the poem for that time on a single line. "
    "The poems may reference the current weather which is {weather}."
)


def build_prompt(start_time: str, end_time: str, weather: str, count: int) -> str:
    return PROMPT_TEMPLATE.format(
        start_time=start_time,
        end_time=end_time,
        weather=weather,
        count=count,
    )


def call_llm(prompt: str, model: str = MODEL) -> str:
    response = ollama.generate(model=model, prompt=prompt)
    return response["response"]
