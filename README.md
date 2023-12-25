# Ankeep - Anki Housekeeper

> [!WARNING]
> Ankeep is a work-in-progress. It will take time to polish up all functionality
> to a point where it is ready for general use. In the meantime, if you
> have suggestions on how I could improve Ankeep or implement additional
> functionality, raise an issue on this repository and I will investigate.

The Anki Housekeeper keeps your Anki collection neat and tidy. It can:

1. Automatically tag your cards based on topic.

2. Fix spelling and grammar mistakes (TODO).

3. Format URLs into nice looking hyperlinks (TODO).

4. Notify you of cards that violate the [Twenty rules of formulating knowledge][0].
   These cards are tagged and / or output to the console or a file (TODO).

## Installation

> [!NOTE]
> Requires Python 3.10+

```bash
pip install ankeep
```

```Python
def process(dname, cards, manager: AnkiManager):
    tqdm.write(f"Began linting {dname}.")
    tags_prompt = get_tags_suggestions_multiple()
    definition_prompt = is_definition_multi_card_prompt()
    card_count = 1
    MAX_PROMPT_LENGTH = 3000

    for i, card in enumerate(cards):
        is_final_card = i == len(cards) - 1
        if card.has_lint_tag():
            continue
```

### ChatGPT Access

> [!IMPORTANT]
> You need to provide a ChatGPT API Token to make use of some features.
> You can do this by creating an environment variable called `OPENAI_API_KEY`
> whose value is your token.

Sign up for an account for ChatGPT [here][2].

## Usage

Run `ankeep` in your terminal from anywhere on your filesystem.

### Environment Variable Options

#### OPENAI_API_KEY

Your OpenAI ChatGPT API key.

#### PROFILE_DIR

Path to your Anki profile directory. Can also be specified using a command-line option (see below).

### Command Line Options

Run `ankeep --help` to view all options alongside their explanations.

`-h, --help`
Show available command-line options and exit.

`-p, --profile`
Path to your Anki profile directory.
By default, this points to `$HOME/Library/Application Support/Anki2/<user>`.

`-c, --config`
Read configuration options from a configuration file.
See below for more details.

`-m, --model`
The ChatGPT model to use. GPT-4 models have access to larger, more recent data sets.
The cost of API tokens for each model varies; by default Ankeep is configured to use
an older, less expensive model.

Options: [`"gpt-4"`,`"gpt-4-1106-preview"`,`"gpt-3.5-turbo-1106"`].
Default: `"gpt-3.5-turbo-1106"`.

You can view ChatGPT pricing information [here][1].

`-d, --decknames`
A list of Anki decknames to run Ankeep on. Useful if you have a large collection,
but only need to lint a small portion of your cards.

`-q, --quiet`
Reduces the amount of output produced by Ankeep.

`-v, --verbose`
Increases the amount of output produced by Ankeep.

### The Configuration File

You can optionally configure Ankeep using a configuration file.
Place it in the appropriate location, depending on your Operating System:

- Windows: `~\.ankeep`
- Unix-like (Linux, MacOS, etc.): `$XDG_CONFIG_HOME/ankeep` (`~/.config/ankeep` by default)

[0]: https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge
[1]: https://openai.com/pricing
[2]: https://platform.openai.com/
