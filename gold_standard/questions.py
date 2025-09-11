# Example: Add a few gold standard questions as Python dicts in a list
GOLD_STANDARD_QUESTIONS = [
    {
        "q": "What is an abstract class?",
        "choices": [
            "An abstract class is the name for any class from which you can instantiate an object.",
            "Abstract classes must be redefined any time an object is instantiated from them.",
            "Abstract classes must inherit from concrete classes.",
            "An abstract class exists only so that other 'concrete' classes can inherit from the abstract class."
        ],
        "answer": [3],
        "multi": False
    },
    {
        "q": "What happens when you use the built-in function any() on a list?",
        "choices": [
            "The any() function will randomly return any item from the list.",
            "The any() function returns True if any item in the list evaluates to True. Otherwise, it returns False.",
            "The any() function takes as arguments the list to check inside, and the item to check for. If 'any' of the items in the list match the item to check for, the function returns True.",
            "The any() function returns a Boolean value that answers the question 'Are there any items in this list?'"
        ],
        "answer": [1],
        "multi": False
    }
    # Add more questions as needed...
]