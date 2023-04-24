import random
from enum import Enum
from typing import Dict, Any
import openai
from src import utils
from src.utils import MacroGPTJSON, MacroNLG
from emora_stdm import DialogueFlow, Macro, Ngrams, List
from src.transitions.evaluation import audio


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


transitions_travel = {
    'state': 'travel',
    '#WHEREF #USERINPUT': {
        '#SET_LOCATION': {
            '#GET_LOCATION #USERINPUT #SET_USER_OPINION': {
                '#GET_USER_OPINION': {
                    '#FAV_PART #USERINPUT': {
                        '#SET_FAVORITE': {
                            '#GET_FAVORITE': 'travel_question'
                        },
                        'error': {
                            '#GOOGLE': 'other_location'
                        }
                    }

                },
                'error': {
                    '#SUCKS #USERINPUT': {
                        '#RB': {
                            '#RATHER_LIVE #USERINPUT #SET_LOCATION': {
                                '#GET_LOCATION2': 'travel_question'
                            },
                            'error': {
                                '#OYSTER': 'travel_question'
                            }
                        },
                        'error': {
                            '#SOUND': 'movie'
                        }
                    }
                }
            }
        },
        'error': {
            '#OK': 'other_location'
        }
    },
    'error': {
        '#OK': 'other_location'
    }
}

travel_question = {
    'state': 'travel_question',
    '#HAVE_YOU #USERINPUT #SET_USER_VISITED': {
        '#GET_USER_VISITED': {
            '#WHAT_ACT #USERINPUT': {
                '#SET_ACTIVITY': {
                    '#GET_ACTIVITY': 'other_location'
                },
                'error': {
                    '#ISEE': 'other_location'
                }
            }
        },
        'error': {
            '#MENEITHER': 'other_location'
        }
    },
    'error': {
        '#OK': 'other_location'
    }
}

travel_other_location = {
    'state': 'other_location',
    '#OTHER_PLACE #USERINPUT': {
        '#SET_LOCATION': {
            '#GET_LOCATION3 #USERINPUT #SET_USER_FAMILY': {
                '#GET_USER_FAMILY': {
                    '#SOLO #USERINPUT #SET_USER_SOLO': {
                        '#GET_USER_SOLO': {
                            '#SOLOP #USERINPUT': 'feedback'  #transition into evalutaion!
                        },
                        'error': {
                            '#SOLON #USERINPUT': 'feedback'  # transition into evaluation!
                        }
                    },
                    'error': {
                        '#THANKCHAT': 'feedback'  # transition into evaluation!
                    }
                },
                'error': {
                    '#FRI #USERINPUT #SET_USER_FRIENDS': {
                        '#GET_USER_FRIENDS': {
                            '#FRIP #USERINPUT': 'feedback'
                        },
                        'error': {
                            '#FRIN #USERINPUT': 'feedback'  # transition into evaluation!
                        }
                    }
                }
            },
            'error': {
                '#THANKCHAT': 'feedback'  # transition into evaluation!
            }
        },
        'error': {
            '#THANKCHAT': 'feedback'  # transition into evaluation!
        }
    },
    'error': {
        '#THANKCHAT': 'feedback'  # transition into evaluation!
    }
}

    # df = DialogueFlow('start', end_state='end')
    # df.load_transitions(transitions_travel)
    # df.load_transitions(travel_question)
    # df.load_transitions(travel_other_location)
    # df.add_macros(macros)
    # return df


class MacroWhereF(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "So, Where are you from? "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macroget_location(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        ls = vars[V.location.name]
        ls = ls[random.randrange(len(ls))]
        output = "That\'s awesome! I\'m from Austria. I\'ve never been to " + ls + " though, is it nice? "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroFavPart(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "I\'m glad! Maybe I should plan a visit. What\'s your favorite part about it? "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroGetFavThing(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        ls = vars[V.favoriteThing.name]
        ls = ls[random.randrange(len(ls))]
        output = "That makes sense. " + ls + " is really important. That is why I want to live in Barcelona. "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroGoogle(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ah, okay. I guess I\'ll ask google... "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroSucks(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ah that sucks."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroRB(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        #return random.choice([True, False])
        return False


class MacroRatherLive(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Where would you rather live? "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroSound(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "I really like Austria, it\'s where the sound of music was filmed. "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macroget_location2(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        ls = vars[V.location.name]
        ls = ls[random.randrange(len(ls))]
        output = "That is so cool! I have always wanted to visit " + ls + ". "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroHaveYou(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Have you ever been there? "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroOyster(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Hey, the world is your oyster! I want to live in Barcelona. "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroWhatAct(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Wow! I\'m so jealous. What did you do there?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macroget_activity(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        ls = vars[V.activity.name]
        ls = ls[random.randrange(len(ls))]
        if ls == 'none':
            output = "I see. Sounds fun!"
        else:
            output = "No way, I have always wanted to " + ls + ". It\'s on my bucket list! "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroISEE(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "I see. Sounds fun!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroMeNeither(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Me neither! Hopefully we can both visit someday. "
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroOtherPlace(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = " Are there any other places you would like to live in or visit?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroGET_LOCATION3(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        ls = vars[V.location.name]
        ls = ls[random.randrange(len(ls))]
        output = "I love " + ls + ", I went there with my family once. Do you usually travel with your family?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroSolo(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "That\'s great! Traveling with family is lovely, but I have always wanted to solo travel. Would you " \
                 "ever do something like that?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroSoloP(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "It would be so fun! You would really get to know yourself better"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output

class MacroSoloN(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "That makes sense, it would be scary."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroThankC(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Okay. Thanks for chatting!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroFRI(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ah I see. Do you travel with friends?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroFRIP(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Same! Traveling with friends is my favorite. It was nice chatting with you!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroFRIN(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "That makes sense! Thanks for chatting."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


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


# macros = {
#     'GET_LOCATION': MacroNLG(get_location),
#     'SET_LOCATION': MacroGPTJSON(
#         'What place does the speaker mention?',
#         {V.location.name: ["Austria", "Europe", "Chicago"]}),
#
#     'GET_FAVORITE': MacroNLG(get_favorite_thing),
#     'SET_FAVORITE': MacroGPTJSON(
#         'What does the speaker like about the place they mentioned?',
#         {V.favoriteThing.name: ["great weather", "good food", "feels like home"]}),
#
#     'GET_ACTIVITY': MacroNLG(get_activity),
#     'SET_ACTIVITY': MacroGPTJSON(
#         'What did the speaker do (in present tense)?',
#         {V.favoriteThing.name: ["go to the museum", "eat good food", "go swimming"]}),
#
#     'GET_USER_OPINION': MacroNLG(get_user_opinion),
#     'SET_USER_OPINION': MacroGPTJSON(
#         'Is the speaker\'s answer likely to be "yes"?',
#         {V.user_opinion.name: True},
#         {V.user_opinion.name: False}),
#
#     'GET_USER_VISITED': MacroNLG(get_user_visited),
#     'SET_USER_VISITED': MacroGPTJSON(
#         'Is the speaker\'s answer likely to be "yes"?',
#         {V.user_visited.name: True},
#         {V.user_visited.name: False}),
#
#     'GET_USER_FAMILY': MacroNLG(get_user_family),
#     'SET_USER_FAMILY': MacroGPTJSON(
#         'Is the speaker\'s answer likely to be "yes"?',
#         {V.user_family.name: True},
#         {V.user_family.name: False}),
#
#     'GET_USER_SOLO': MacroNLG(get_user_solo),
#     'SET_USER_SOLO': MacroGPTJSON(
#         'The speaker was asked whether they have solo traveled. Is the speaker\'s answer likely to be "yes"?',
#         {V.user_solo.name: True},
#         {V.user_solo.name: False}),
#
#     'GET_USER_FRIENDS': MacroNLG(get_user_friends),
#     'SET_USER_FRIENDS': MacroGPTJSON(
#         'Is the speaker\'s answer likely to be "yes"? They were just asked whether they travel with friends',
#         {V.user_friends.name: True},
#         {V.user_friends.name: False})
# }

if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    #main().run()
