__author__ = 'Rhea Ramachandran'

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
    healthy = 5  # str
    exercise = 6
    buddy = 7  # str
    balance = 8
    food = 9
    healthy_diet = 10  # str


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
                                                        '`I spend alot of time` $TOPIC`too. Do you make it part of your daily schedule?`': {
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
        '`I hear you. I would say it\'s part of my mine, but I also make sure to do other things as well because it is important to have balance. Would you say you have a healthy lifestyle?`': {
            '#SET_LIFESTYLE #GET_LIFESTYLE': {
                '#IF($HEALTHY) `That\'s great to hear! I\'m guessing you\'ve been getting enough physical exercise then?`': {
                    '#SET_EXERCISE #GET_EXERCISE': {
                        '#IF($EXERCISE) `Wow. That\'s impressive! I mostly like to go for runs, either 5 or 6 times a week. My favorite part about working out is grabbing a bite to eat afterwards.`': {
                            'error': 'food'
                        },
                        '`I know alot of people struggle with getting physical activity in, especially during busy school weeks. Have you tried finding a workout buddy to help you stay motivated?`': {
                            'score': 0.1,
                            '#SET_EXERCISE #GET_EXERCISE': {
                                '#IF($BUDDY) `That\'s really nice. The best part about working out with friends is grabbing a bite to eat after!`': {
                                    'error': 'food'
                                },
                                '`Aww I get it, its hard to find people with the same interests as you. Sometimes, when I don\'t feel like going to the gym I motivate myself by grabbing a bite to eat afterwards.`': {
                                    'score': 0.1,
                                    'error': 'food'
                                }
                            },
                            'error': {
                                '`Sorry, I didn\'t catch that.`': 'end'
                            }
                        }
                    },
                    'error': {
                        '`Sorry, I didn\'t catch that.`': 'end'
                    }
                },
                '`Aww. I know how hard it is to balance everything. What do you think you need to work on the most?`': {
                    'score': 0.1,
                    '#SET_BALANCE': {
                        '#GET_BALANCE': {
                            'error': {
                                '`I hear you. I always try to do what\'s best for my mental and physical health. I find that treating myself to yummy food helps me cope with everyday stressors`': {
                                    'error': 'food'
                                }
                            }
                        }
                    },
                    'error': {
                        '`Sorry, I didn\'t catch that.`': 'end'
                    }
                }
            },
            'error': {
                '`Sorry, I didn\'t catch that.`': 'end'
            }
        }
    }

    food_transitions = {
        'state': 'food',
        '`Mhmm. I usually like to eat pretty healthy, so my favorite place to grab a bite to eat is Cava. What\'s your fav place to eat at?`': {
            '#SET_FOOD': {
                '#GET_FOOD': {
                    '#SET_EATING #GET_EATING': {
                        '#IF($HEALTHYDIET) `Awesome! I\'m glad you are taking good care of yourself:) Sometimes, its hard to maintain a balanced diet, especially if you travel alot.`': {
                            'error': 'travel'
                        },
                        '`You should make sure to eat whole foods like fruits and veggies, without giving up the other foods you enjoy. Have you seen the show, Vegucated?`': {
                            'score': 0.1,
                            'error': {
                                '`It\'s one of my favorites! It\'s surprisingly funny and it really emphasizes the importance of eating foods that fuel you.`': {
                                    'error': {
                                        '`Thanks for hearing me out! While we are on the topic, why don\'t you tell me more about the kinds of movies/shows you like to watch?`': {
                                            'error': 'entertainment'
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
            },
            'error': {
                '`Sorry, I didn\'t catch that.`': 'end'
            }
        }
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(health_transitions)
    df.load_transitions(food_transitions)
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
    if vars['TOPIC'] == "nothing" or vars['TOPIC'] == "not much" or vars['TOPIC'] == "nothing much" or vars[
        'TOPIC'] == "n/a":
        vars['TOPIC'] = "relaxing"
        return "Ahh. Sometimes its nice to sit back and relax."

    return topic + " is well worth your time. It's a great way to keep yourself occupied."


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


def get_lifestyle(vars: Dict[str, Any]):
    healthy = vars[V.healthy.name]
    print(healthy)
    vars['HEALTHY'] = False
    if healthy == "yes":
        vars['HEALTHY'] = True
    return True


def get_exercise(vars: Dict[str, Any]):
    exercise = vars[V.exercise.name]
    vars['EXERCISE'] = False
    if exercise == "yes":
        vars['EXERCISE'] = True
    return True


def get_buddy(vars: Dict[str, Any]):
    buddy = vars[V.buddy.name]
    vars['BUDDY'] = False
    if buddy == "yes":
        vars['BUDDY'] = True
    return True


def get_balance(vars: Dict[str, Any]):
    balance = vars[V.balance.name]
    vars['BALANCE'] = balance
    if balance == "none":
        return "I hear you. I usually struggle with getting enough sleep, but the key is to put your health first. Everything else comes second."
    return balance + " can be very difficult. I struggle with that too. The key is to put your health first no matter what. Everything else comes second."


def get_food(vars: Dict[str, Any]):
    food = vars[V.food.name]
    if food == 'none':
        return "Gotcha. Home-cooked food is also the way to go sometimes, especially if you are a healthy-eater. Would you say you have a pretty good diet?"
    return "I love " + food + "! It's delicious. I also like to eat home-cooked food because I like knowing exactly whats in it. Would you say you have a pretty good diet?"


def get_eating(vars: Dict[str, Any]):
    healthyDiet = vars[V.healthy_diet.name]
    vars['HEALTHYDIET'] = False
    if healthyDiet == "yes":
        vars['HEALTHYDIET'] = True
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
    # modified
    'SET_TOPIC': MacroGPTJSON(
        'What activity has the user been up to, if anything?',
        {V.activity.name: "watching sports"}, {V.activity.name: "working out"}
    ),
    'GET_TOPIC': MacroNLG(get_topic),
    # 'DETERMINE_CATEGORY': MacroGPTJSON(
    #     'Which of the following categories is closest to what the user is talking about: health, travel, entertainment, or none of these?',
    #     {V.category.name: "health"},
    #     {V.category.name: "entertainment"}
    # ),
    # 'SORT_CATEGORY': MacroNLG(sort_category)
    'SET_LIFESTYLE': MacroGPTJSON(
        'Is the speaker indicating that they have a healthy lifestyle, yes or no?',
        {V.healthy.name: "yes"},
        {V.healthy.name: "no"}
    ),
    'GET_LIFESTYLE': MacroNLG(get_lifestyle),
    'SET_EXERCISE': MacroGPTJSON(
        'Is the speaker indicating that they exercise, yes or no?',
        {V.exercise.name: "yes"},
        {V.exercise.name: "no"}
    ),
    'GET_EXERCISE': MacroNLG(get_exercise),
    'SET_BUDDY': MacroGPTJSON(
        'Is the speaker indicating that they have a workout buddy, yes or no?',
        {V.buddy.name: "yes"},
        {V.buddy.name: "no"}
    ),
    'GET_BUDDY': MacroNLG(get_buddy),
    'SET_BALANCE': MacroGPTJSON(
        'What is the user indicating that they need to work on?',
        {V.balance.name: "managing homework", V.balance.name: "getting enough sleep"},
        {V.balance.name: "nothing"}
    ),
    'GET_BALANCE': MacroNLG(get_balance),
    'SET_FOOD': MacroGPTJSON(
        'What is the user\'s favorite place to eat?',
        {V.food.name: "chipotle", V.food.name: "subway"},
        {V.food.name: "none"}
    ),
    'GET_FOOD': MacroNLG(get_food),
    'SET_EATING': MacroGPTJSON(
        'Is the speaker indicating that they have a healthy diet, yes or no?',
        {V.healthy_diet.name: "yes"},
        {V.healthy_diet.name: "no"}
    ),
    'GET_EATING': MacroNLG(get_eating)
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
