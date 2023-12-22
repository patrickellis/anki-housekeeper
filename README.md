# Anki Housekeeper

The Anki Housekeeper keeps your Anki collection neat and tidy.

You can configure it to:

1. Automatically tag your cards based on topic.

2. Fix spelling and grammar mistakes (TODO).

3. Format URLs into nice looking hyperlinks (TODO).

4. Notify you of cards that violate the [Twenty rules of formulating knowledge][0].
   These cards are tagged and / or output to the console or a file (TODO).

## Installation

```bash
pip install ankeep
```

> [!IMPORTANT]
> You need to provide a ChatGPT API Token to make use of some features.
> You can do this by creating an environment variable called `OPENAI_API_KEY`
> whose value is your token.

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
Path to your Anki profile directory. By default, this points to `$HOME/Library/Application Support/Anki2/<user>`.

`-c, --config`
Read configuration options from a configuration file. See below for more details on the configuration file.

`-q, --quiet`
Reduces the amount of output produced by Ankeep.

`-v, --verbose`
Increases the amount of output produced by Ankeep.

[0]: https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge
