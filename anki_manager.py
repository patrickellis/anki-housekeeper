import csv
import re
from typing import Any, Sequence
from pathlib import Path
import os
from anki.collection import Collection
from anki.exporting import *
from anki.decks import DeckManager
from anki.decks import DeckNameId
import sys


import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
REMOVE_LINT_TAG = False


def get_collection(collection_path: Path) -> Collection | None:
    try:
        return Collection(str(collection_path))
    except FileNotFoundError:
        logger.error(
            f"Collection file not found! File does not exist: {collection_path}"
        )
        sys.exit(1)


def get_deck_manager(col: Collection) -> DeckManager:
    return DeckManager(col)


def get_deck_names(col: Collection) -> list:
    return col.decks.allNames()


def get_deck_names_and_ids(col: DeckManager) -> Sequence[DeckNameId]:
    return col.decks.all_names_and_ids()


def exclude_non_ascii(s: str) -> str:
    return "".join([c for c in s if ord(c) <= 256 and c not in ("/", "\0")])


def clean_html(html: str) -> str:
    return BeautifulSoup(html, "lxml").text.strip()


class Card(object):
    def __init__(self, card: Any, deckName: str, did: str) -> None:
        self.src_card = card
        question_html = card.question()
        lines = question_html.splitlines()
        # Remove tags
        for i, line in enumerate(lines):
            if '<div class="tags">' in line:
                while i < len(lines):
                    lines[i] = ""
                    if "</div>" in lines[i]:
                        break
                    i += 1
        question_html = "\n".join([line for line in lines if line != ""])
        question_html = re.sub(r"(?m)^.*\"decktext\".*$", "", question_html)
        question_html = re.sub(r"(?m)^.*\[\[type:.*\]\].*$", "", question_html)
        answer_html = card.answer()
        self.question = clean_html(question_html)
        self.answer = clean_html(answer_html)
        self.note = self.src_card.note()
        self.tags = self.note.tags
        self.fields = self.note.fields
        self.deck = deckName
        self.did = did

    def remove_lint_tag(self) -> None:
        self.tags = [tag for tag in self.tags if tag != "LINT_TAGS=1"]

    def has_lint_tag(self) -> None:
        return "LINT_TAGS=1" in self.tags

    def add_tags(self, tags: list[str]) -> None:
        self.tags += tags
        self.tags = list(dict.fromkeys(self.tags))

    def get_note_with_tags(self) -> None:
        """Sets the tags of the parent note to the tags of the card,
        and returns the note.
        """
        self.note.tags = self.tags
        return self.note


class AnkiManager(object):
    def __init__(
        self,
        profile_dir: str | None = None,
        collection_filename: str = "collection.anki2",
    ):
        if profile_dir is None:
            profile_dir = os.getenv("PROFILE_DIR")

        self.profile_dir = Path(profile_dir).expanduser()
        self.collection_filename = Path(collection_filename)
        self.collection_path = self.profile_dir / self.collection_filename
        self.collection: Collection = get_collection(self.collection_path)  # type: ignore

        if self.collection is None:
            logger.critical("Could not fetch collection. Aborting.")
            sys.exit(1)

        self.deck_manager = get_deck_manager(self.collection)
        self.decks: tuple[str, str] = []

        for dinfo in get_deck_names_and_ids(self.collection):
            if "SRE" not in dinfo.name or "Vocab" in dinfo.name:
                logger.debug(f"Skipping deck {dinfo.name}")
            else:
                self.decks.append((dinfo.name, dinfo.id))

        self.cards = self.get_cards()

    def flush_cards(self, cards: list[Card]) -> None:
        # TODO: extend this to use col.update_cards() when there are changes to
        # Individual cards being made. Currently we only change tags.
        if REMOVE_LINT_TAG:
            for card in cards:
                card.remove_lint_tag()

        notes = [card.get_note_with_tags() for card in cards]

        if not REMOVE_LINT_TAG:
            for note in notes:
                if "LINT_TAGS=1" not in note.tags:
                    note.tags.append("LINT_TAGS=1")
        self.collection.update_notes([card.get_note_with_tags() for card in cards])

    def flush_all_cards(self) -> None:
        self.flush_cards(self.cards)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.collection.close()

    def get_cards(self):
        cards = {}
        card_info = {
            dname: {"did": did, "cids": self.deck_manager.cids(did)}
            for dname, did in self.decks
        }
        seen = set()
        for dname, ci in sorted(card_info.items(), key=lambda x: len(x[1]["cids"])):
            did = ci["did"]
            cids = ci["cids"]
            cards[dname] = [
                Card(self.collection.get_card(cid), dname, did)
                for cid in cids
                if cid not in seen
            ]
            seen.update(cids)
        return cards

    def write_cards(self, cards: list[Card]):
        logger.debug("Writing cards to questions.csv")
        with open("questions.csv", "w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["deck", "question", "suggested tags"])
            for card in cards:
                writer.writerow([card.deck, card.question, card.suggested_tags])


def main():
    with AnkiManager() as manager:
        manager.write_cards(manager.cards)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    main()
