import csv
import re
from typing import Any
from pathlib import Path
import os
from anki.collection import Collection, DeckIdLimit
from anki.exporting import *
from anki.decks import DeckManager, DeckDict
from anki.decks import DeckNameId


import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
PROFILE_DIR = Path(os.getenv("PROFILE_DIR")).expanduser()
GLOBAL_DECK_NAME = "global config for FSRS4Anki"
MAKE_BACKUPS = False


def get_collection(filename: str = "collection.anki2") -> Collection | None:
    collection_path = PROFILE_DIR / filename
    try:
        return Collection(str(collection_path))
    except FileNotFoundError:
        log.error(f"Collection file not found! File does not exist: {collection_path}")


def get_deck_manager(col: Collection) -> DeckManager:
    return DeckManager(col)


def get_exporter(col: Collection) -> AnkiPackageExporter:
    return AnkiPackageExporter(col)


def get_deck_names(col: Collection) -> list:
    return col.decks.allNames()


def get_deck_names_and_ids(col: DeckManager) -> Sequence[DeckNameId]:
    return col.decks.all_names_and_ids()


def exclude_non_ascii(s: str) -> str:
    return "".join([c for c in s if ord(c) <= 256 and c not in ("/", "\0")])


"""
See [here](https://github.com/open-spaced-repetition/fsrs4anki/blob/5a34201f4d5b3a9cc1a5da4511b6bc32b7c6e909/fsrs4anki_optimizer.ipynb)
for more details and explanations of the options below.
"""


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

    def add_suggested_tags(self, tags: list[str]) -> None:
        self.suggested_tags = tags
        self.tags += tags
        self.tags = list(dict.fromkeys(self.tags))

    def get_note_with_tags(self) -> None:
        """Sets the tags of the parent note to the tags of the card,
        and returns the note.
        """
        self.note.tags = self.tags
        return self.note


# Export
def backup(deck: DeckDict | None, name: str) -> None:
    """
    Makes a backup of the deck with the given name.
    """
    if name != GLOBAL_DECK_NAME and not deck:
        raise ValueError(f"Deck {name} not found!")

    fname = os.path.abspath(f"{exclude_non_ascii(name)}.apkg")
    fd = open(fname, "w")
    os.unlink(fname)
    fd.close()

    if name == GLOBAL_DECK_NAME:
        collection.export_collection_package(
            out_path=fname, include_media=False, legacy=True
        )
    else:
        collection.export_anki_package(
            out_path=fname,
            limit=DeckIdLimit(deck["id"]),
            with_scheduling=True,
            with_media=False,
            legacy_support=True,
        )


class AnkiManager(object):
    def __init__(self):
        self.collection: Collection = get_collection()  # type: ignore

        if self.collection is None:
            logger.critical("Could not fetch collection. Aborting.")

        self.deck_manager = get_deck_manager(self.collection)
        self.decks: tuple[str, str] = []

        for dinfo in get_deck_names_and_ids(self.collection):
            # if "SRE" not in dinfo.name:
            if "SRE" not in dinfo.name:
                logger.debug(f"Skipping deck {dinfo.name}")
            else:
                self.decks.append((dinfo.name, dinfo.id))

        self.cards = self.get_cards()

    def flush_cards(self, cards: list[Card]) -> None:
        # TODO: extend this to use col.update_cards() when there are changes to
        # Individual cards being made. Currently we only change tags.
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
        print("Writing cards to questions.csv")
        with open("questions.csv", "w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerow(["deck", "question", "suggested tags"])
            for card in cards:
                writer.writerow([card.deck, card.question, card.suggested_tags])


def main():
    with AnkiManager() as manager:
        manager.write_cards(manager.cards)


if __name__ == "__main__":
    main()
