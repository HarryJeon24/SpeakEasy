from enum import Enum
from typing import Dict, Any

import openai
from emora_stdm import DialogueFlow

from src import utils
from src.utils import MacroGPTJSON, MacroNLG


class V(Enum):
    user_opinion = 0  # bool
    user_strln = 1  # bool
    user_strln_str = 2  # str
    user_comm = 3  # bool
    user_comm_str = 4  # str
    user_actor = 5  # bool
    user_actor_str = 6  # str
    user_message = 7  # bool
    user_message_str = 8  # str
    user_reason = 9  # bool
    user_reason_str = 10  # str
    user_interest = 11  # bool


def main() -> DialogueFlow:
    transitions = {
        'state': 'start',
        '`What do you think of the movie?`': {
            '#SET_USER_OPINION': {
                '#IF(#GET_USER_OPINION) `I also like the movie! In your opinion, which storyline in "Babel" was the '
                'most impactful? Personally, I found the storyline in Morocco to be particularly powerful.`': {
                    'state': 'strln',
                    '#SET_USER_STRLN': {
                        '#IF(#GET_USER_STRLN) `You are right. The` #GET_USER_STRLN_STR `storyline is really '
                        'interesting. What did you think of the way the movie explored cultural differences and '
                        'communication?`': {
                            'state': 'comm',
                            '#SET_USER_COMM': {
                                '#IF(#GET_USER_COMM) `So you are saying that` #GET_USER_COMM_STR ` Interesting '
                                'thought! What did you think of the performances in the movie? Who is your favorite '
                                'actor?`': {
                                    'state': 'actor',
                                    '#SET_USER_ACTOR': {
                                        '#IF(#GET_USER_ACTOR) `Yes!` #GET_USER_ACTOR_STR `is the best! What message '
                                        'about human connection do you think the filmmakers were trying to convey in '
                                        'the movie?`': {
                                            'state': 'message',
                                            '#SET_USER_MESSAGE': {
                                                '#IF(#GET_USER_MESSAGE) `Good point! Personally, I think it '
                                                'emphasized our shared humanity.`': 'outro',
                                                '`Ok! Personally, I think it emphasized our shared humanity.`': {
                                                    'state': 'outro',
                                                    'score': 0.1
                                                }
                                            }
                                        },
                                        '`That is fine also. What message about human connection do you think the '
                                        'filmmakers were trying to convey in the movie?`': {
                                            'state': 'message',
                                            'score': 0.1
                                        }
                                    }
                                },
                                '`Ok! What did you think of the performances in the movie? Who is your favorite actor?`': {
                                    'state': 'actor',
                                    'score': 0.1
                                }
                            }
                        },
                        '`Ok! What did you think of the way the movie explored cultural differences and '
                        'communication?`': {
                            'state': 'comm',
                            'score': 0.1
                        }
                    }
                },
                '`I do not like the movie either! What is the reason for your opinion?`': {
                    '#SET_USER_REASON': {
                        '#IF(#GET_USER_REASON) `Ok, so the reason is` #GET_USER_REASON_STR `Would you like to '
                        'continue talking about the movie?`': {
                            'state': 'interest',
                            '#SET_USER_INTEREST': {
                                '#IF(#GET_USER_INTEREST) `Amazing! In your opinion, which storyline in "Babel" was '
                                'the most impactful?`': 'strln',
                                '`Ok!`': 'outro'
                            }
                        },
                        '`Ok, thank you for sharing! Would you like to continue talking about the movie?`': {
                            'state': 'interest',
                            'score': 0.1
                        }
                    }
                }
            }
        }
    }

    transitions_outro = {
        'state': 'outro',
        '`Thank you so much for talking with me today!`': 'end'     #transition into entertainment? For example: Would you like other movie recommendations -> movie_red
    }

    macros = {
        'GET_USER_OPINION': MacroNLG(get_user_opinion),
        'SET_USER_OPINION': MacroGPTJSON(
            'Does the user like the movie?',
            {V.user_opinion.name: True},
            {V.user_opinion.name: False}),
        'GET_USER_STRLN': MacroNLG(get_user_strln),
        'GET_USER_STRLN_STR': MacroNLG(get_user_strln_str),
        'SET_USER_STRLN': MacroGPTJSON(
            'Does the speaker have a preferred storyline from the movie "Babel"? The options are "Morocco", '
            '"Richard/Susan", "United States/Mexico", and "Japan". Otherwise, choose "N/A".',
            {V.user_strln.name: True, V.user_strln_str.name: "Japan"},
            {V.user_strln.name: False, V.user_strln_str.name: "N/A"}),
        'GET_USER_COMM': MacroNLG(get_user_comm),
        'GET_USER_COMM_STR': MacroNLG(get_user_comm_str),
        'SET_USER_COMM': MacroGPTJSON(
            'What does the speaker think of the way the movie "Babel" explores cultural differences and '
            'communication? Complete the sentence: "The speaker is saying that...".',
            {V.user_comm.name: True, V.user_comm_str.name: "the movie did a good job."},
            {V.user_comm.name: False, V.user_comm_str.name: "N/A"}),
        'GET_USER_ACTOR': MacroNLG(get_user_actor),
        'GET_USER_ACTOR_STR': MacroNLG(get_user_actor_str),
        'SET_USER_ACTOR': MacroGPTJSON(
            'Who is the speaker\'s favorite actor or actress?',
            {V.user_comm.name: True, V.user_comm_str.name: "Brad Pitt"},
            {V.user_comm.name: False, V.user_comm_str.name: "N/A"}),
        'GET_USER_MESSAGE': MacroNLG(get_user_message),
        'GET_USER_MESSAGE_STR': MacroNLG(get_user_message_str),
        'SET_USER_MESSAGE': MacroGPTJSON(
            'Summarize the speaker\'s opinion on this questions: "What message about human connection do you think '
            'the filmmakers were trying to convey in "Babel"?"',
            {V.user_message.name: True, V.user_message_str.name: "I think it emphasized our shared humanity."},
            {V.user_message.name: False, V.user_message_str.name: "N/A"}),
        'GET_USER_REASON': MacroNLG(get_user_reason),
        'GET_USER_REASON_STR': MacroNLG(get_user_reason_str),
        'SET_USER_REASON': MacroGPTJSON(
            'Why does the speaker not like the movie? The options are "storyline", "casting", '
            '"direction", "visuals", and "soundtrack".',
            {V.user_reason.name: True, V.user_reason_str.name: "because the storyline is bad."},
            {V.user_reason.name: False, V.user_reason_str.name: "N/A"}),
        'GET_USER_INTEREST': MacroNLG(get_user_interest),
        'SET_USER_INTEREST': MacroGPTJSON(
            'Is the speaker\'s answer likely to be "yes"?',
            {V.user_interest.name: True},
            {V.user_interest.name: False})
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(transitions_outro)
    df.add_macros(macros)
    return df


def get_user_opinion(vars: Dict[str, Any]):
    return vars[V.user_opinion.name]


def get_user_strln(vars: Dict[str, Any]):
    return vars[V.user_strln.name]


def get_user_strln_str(vars: Dict[str, Any]):
    return vars[V.user_strln_str.name]


def get_user_comm(vars: Dict[str, Any]):
    return vars[V.user_comm.name]


def get_user_comm_str(vars: Dict[str, Any]):
    return vars[V.user_comm_str.name]


def get_user_actor(vars: Dict[str, Any]):
    return vars[V.user_actor.name]


def get_user_actor_str(vars: Dict[str, Any]):
    return vars[V.user_actor_str.name]


def get_user_message(vars: Dict[str, Any]):
    return vars[V.user_message.name]


def get_user_message_str(vars: Dict[str, Any]):
    return vars[V.user_message_str.name]


def get_user_reason(vars: Dict[str, Any]):
    return vars[V.user_reason.name]


def get_user_reason_str(vars: Dict[str, Any]):
    return vars[V.user_reason_str.name]


def get_user_interest(vars: Dict[str, Any]):
    return vars[V.user_interest.name]


if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    main().run()
