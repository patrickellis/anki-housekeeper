import openai
import time
import re
import os
from enum import Enum
from anki_manager import AnkiManager
from dotenv import load_dotenv
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from prompt import (
    is_definition_multi_card_prompt,
    get_definition_prompt_query_suffix,
    get_tags_suggestions_multiple,
    get_multiple_tags_query_suffix,
)


class Model(Enum):
    GPT4_TURBO = "gpt-4-1106-preview"  # $0.01 / 1K tokens
    GPT4_TURBO_VISION = "gpt-4-vision-preview"  # $0.01 / 1K tokens
    GPT4 = "gpt-4"  # $0.03 / 1K tokens
    GPT3 = "gpt-3.5-turbo-1106"  # $0.0010 / 1K tokens
    GPT3_0613 = "gpt-3.5-turbo"


REMOVE_LINT_TAG = False
logger = logging.getLogger(__name__)
tag_pattern = re.compile(r"\d+\.\s+(.+)")
tag_pattern_multi = re.compile(r"Question (\d+)")


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


bot = ChatGPT(Model.GPT3_0613)


def tag_suggestion_multi_query(prompt: str, repeat: int = 1) -> list[list[str]]:
    tags = []
    for _ in range(repeat):
        response = bot.get_completion(prompt)

    curr_tags = []
    curr_question = 0

    for line in response.splitlines():
        match = tag_pattern_multi.search(line)
        if match:
            curr_question += 1
            if curr_question > 1:
                tags.append(curr_tags)
                curr_tags = []
        elif curr_question > 0:
            curr_tags.append(line.replace(" ", "_").replace("-", ""))

    tags.append(curr_tags)

    return tags, response


def definition_multi_query(prompt: str, repeat: int = 2):
    """All queries must return yes for the tag to be applied.

    Configured this way to avoid false positives, but not yet extensively
    tested.
    """
    tags = []
    for _ in range(repeat):
        response = bot.get_completion(prompt)

    for line in response.splitlines():
        if "No" in line:
            tags.append([])
        elif "Yes" in line:
            tags.append(["Definition"])
    return tags, response


def process(dname, cards, manager: AnkiManager):
    tags_prompt = get_tags_suggestions_multiple()
    definition_prompt = is_definition_multi_card_prompt()
    card_count = 1
    MAX_PROMPT_LENGTH = 3000

    for i, card in enumerate(cards):
        is_final_card = i == len(cards) - 1
        if card.has_lint_tag():
            continue

        question = card.question
        answer = card.answer
        answer = answer.strip()

        lines = [
            line
            for line in answer.splitlines()
            if not line.isspace() and not len(line) == 0
        ]
        answer = "\n".join(lines)

        tags_prompt += get_multiple_tags_query_suffix(question, card_count)
        definition_prompt += get_definition_prompt_query_suffix(
            question, answer, card_count
        )

        if is_final_card or any(
            [
                len(tags_prompt) > MAX_PROMPT_LENGTH,
                len(definition_prompt) > MAX_PROMPT_LENGTH,
            ]
        ):
            definition_tags, definition_response = definition_multi_query(
                definition_prompt, repeat=1
            )
            suggested_tags, suggested_response = tag_suggestion_multi_query(
                tags_prompt, repeat=1
            )
            if card_count != len(suggested_tags):
                logger.warning(
                    f"Found {len(suggested_tags)} sets of suggested tags, but there are {card_count} cards."
                )
            else:
                for card, tags in zip(cards[i - card_count : i + 1], suggested_tags):
                    card.add_tags(tags)

            if card_count != len(definition_tags):
                logger.error(
                    f"Found {len(definition_tags)} sets of definition tags, but there are {card_count} cards."
                )
            else:
                for card, tags in zip(cards[i - card_count : i + 1], definition_tags):
                    card.add_tags(tags)

            tags_prompt = get_tags_suggestions_multiple()
            definition_prompt = is_definition_multi_card_prompt()

            card_count = 1
        else:
            card_count += 1

    return dname, cards


class App:
    def __init__(self):
        pass

    def start(self):
        logger.info("Starting Thread Pool..")

        with AnkiManager() as manager:
            args = (
                (dname, cards, manager)
                for dname, cards in manager.cards.items()
                if len(cards) > 0
            )
            n_cards = sum(len(cards) for _, cards in manager.cards.items())
            n_decks = len(manager.cards)
            n_zero_card_decks = list(manager.cards.values()).count(0)
            n_workers = max(min(n_decks - n_zero_card_decks, 10), 1)
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
