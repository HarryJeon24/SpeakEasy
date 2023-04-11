import pickle
from emora_stdm import DialogueFlow, Macro, Ngrams
from typing import Dict, Any, List
import re
import time
import json
import requests
import random
from enum import Enum
from typing import Dict, Any
import openai
from emora_stdm import DialogueFlow
import utils
from utils import MacroGPTJSON, MacroNLG

class V(Enum):
    person_name = 0  # str
    person_feeling = 1  # str
    implemented_advice = 2  # str
    activity = 3  # str
    category = 4  # str


def visits() -> DialogueFlow:
    transitions = {
        'state': 'start',
        '#TIME #ASK_NAME': {
            '#SET_NAME #GET_NAME': {
                # new user
                '#IF($NEW_USER) `Hi,` $NAME `. Nice to meet you. How are you doing?`': {
                    '#SET_FEELING': {
                        '#GET_FEELING `What have you been up to recently?`': {
                            '#SET_TOPIC': {
                                '#GET_TOPIC': {
                                    'error': {
                                        '`I also spend a good amount of time` $TOPIC`. Is it part of your everyday routine?`': {
                                            'error': 'health'
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                '`Welcome back,` $NAME `! How have you been?`': {
                    'score': 0.1,
                    '#SET_FEELING': {
                        '#GET_FEELING `Did you get a chance to work on those speaking tips I gave you last time?`': {
                            '#SET_LISTENED': {
                                '#GET_LISTENED': {
                                    '#SET_RATING': {
                                        '`Thanks for evaluating my feedback! Now, I\'d love to hear more about you. What have you been up to recently?`': {
                                            '#SET_TOPIC': {
                                                '#GET_TOPIC': {
                                                    'error': {
                                                        '#UNX `I spend alot of time` $TOPIC`too. Is it part of your daily schedule?`': {
                                                            'error': 'health'
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                    }

                                }

                            },
                            'error': {
                                '`Sorry, I didn\'t catch that.`': 'end'
                            }
                        }
                    }

                }

            },
            'error': {
                '`Sorry, I didn\'t catch that.`': 'end'
            }
        }
    }

    health_transitions = {
        'state': 'health',
    }

    travel_transitions = {
        'state': 'travel',
    }
    entertainment_transitions = {
        'state': 'entertainment',
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(health_transitions)
    df.load_transitions(travel_transitions)
    df.load_transitions(entertainment_transitions)
    df.add_macros(macros)
    return df


def get_feeling(vars: Dict[str, Any]):
    feeling = vars[V.person_feeling.name]
    if feeling == "good":
        return "I'm happy to hear you are doing well! I'm not so bad myself. "
    elif feeling == "bad":
        return "I'm sorry to hear that:( I hope things get better soon."
    else:
        return "Glad to hear you are doing okay. I'm doing alright too."


def get_listened(vars: Dict[str, Any]):
    listened = vars[V.implemented_advice.name]
    if listened == "yes":
        return "I'm glad you were able to practice my tips. How helpful would you say the advice was on a scale of 1 to 5 (with 5 being very helpful)?"
    elif listened == "no":
        return "Hopefully you get a chance to practice them going forwards. How helpful do you think my advice was on a scale of 1 to 5 (with 5 being very helpful)?"
    else:
        return "Gotcha. How helpful do you think my advice was on a scale of 1 to 5 (with 5 being very helpful)?"


class MacroTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        hour = time.strftime("%H")
        if int(hour) < 12:
            return "Good morning!"
        if 12 < int(hour) < 17:
            return "Good afternoon!"
        else:
            return "Good evening!"


class MacroAskName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        options = (
            "What's your name?", "What can I call you?", "Can I have your name?", "What do you call yourself?")
        return random.choice(options)


def get_topic(vars: Dict[str, Any]):
    topic = vars[V.activity.name]
    vars['TOPIC'] = topic
    return topic + " is excellent. It's nice to keep yourself busy while doing what you enjoy."


def get_name(vars: Dict[str, Any]):
    name = vars[V.person_name.name]
    vars['NAME'] = name
    vn = 'LIST_OF_NAMES'
    usersDict = {}
    new_user = True
    if 'USERS' not in vars:
        vars['USERS'] = usersDict
    else:
        if name in vars['USERS']:
            new_user = False
        else:
            (vars['USERS'])[name] = []
    vars['NEW_USER'] = new_user
    return True


# def sort_category(vars: Dict[str, Any]):
#     category = vars[V.category.name]
#     if category == "health":
#         vars['HEALTH'] = 'True'
#     if category == "entertainment":
#         vars['ENTERTAINMENT'] = 'True'
#     if category == "entertainment":
#         vars['TRAVEL'] = 'True'


class MacroSetRating(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        r = re.compile(r"(1|2|3|4|5|one|two|three|four|five|One|Two|Three|Four|Five)")
        m = r.search(ngrams.raw_text())
        if m == "1" or "one" or "One":
            (vars['USERS'])[vars['NAME']].append(1)
        if m == "2" or "two" or "Two":
            (vars['USERS'])[vars['NAME']].append(2)
        if m == "3" or "three" or "Three":
            (vars['USERS'])[vars['NAME']].append(3)
        if m == "4" or "four" or "Four":
            (vars['USERS'])[vars['NAME']].append(4)
        if m == "5" or "five" or "Five":
            (vars['USERS'])[vars['NAME']].append(5)
        return True


macros = {
    'TIME': MacroTime(),
    'ASK_NAME': MacroAskName(),
    'GET_NAME': MacroNLG(get_name),
    'SET_NAME': MacroGPTJSON(
        'How does the speaker want to be called?',
        {V.person_name.name: "Mike Johnson"},
        {V.person_name.name: "Michael"}
    ),
    'SET_FEELING': MacroGPTJSON(
        'Is the speaker doing good, bad, or okay?',
        {V.person_feeling.name: "good"},
        {V.person_feeling.name: "bad"}
    ),
    'GET_FEELING': MacroNLG(get_feeling),
    'GET_LISTENED': MacroNLG(get_listened),
    'SET_LISTENED': MacroGPTJSON(
        'Is the speaker indicating that they took my advice, yes or no?',
        {V.implemented_advice.name: "yes"},
        {V.implemented_advice.name: "no"}
    ),
    'SET_RATING': MacroSetRating(),
    'SET_TOPIC': MacroGPTJSON(
        'What activity has the user been up to',
        {V.activity.name: "watching sports"},
        {V.activity.name: "working out"}
    ),
    'GET_TOPIC': MacroNLG(get_topic),
    # 'DETERMINE_CATEGORY': MacroGPTJSON(
    #     'Which of the following categories is closest to what the user is talking about: health, travel, entertainment, or none of these?',
    #     {V.category.name: "health"},
    #     {V.category.name: "entertainment"}
    # ),
    # 'SORT_CATEGORY': MacroNLG(sort_category)
}


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    d = pickle.load(open(varfile, 'rb'))
    df.vars().update(d)
    df.run()
    save(df, varfile)


if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    load(visits(), 'resources/userLog.pkl')