def get_tags_prompt(question: str):
    return f"""
    The text below is the Question portion of a flashcard I wrote. I would like you to help me categorise it into one or more topics. Tell me the topics you think most accurately describe the question. You can pick more than one topic, but do not pick more than four. Only return topics from the list under the 'Topics' heading below. Format your response as a numbered list of topics.

    If the question isn't long enough or provide enough detail to make a guess, reply 'I don't know' and nothing else.

    Topics
    =====
    1. Dictionaries
    2. Python
    3. Golang
    4. Complexity
    5. Processes/Threads
    6. Operating Systems
    7. Linux
    8. SRE
    9. Networking
    10. Memory/Storage
    11. Maths
    12. Number Theory
    13. Virtualization
    14. File Systems
    16. I/O Management
    17. Parallel Computing
    18. Hardware
    19. Streaming Processors
    20. Security


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
    1. Dictionaries
    2. Python
    3. Golang
    4. Complexity
    5. Processes/Threads
    6. Operating Systems
    7. Linux
    8. SRE
    9. Networking
    10. Memory/Storage
    11. Maths
    12. Number Theory
    13. Virtualization
    14. File Systems
    16. I/O Management
    17. Parallel Computing
    18. Hardware
    19. Streaming Processors


    Question
    =======
    {question}
    """


def is_definition_card_prompt(question: str, answer: str):
    return f"""
    The text below is the Question and Answer portions of a flashcard I wrote. I would like you to tell me if it a Definition card or not. I.e. a flashcard that asks me to define a term, concept, or topic.

    Respond with 'Yes' if the Question is a definition flashcard, and 'No' otherwise.

    Here is an example of a Definition card to demonstrate:

    Question
    ======
    What is a clock cycle?
    Answer
    =====
    The amount of time between two pulses of an oscillator


    Question
    =======
    {question}
    Answer
    =====
    {answer}
    """
