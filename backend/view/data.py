import json


def get_index_data():
    all_data = {
        "text_input": {
            "text": "Hello world!."
        },
        "text_output": {
            "locations": ["location A", "location B"],
            "organizations": ["Org A"],
            "persons": ["person A", "person B"]
        },
    }
    return all_data
