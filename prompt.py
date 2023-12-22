def get_tags_suggestions_multiple() -> str:
    prompt = """I'm going to present you with a series of Questions and Answers. Each Question is  from a flashcard that I wrote.
    I would like you to help me categorise it into one or more topics. Tell me the topics you think most accurately describe the question.
    You can pick more than one topic, but do not pick more than four.

    If the content is not related to Computer Science, Engineering, or Mathematics. Ignore my query and do not reply.

    I have provided a list of example topics that you may choose from, but you do not have to use only items from that list.

    Format your response as a numbered list of Questions, with a list of topics beneath, one list per question.

    Example Response:

    Question 1
    Networking
    Systems Design

    Question 2
    Maths
    Number Theory

    Example Topics:

    Software Engineering
    Python
    Golang
    Complexity
    Processes/Threads
    Operating Systems
    Linux
    SRE
    Networking
    Memory/Storage
    Maths
    Number Theory
    Virtualization
    File Systems
    I/O Management
    """
    return prompt


def get_multiple_tags_query_suffix(question: str, index: int = 1) -> str:
    return f"""Question {index}\n{question}\n\n"""


def get_tags_prompt(question: str):
    return f"""
    The text below is the Question portion of a flashcard I wrote. I would like you to help me categorise it into one or more topics. Tell me the topics you think most accurately describe the question. You can pick more than one topic, but do not pick more than four. Only return topics from the list under the 'Topics' heading below. Format your response as a numbered list of topics.

    If the question isn't long enough or provide enough detail to make a guess, reply 'I don't know' and nothing else.

    Topics
    =====
    1. Data Structures
    2. Python
    3. Golang
    4. Markdown
    5. Security
    6. Operating Systems
    7. Linux
    8. Networking
    9. Maths
    10. I/O Management
    11. Hardware

    Question
    =======
    {question}
    """


def get_tags_suggestions_prompt(question: str):
    return f"""
    The text below is the Question portion of a flashcard I wrote. I would like you to help me categorise it into one or more topics. Tell me the topics you think most accurately describe the question.

    If the question isn't long enough or provide enough detail to make a guess, reply 'I don't know' and nothing else.

    Below are some example topics. You can assume that all of the flashcards relate to computer science and software engineering.

    Topics
    =====
    1. Data Structures
    2. Python
    3. Golang
    4. Markdown
    5. Security
    6. Operating Systems
    7. Linux
    8. Networking
    9. Maths
    10. I/O Management
    11. Hardware


    Question
    =======
    {question}
    """


def is_definition_multi_card_prompt():
    return """
    I'm going to present you with a series of Questions and Answers. Each Question is  from a flashcard that I wrote.
    I would like you to tell me if it is a Definition card or not. I.e. a flashcard that asks me to define a term, concept, or topic.

    Format your response as a numbered list of Questions, with a 'Yes' or 'No' underneath each question.
    'Yes' if the Question is a definition card, otherwise 'No'.

    Example Response:

    Question 1
    Yes

    Question 2
    No


    Example Definition Card:

    Question 1
    What is a clock cycle?
    Answer:
    The amount of time between two pulses of an oscillator



    """


def get_definition_prompt_query_suffix(question, answer, index: int = 1):
    return f"""

    Question {index}\n{question}
    Answer:
    {answer[:125]}

    """
