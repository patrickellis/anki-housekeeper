import openai
import math
import time
import re
from collections import Counter
import os
from enum import Enum
from anki_manager import AnkiManager
from dotenv import load_dotenv
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from prompt import (
    is_definition_card_prompt,
    get_tags_suggestions_prompt,
    get_tags_prompt,
)

logger = logging.getLogger(__name__)
REMOVE_LINT_TAG = False

# TODO(Ellis): String multiple queries into a single API call and text block.


class Model(Enum):
    GPT4_TURBO = "gpt-4-1106-preview"  # $0.01 / 1K tokens
    GPT4_TURBO_VISION = "gpt-4-1106-vision-preview"  # $0.01 / 1K tokens
    GPT4 = "gpt-4"  # $0.03 / 1K tokens
    GPT3 = "gpt-3.5-turbo-1106"  # $0.0010 / 1K tokens
    GPT3_0613 = "gpt-3.5-turbo"


class ChatGPT:
    def __init__(self, model: Model | None = None):
        self.model = model or Model.GPT4_TURBO

    def get_completion(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        try:
            response = openai.chat.completions.create(
                model=self.model.value,
                messages=messages,
                temperature=0,
            )
        except openai.RateLimitError as e:
            grace_period = re.search(r"Please try again in (\d+\.?\d*)(\w+).", str(e))

            if grace_period:
                time_period, units = grace_period.groups()
                time_period = float(time_period)
                if units not in ["ms", "s", "m"]:
                    logger.debug(f"timeout units not one of (`ms`, `s`, `m`): {units}")
                    time_period = 5
                else:
                    if units == "ms":
                        time_period /= 1000
                    elif units == "m":
                        time_period *= 60
                logger.warning(
                    f"Hit API rate limit. Retrying in {time_period}s.", exc_info=True
                )
            else:
                time_period = 5
                logger.warning(
                    "Hit API rate limit. "
                    "Could not parse error message for timeout period, "
                    f"sleeping for {time_period} seconds.",
                    exc_info=True,
                )
                logger.debug(f"Rate limited for {time_period} seconds.")
            time.sleep(time_period)
            return self.get_completion(prompt)

        return response.choices[0].message.content


tag_pattern = re.compile(r"\d+\.\s+(.+)")
bot = ChatGPT(Model.GPT4)


def tag_suggestion_query(question, answer: str | None = None, repeat: int = 1):
    tags = []
    prompt = get_tags_suggestions_prompt(f"{question}\n{answer}")
    for _ in range(repeat):
        response = bot.get_completion(prompt)
        for line in response.splitlines():
            match = tag_pattern.match(line)
            if match:
                tags.append(match.group(1).replace(" ", "_"))

    c = Counter(tags)
    tags = [tag for tag in c.keys() if c[tag] >= repeat // 2]
    return tags


def definition_query(question, answer: str | None = None, repeat: int = 2):
    """All queries must return yes for the tag to be applied.

    Configured this way to avoid false positives, but not yet extensively
    tested.
    """
    for _ in range(repeat):
        prompt = is_definition_card_prompt(question, answer)
        response = bot.get_completion(prompt)
        if "Yes" not in response:
            logger.debug(
                f"Card not a definition. Q: \n{question}.\nA: \n{answer[:300]}"
            )
            return False
    return True


def process(dname, cards, manager: AnkiManager):
    for i, card in enumerate(cards):
        if i != 0 and i % 10 == 0:
            tqdm.write(f"{dname}: +10 -> {i}")

        if card.has_lint_tag():
            continue

        question = card.question
        answer = card.answer
        tags = []

        # tags = tag_suggestion_query(question, answer, repeat=2)
        # tags.append("LINT_TAGS=1")

        is_definition = definition_query(question, answer, repeat=1)
        if is_definition:
            tags.append("Definition")

        card.add_suggested_tags(tags)
        if REMOVE_LINT_TAG:
            card.remove_lint_tag()

    return dname, cards


class App:
    def __init__(self):
        pass

    def start(self):
        logger.info("Starting Thread Pool..")

        with AnkiManager() as manager:
            card_data = [
                (d, cards) for d, cards in manager.cards.items() if len(cards) > 0
            ]
            n_total_decks = len(manager.cards)

            for i in range(0, n_total_decks, 5):
                logger.info(
                    f"Processing batch {i//5} ({i}-{i+5}) of {math.ceil(n_total_decks / 5)}"
                )
                batch = list(card_data)[i : i + 5]
                args = (
                    (dname, cards, manager) for dname, cards in batch if len(cards) > 0
                )
                n_cards = sum(len(cards) for _, cards in batch)
                n_decks = len(batch)
                n_zero_card_decks = sum(len(cards) == 0 for _, cards in batch)
                n_workers = min(n_decks - n_zero_card_decks, 10)
                logger.info(f"Spawning {n_workers} Thread Workers.")

                with tqdm(total=n_cards) as pbar:
                    with ThreadPoolExecutor(max_workers=n_workers) as executor:
                        futures = [
                            executor.submit(process, *arguments) for arguments in args
                        ]
                        for future in as_completed(futures):
                            dname, cards = future.result()
                            pbar.update(len(cards))
                            tqdm.write(f"{dname} complete. {len(cards)} linted.")
                            manager.flush_cards(cards)


def main() -> None:
    try:
        app = App()
        app.start()
    except Exception:
        logger.error("Unhandled exception.", exc_info=True)


if __name__ == "__main__":
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, datefmt="%H:%M:%S")
    logger.setLevel(level=logging.INFO)
    main()
