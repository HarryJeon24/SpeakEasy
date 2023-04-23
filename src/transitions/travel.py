import random
from enum import Enum
from typing import Dict, Any
import openai
from emora_stdm import DialogueFlow
from src import utils
from src.utils import MacroGPTJSON, MacroNLG


class V(Enum):
    location = 0
    favoriteThing = 1
    activity = 2
    healthy = 3
    user_opinion = 4
    user_visited = 5
    user_family = 6
    user_solo = 7
    user_friends = 8


def main() -> DialogueFlow:
    transitions_travel = {
        'state': 'start',
        '`Where are you from?`': {
            '#SET_LOCATION': {
                '`That\'s awesome! I\'m from Austria. I\'ve never been to` #GET_LOCATION `though, is it nice?`': {
                    '#SET_USER_OPINION': {
                        '#IF(#GET_USER_OPINION) `I\'m glad! Maybe I should plan a visit. What\'s your favorite part about it?`': {
                            '#SET_FAVORITE': {
                                '`That makes sense.` #GET_FAVORITE `is really important. That is why I want to live '
                                'in Barcelona.`': 'travel_question'
                            },
                            'error': {
                                '`Ah, okay. I guess I\'ll ask google...`': 'other_location'
                            }
                        },
                        '`That\'s unfortunate. I really like Austria, it\'s where the sound of music was filmed`': {
                            'score': 0.1,
                            'state': 'entertainment'    #Transition to entertainment?? or get fully rid of this option
                        },
                        '`Ah that sucks. Where would you rather live?`': {
                            'score': 0.1,
                            '#SET_LOCATION': {
                                '`That is so cool! I have always wanted to visit` #GET_LOCATION`.`': 'travel_question'
                            },
                            'error': {
                                '`Hey, the world is your oyster! I want to live in Barcelona.`': 'travel_question'
                            }
                        }
                    },
                    'error': {
                        '`Nice, thanks for sharing.`': 'other_location'
                    }
                }
            },
            'error': {
                '`Okay.`': 'other_location'
            }
        },
        'error': {
            '`Okay. Thanks for chatting!`': 'other_location'
        }
    }

    travel_question = {
        'state': 'travel_question',
        '`Have you ever been?`': {
            '#SET_USER_VISITED': {
                '#IF(#GET_USER_VISITED):`Wow! I\'m so jealous. What did you do there?`': {
                    '#SET_ACTIVITY': {
                        '`No way, I have always wanted to ` #GET_ACTIVITY `. It\'s on my bucket list!`': 'other_location'
                    },
                    'error': {
                        '`I see. Sounds fun!`': 'other_location'
                    }
                }
            },
            '`Me neither! Hopefully we can both visit someday.`': {
                'score': 0.1,
                'state': 'other_location'
            },
            'error': 'other_location'
        },
        'error': {
            '`I see.`': 'other_location'
        }
    }

    travel_other_location = {
        'state': 'other_location',
        '`Are there any other places you would like to live in or visit?`': {
            '#SET_LOCATION': {
                '`I love` #GET_LOCATION `, I went there with my family once. Do you usually travel with your family?`': {
                    '#SET_USER_FAMILY': {
                        '#IF(#GET_USER_FAMILY) `That\'s great! Traveling with family is lovely, but I have always '
                        'wanted to solo travel. Would you ever do something like that?`': {
                            '#SET_USER_SOLO': {
                                '#IF(GET_USER_SOLO) `It would be so fun! You would really get to know yourself better`': 'end'  #transition into evalutaion!
                            },
                            '`That makes sense, it would be scary.`': 'end', #transition into evaluation!
                            'error': {
                                '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
                            }
                        },
                        '`Ah I see. Do you travel with friends?`': {
                            '#SET_USER_FRIENDS': {
                                '#IF(#GET_USER_FRIENDS) `Same! Traveling with friends is my favorite. It was nice chatting!`': 'end',  #transition into evaluation!
                                '`That makes sense! Thanks for chatting.`': 'end', #transition into evaluation!
                                'error': {
                                    '`Okay. Thanks for chatting!`': 'end'   #transition into evaluation!
                                }
                            }
                        },
                        'error': {
                            '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
                        }
                    },
                    'error': {
                        '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
                    }
                },
                'error': {
                    '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
                }
            },
            'error': {
                '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
            }
        },
        'error': {
            '`Okay. Thanks for chatting!`': 'end'  # transition into evaluation!
        }
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions_travel)
    df.load_transitions(travel_question)
    df.load_transitions(travel_other_location)
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


def get_user_opinion(vars: Dict[str, Any]):
    return vars[V.user_opinion.name]


def get_user_visited(vars: Dict[str, Any]):
    return vars[V.user_visited.name]

def get_user_family(vars: Dict[str, Any]):
    return vars[V.user_family.name]


def get_user_solo(vars: Dict[str, Any]):
    return vars[V.user_solo.name]


def get_user_friends(vars: Dict[str, Any]):
    return vars[V.user_friends.name]


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
        {V.favoriteThing.name: ["go to the museum", "eat good food", "go swimming"]}),

    'GET_USER_OPINION': MacroNLG(get_user_opinion),
    'SET_USER_OPINION': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {V.user_opinion.name: True},
        {V.user_opinion.name: False}),

    'GET_USER_VISITED': MacroNLG(get_user_visited),
    'SET_USER_VISITED': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {V.user_visited.name: True},
        {V.user_visited.name: False}),

    'GET_USER_FAMILY': MacroNLG(get_user_family),
    'SET_USER_FAMILY': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {V.user_family.name: True},
        {V.user_family.name: False}),

    'GET_USER_SOLO': MacroNLG(get_user_solo),
    'SET_USER_SOLO': MacroGPTJSON(
        'The speaker was asked whether they have solo traveled. Is the speaker\'s answer likely to be "yes"?',
        {V.user_solo.name: True},
        {V.user_solo.name: False}),

    'GET_USER_FRIENDS': MacroNLG(get_user_friends),
    'SET_USER_FRIENDS': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"? They were just asked whether they travel with friends',
        {V.user_friends.name: True},
        {V.user_friends.name: False})
}

if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    main().run()
