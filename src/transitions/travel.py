import random
from enum import Enum
from typing import Dict, Any

import openai
from emora_stdm import DialogueFlow

from src import utils
from src.utils import MacroGPTJSON, MacroNLG

import requests

# url = "https://api.foursquare.com/v3/places/5a187743ccad6b307315e6fe/tips?limit=1&fields=text&sort=POPULAR"
#
# headers = {
#     "accept": "application/json",
#     "Authorization": "fsq3gXbQNZVL7/XgHr8QJqBec8QhAUAdyHITSHQ3cfch/Ho="
# }
#
# response = requests.get(url, headers=headers)
#
# print(response.text)

# PATH_USER_INFO = 'resources/userinfo.json'


class V(Enum):
    location = 0,
    favoriteThing = 1,
    activity = 2


def main() -> DialogueFlow:
    transitions = {
        'state': 'start',
        '`Hi, where are you from?`': {
            '#SET_LOCATION': {
                '`That\'s awesome! I\'m from Austria. I\'ve never been to` #GET_LOCATION `though, is it nice?`': {
                    '[<{of course, yes, duh, yeah, nice, good, great, lovely, fantastic, ok, okay, fine, good}>]': {
                        '`I\'m glad! Maybe I should plan a visit. What is your favorite part about it?`': {
                            '#SET_FAVORITE': {
                                '`That makes sense.` #GET_FAVORITE `is really important. That is why I want to live '
                                'in Barcelona.`': 'barcelona'
                            },
                            '[<{who knows, do not know, idk, anything, dont know, no, not, nah}>]': {
                                '`Ah, okay. I guess I\'ll ask google...`': 'other_location'
                            },
                            'error': {
                                '`Nice! Thanks for sharing.`': 'end'
                            }
                        }
                    },
                    '[<{how, what, where, you, about}>]': {  # figure out how to deal w questions
                        '`I really like Austria. It\'s where The Sound of Music was filmed`': 'end'  # TRANSITION TO ENTERTAINMENT
                    },
                    '[<{no, not, nah, never, eh, sort of, hate, mid, rainy, horrible, whack, bad, lame}>]': {
                        '`Ah that sucks. Where would you rather live?`': {
                            '[<{who knows, do not know, idk, anywhere, dont know}>]': {
                                '`Hey, the world is your oyster! I want to live in Barcelona.`': 'barcelona'
                            },
                            '#SET_LOCATION': {
                                '`That is so cool! I have always wanted to visit ` #GET_LOCATION `. `': 'end'
                            },
                            'error': {
                                '`Thanks for sharing!.`': 'other_location'
                            }
                        }
                    },
                    'error': {
                        '`Nice, thanks for sharing.`': 'end'
                    }
                }
            },
            'error': {
                '`Sorry, I didn\'t understand you.`': 'end'
            }
        },
    }

    barcelona = {
        'state': 'barcelona',
        '`Have you ever been?`': {
            '[<{no, not, nah, never, eh}>]': {
                '`Me neither! Hopefully we can both visit someday`': 'end'
            },
            '[<{of course, yes, duh, yeah, nice, good, great, lovely, fantastic, ok, okay, fine, good}>]': {
                '`Wow! I\'m so jealous. What did you do there?`': {
                    '#SET_ACTIVITY': {
                        '`No way, I have always wanted to ` #GET_ACTIVITY `. It\'s on my bucketlist!`': 'end'
                    },
                    'error': {
                        '`I see. Sounds fun!`': 'end'
                    }
                }
            },
            'error': 'other_location'
        }
    }

    other_location = {
        'state': 'other_location',
        '`Are there any other places you would like to live or visit?`': {
            '#SET_LOCATION': {
                '`I love` #GET_LOCATION `I hope you get to go there soon`': 'end'
            }
        }
    }

    macros = {
        'GET_LOCATION': MacroNLG(get_location),
        'SET_LOCATION': MacroGPTJSON(
            'What place does the speaker mention?',
            {V.location.name: ["Austria", "Europe", "Chicago"]}),
        'GET_FAVORITE': MacroNLG(get_favorite_thing),
        'SET_FAVORITE': MacroGPTJSON(
            'What does the speaker like about the place they mentioned?',
            {V.favoriteThing.name: ["great weather", "good food", "feels like home"]}),
        'GET_ACTIVITY': MacroNLG(get_activity),
        'SET_ACTIVITY': MacroGPTJSON(
            'What did the speaker do (in present tense)?',
            {V.favoriteThing.name: ["go to museum", "eat good food", "go swimming"]})
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(barcelona)
    df.load_transitions(other_location)
    df.add_macros(macros)
    return df


def get_location(vars: Dict[str, Any]):
    ls = vars[V.location.name]
    return ls[random.randrange(len(ls))]


def get_favorite_thing(vars: Dict[str, Any]):
    ls = vars[V.favoriteThing.name]
    return ls[random.randrange(len(ls))]


def get_activity(vars: Dict[str, Any]):
    ls = vars[V.activity.name]
    return ls[random.randrange(len(ls))]


if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    main().run()
