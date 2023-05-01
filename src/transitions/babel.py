from enum import Enum
from typing import Dict, Any
import openai
from emora_stdm import DialogueFlow, Macro, Ngrams, List
from src import utils
from src.utils import MacroGPTJSON, MacroNLG
from src.transitions.evaluation import audio


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


transitions_babel = {
    'state': 'babel',
    '#THINK_MOVIE #USERINPUT #SET_USER_OPINION': {
        '#GET_USER_OPINION': {
            '#LIKE_MOVIE #USERINPUT': {
                'state': 'strln',
                '#SET_USER_STRLN': {
                    '#GET_USER_STRLN': {
                        '#CULTURAL #USERINPUT #SET_USER_COMM': {
                            'state': 'comm',
                            '#GET_USER_COMM': 'outro',
                                # '#ACTOR #USERINPUT #SET_USER_ACTOR': {
                                #     'state': 'actor',
                                #     '#GET_USER_ACTOR': {
                                #         '#FILMMAKERS #USERINPUT #SET_USER_MESSAGE': {
                                #             'state': 'message',
                                #             '#GET_USER_MESSAGE': {'#HUMANITY': 'outro'},
                                #             'error': {'#PERSONALLY': 'outro'}
                                #         },
                                #         'error': {
                                #             '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that'
                                #             '." #GTTS': 'end'
                                #         }
                                #     },
                                #     'error': {
                                #         '#ALSO #USERINPUT #SET_USER_MESSAGE': 'message',
                                #         'error': {
                                #             '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that'
                                #             '." #GTTS': 'end'
                                #         }
                                #     }
                                # },
                                # 'error': {'#USERINPUT #SET_USER_ACTOR': 'actor'}
                            'error': {
                                '#PERFORMANCES #USERINPUT #SET_USER_ACTOR': 'actor',
                            },
                        },
                        'error': {'#ASKAGAIN #USERINPUT #SET_USER_COMM': 'comm'}
                    },
                    'error': {
                        '#COMMUNICATION #USERINPUT #SET_USER_COMM': 'comm',
                    },
                },
                'error': {
                    '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
                }
            },
            'error': {
                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
            }
        },
        'error': {
            '#OPINION #USERINPUT #SET_USER_REASON': {
                '#GET_USER_REASON': {
                    '#CONTINUE #USERINPUT #SET_USER_INTEREST': {
                        'state': 'interest',
                        '#GET_USER_INTEREST': {
                            '#AMAZING #USERINPUT': 'strln'
                        },
                        'error': {'#OK': 'outro'}
                    },
                    'error': {
                        '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
                    }
                },
                'error': {
                    '#SHARING #USERINPUT #SET_USER_INTEREST': 'interest'
                }
            },
            'error': {
                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
            }
        },
    },
    'error': {
        '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
    }
}

transitions_outro = {
    'state': 'outro',
    '#THANKYOU': 'music',
    'error': {
        '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
    }
}


def main() -> DialogueFlow:
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
            {V.user_actor.name: True, V.user_actor_str.name: "Brad Pitt"},
            {V.user_actor.name: False, V.user_actor_str.name: "N/A"}),
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
            {V.user_interest.name: False}),

        # Text Macros
        'THINK_MOVIE': MacroThinkMovie(),
        'LIKE_MOVIE': MacroLikeMovie(),
        'CULTURAL': MacroCultural(),
        'ACTOR': MacroActor(),
        'FILMMAKERS': MacroFilmmakers(),
        'HUMANITY': MacroHumanity(),
        'PERSONALLY': MacroPersonally(),
        'ALSO': MacroAlso(),
        'PERFORMANCES': MacroPerformances(),
        'COMMUNICATION': MacroCommunication(),
        'OPINION': MacroOpinion(),
        'CONTINUE': MacroContinue(),
        'AMAZING': MacroAmazing(),
        'SHARING': MacroSharing(),
        'THANKYOU': MacroThankYou()
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions_outro)
    df.add_macros(macros)
    return df


class MacroAskAgain(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Thank you so much for talking about babel with me!'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroThankYou(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Thank you so much for talking about babel with me!'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroSharing(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Ok, thank you for sharing! Would you like to continue talking about the movie?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroAmazing(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Amazing! In your opinion, which storyline in "Babel" was the most impactful?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroContinue(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Ok, so the reason is {get_user_reason_str(vars)} Would you like to continue talking about the' \
                 f' movie?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroOpinion(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'I do not like the movie either! What is the reason for your opinion?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroCommunication(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Ok! What did you think of the way the movie explored cultural differences and communication?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroPerformances(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Ok! What did you think of the performances in the movie? Who is your favorite actor?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroAlso(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'That is fine also. What message about human connection do you think the filmmakers were trying to ' \
                 f'convey in the movie?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroPersonally(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Ok! Personally, I think it emphasized our shared humanity.'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroHumanity(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Good point! Personally, I think it emphasized our shared humanity.'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroFilmmakers(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'Yes! {get_user_actor_str(vars)} is the best! What message about human connection do you think' \
                 f' the filmmakers were trying to convey in the movie?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output

class MacroActor(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'So you are saying that {get_user_comm_str(vars)} Interesting thought! What did you think' \
                 f' of the performances in the movie? Who is your favorite actor?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroCultural(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = f'You are right. The {get_user_strln_str(vars)} storyline is really interesting. What did you ' \
                 f'think of the way the movie explored cultural differences and communication?'
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroLikeMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "I also like the movie! In your opinion, which storyline in \"Babel\" was the most impactful? " \
                 "Personally, I found the storyline in Morocco to be particularly powerful."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroThinkMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "I heard I was going to be talking to an I D S student today. What do you think of the movie Babel. " \
                 "I know you watched that recently?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


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
    # main().run()
