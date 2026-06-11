import ollama

MODEL = "gemma4:31b"

PROMPT_TEMPLATE = (
    "Write very short poems for a clock display, one for each minute. "
    "Each poem should be 1-2 lines long and clearly include its assigned time in natural language, "
    "not just as digits. "
    "For example, use phrases like “twelve exactly”, “one minute after twelve”, “two past twelve”, “five to noon”, "
    "and so on. The poems should feel surprising, and related to the time, suitable for appearing briefly on a clock. "
    "Vary the syntax: some can begin with the time, some can place it mid-line, some can use a fragment, and some can "
    "be a full sentence. Keep the tone playful and poetic rather than functional. The time should be unmistakable, but "
    "embedded gracefully in the poem. Style examples: 'Eight twelve, shadows softly sigh, / a teardrop glistens, as dusk draws nigh'."
    "'Noon appears, wearing sunlight in both ears'. 'Love blooms bright, sweet and serene / It's five thirteen, a fleeting scene'. "
    "'The stars are keen, to see the Earth, at nine sixteen'."
    "Many should rhyme, but not all - maybe two thirds. Make sure to mix up the structure, so the time appears at different places."
    "Before starting, make a list of the numbers, and decide for each the structure and whether it will rhyme. "
    ""
    "Please produce {count} poems, for {start_time} to {end_time}. "
    "The output format should be [24-hour time in digits]: the poem for that time on a single line. "
    "A few of the poems may reference the current weather which is {weather}."
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
