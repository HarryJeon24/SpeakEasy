import json
import os.path
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
from src.utils import MacroGPTJSON, MacroNLG
import pyaudio
import wave
from gtts import gTTS
import threading
from mutagen.mp3 import MP3
from src.transitions.evaluation import transitions_feedback, transitions_evaluation
import src.transitions.evaluation as evaluation


class V(Enum):
    person_name = 0  # str
    person_feeling = 1  # str
    implemented_advice = 2  # str
    activity = 3  # str
    category = 4  # str


def visits() -> DialogueFlow:
    transitions = {
        'state': 'start',
        '#TIME #INTRODUCE #ASK_NAME #USERINPUT #SET_NAME': {
            '#GET_NAME1': {
                '`Welcome back,` $NAME `! How have you been?` #RETURN #USERINPUT': {
                    '#SET_FEELING': {
                        '#GET_FEELING $RESPONSE="Did you get a chance to work on those speaking tips I gave you last '
                        'time?" #GTTS #USERINPUT': {
                            '#SET_LISTENED': {
                                '#GET_LISTENED #USERINPUT': {
                                    '#SET_RATING': {
                                        '$RESPONSE="Thanks for evaluating my feedback! Now, I\'d love to hear more '
                                        'about you. What have you been up to recently?" #GTTS #USERINPUT': {
                                            '#SET_TOPIC': {
                                                '#GET_TOPIC #USERINPUT': {
                                                    'error': {
                                                        '`I spend a lot of time` $TOPIC`too. Is it part of your daily '
                                                        'schedule?` #ROUTINE #USERINPUT': {
                                                            'error': 'health'
                                                        }
                                                    }
                                                },
                                                'error': {
                                                    '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch '
                                                    'that." #GTTS': 'end'
                                                }
                                            },
                                            'error': {
                                                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch '
                                                'that." #GTTS': 'end'
                                            }
                                        },
                                        'error': {
                                            '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                            '#GTTS': 'end'
                                        }

                                    },
                                    'error': {
                                        '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                        '#GTTS': 'end'
                                    }
                                },
                                'error': {
                                    '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                    '#GTTS': 'end'
                                }
                            },
                            'error': {
                                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                '#GTTS': 'end'
                            }
                        }
                    },
                },
                'error': {
                    '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
                }
            },
            '#GET_NAME2': {
                # new user
                '#FIRST_TIME #USERINPUT': {
                    '#SET_FEELING': {
                        '#GET_FEELING #UPTO #USERINPUT': {
                            '#SET_TOPIC': {
                                '#GET_TOPIC #USERINPUT': {
                                    'error': {
                                        '#ROUTINE #USERINPUT': {
                                            'error': 'feedback'
                                        },
                                        'error': {
                                            '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                            '#GTTS': 'end'
                                        }
                                    }
                                },
                                'error': {
                                    '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." '
                                    '#GTTS': 'end'
                                }
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
                        '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
                    }
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
            '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
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
    df.load_transitions(transitions_feedback)
    df.load_transitions(transitions_evaluation)
    df.load_transitions(travel_transitions)
    df.add_macros(macros)
    return df


def audio(text: str):
    tts = gTTS(text=text, lang='en')
    tts.save("bot_output.mp3")
    os.system("start bot_output.mp3")
    time.sleep(MP3("bot_output.mp3").info.length)


# Macro's for audios
class MacrogTTS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'BOTLOG' not in vars:
            vars['BOTLOG'] = vars['RESPONSE']
        vars['BOTLOG'] = vars['BOTLOG'] + vars['RESPONSE']
        audio(vars['RESPONSE'])
        return vars['RESPONSE']


class MacroRecordAudio(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        # Define audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024

        # Specify the directory to save the file
        SAVE_DIR = "/src"
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        # Specify the full path to the WAV file
        WAVE_OUTPUT_FILENAME = os.path.join(SAVE_DIR, "USERINPUT.wav")

        # Create PyAudio object
        audio = pyaudio.PyAudio()

        # Start audio stream
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print("Recording... Press Enter to stop")

        # Record start time
        start_time = time.time()

        # Record audio data
        frames = []
        stop_recording = threading.Event()

        def read_audio_data():
            while not stop_recording.is_set():
                data = stream.read(CHUNK)
                frames.append(data)

        # Start recording thread
        recording_thread = threading.Thread(target=read_audio_data)
        recording_thread.start()

        # Wait for user input to stop the recording
        input()

        # Set event to stop the recording thread
        stop_recording.set()
        recording_thread.join()
        # Record end time
        end_time = time.time()
        print("Finished recording.")

        # Calculate duration
        duration = end_time - start_time

        # Stop audio stream
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio data to WAV file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        openai.api_key_path = 'C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt'
        audio_file = open("/src/USERINPUT.wav", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        vars['USERINPUT'] = text
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = text.lower()
            vars['SPOKENTIME'] = duration
            vars['UTTERANCE'] = 1
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + text.lower()
            vars['SPOKENTIME'] = vars['SPOKENTIME'] + duration
            if 'UTTERANCE' not in vars:
                vars['UTTERANCE'] = 1
            vars['UTTERANCE'] = vars['UTTERANCE'] + 1
        print("Your Input: ", vars['USERINPUT'])

        return True


class MacroFirstTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        audio("Hi," + vars["NAME"] + ". Nice to meet you. How are you doing?")
        return True


class MacroRoutine(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        options = ("I also spend a good amount of time" + vars["TOPIC"] + ". Is it part of your everyday routine?",
                   "I spend alot of time" + vars["TOPIC"] + "too. Is it part of your daily schedule?")

        audio(random.choice(options))

        return True


class MacroReturn(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        audio("Welcome back," + vars["NAME"] + "! How have you been?")
        return True


class MacroTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        hour = time.strftime("%H")

        if int(hour) < 12:
            vars["TIME"] = "Good morning!"
        if 12 < int(hour) < 17:
            vars["TIME"] = "Good afternoon!"
        else:
            vars["TIME"] = "Good evening!"

        audio(vars["TIME"])

        return vars["TIME"]


class MacroIntroduction(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        # intro = f'My name is SpeakEasy. I am a chatbot designed to help you improve your conversations. ' \
        #         f'We are going to engage in a few minutes long conversation and I will provide some ' \
        #         f'feedback on your conversational skills. Whenever the screen displays ' \
        #         f'"Recording... Press Enter to stop" please begin speaking and press Enter when you are ' \
        #         f'finished. When you see "U:" press enter once again. Before we get started, '
        intro = "dad"
        audio(intro)


class MacroAskName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        options = (
            "What's your name?", "What can I call you?", "Can I have your name?", "What do you call yourself?")
        vars["ASK_NAME"] = random.choice(options)

        audio(vars["ASK_NAME"])

        return vars["ASK_NAME"]


class MacroGetName1(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        name = vars[V.person_name.name]
        vars['NAME'] = name

        usersDict = {}
        if 'USERS' not in vars:
            vars['USERS'] = usersDict

        if name in vars['USERS']:
            vars['NEW_USER'] = False
            return True

        return False


class MacroGetName2(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        name = vars[V.person_name.name]
        vars['NAME'] = name

        usersDict = {}
        if 'USERS' not in vars:
            vars['USERS'] = usersDict

        if name in vars['USERS']:
            return False
        else:
            vars['USERS'][name] = []
            vars['NEW_USER'] = True
            return True


def get_feeling(vars: Dict[str, Any]):
    feeling = vars[V.person_feeling.name]
    if feeling == "good":
        vars["FEELING"] = "I'm happy to hear you are doing well! I'm not so bad myself. "
    elif feeling == "bad":
        vars["FEELING"] = "I'm sorry to hear that:( I hope things get better soon."
    else:
        vars["FEELING"] = "Glad to hear you are doing okay. I'm doing alright too."

    audio(vars["FEELING"])

    return vars["FEELING"]


class MacroWhatHaveYouBeenUpTo(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        output = "What have you been up to?"
        add_to_log(vars, output)
        audio(output)


def add_to_log(vars: Dict[str, Any], output: str):
    if 'BOTLOG' not in vars:
        vars['BOTLOG'] = output
    vars['BOTLOG'] = vars['BOTLOG'] + output


def get_listened(vars: Dict[str, Any]):
    listened = vars[V.implemented_advice.name]
    if listened == "yes":
        a = "I'm glad you were able to practice my tips. How helpful would you say the advice was on a scale of 1 to " \
            "5 (with 5 being very helpful)?"
    elif listened == "no":
        a = "Hopefully you get a chance to practice them going forwards. How helpful do you think my advice was on a" \
            " scale of 1 to 5 (with 5 being very helpful)?"
    else:
        a = "Gotcha. How helpful do you think my advice was on a scale of 1 to 5 (with 5 being very helpful)?"

    audio(a)

    return a


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


def get_topic(vars: Dict[str, Any]):
    topic = vars[V.activity.name]
    vars['TOPIC'] = topic
    a = topic + " is excellent. It's nice to keep yourself busy while doing what you enjoy."

    audio(a)

    return a


macros = {
    # Audio
    "GTTS": MacrogTTS(),
    "USERINPUT": MacroRecordAudio(),
    "FIRST_TIME": MacroFirstTime(),
    "ROUTINE": MacroRoutine(),
    "RETURN": MacroReturn(),

    'TIME': MacroTime(),
    'INTRODUCE': MacroIntroduction(),
    'ASK_NAME': MacroAskName(),
    'GET_NAME1': MacroGetName1(),
    'GET_NAME2': MacroGetName2(),
    'SET_NAME': MacroGPTJSON(
        'How does the speaker want to be called?',
        {V.person_name.name: "Mike Johnson"},
        {V.person_name.name: ""}
    ),
    'SET_FEELING': MacroGPTJSON(
        'Is the speaker doing good, bad, or okay?',
        {V.person_feeling.name: "good"},
        {V.person_feeling.name: "bad"}
    ),
    'GET_FEELING': MacroNLG(get_feeling),
    'UPTO': MacroWhatHaveYouBeenUpTo(),
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

    'GET_EVAL': MacroNLG(evaluation.get_eval),
    'CONGRATS': evaluation.MacroCongrats(),
    'GPTDETAIL': MacroGPTJSON('Does the user want to know the detail about the feedback? Respond in yes or no.',
                              {evaluation.V.detail.name: "yes"}),
    'GPTEFF': MacroGPTJSON(
        'Considering the user input about the conversation, assign a score: -1 for negative, 0 for neutral, '
        '1 for positive.', {evaluation.V.effectiveness.name: "0"}),
    'GPTSAT': MacroGPTJSON(
        'Considering the user input about the satisfaction of the conversation, assign a score to satisfactiory: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign the score to effectiveness.', {evaluation.V.satisfactory.name: "0"}),
    'GPTCOR': MacroGPTJSON(
        'Considering the user input about the correctness of the conversation, assign a score to correctness: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign score to effectiveness.', {evaluation.V.correctness.name: "0"}),
    'GPTINT': MacroGPTJSON(
        'Considering the user input about the interpretability of the conversation, assign a score to interpretability: -1 for negative, 0 for '
        'neutral, 1 for positive. Do not assign score to effectiveness.', {evaluation.V.interpretability.name: "0"}),
    'GPTCOH': MacroGPTJSON(
        'Considering the user input about the coherence of the conversation, assign a score to coherence: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign score to effectiveness.', {evaluation.V.coherence.name: "0"}),
    "QUEST": evaluation.MacroNumQuestions(),
    "SPEED": evaluation.MacroAVGToken(),
    "TIC": evaluation.MacroTic(),
    "ACKNOW": evaluation.MacroAcknow(),
    "AWKWARD": evaluation.MacroAwkward(),
    "DETAIL": evaluation.MacroDetail()

}


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    # 'C:/Users/Harry/PycharmProjects/SpeakEasy/src'
    # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy/src
    path = f'C:/Users/Harry/PycharmProjects/SpeakEasy/{varfile}'
    if os.path.isfile(path):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
        df.vars()['ANSWERS'] = ""
        df.vars()['UTTERANCE'] = 0
        df.vars()['BOTLOG'] = ""
    df.run()
    save(df, varfile)


if __name__ == '__main__':
    # C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt
    # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/chat_gpt_api_key.txt
    openai.api_key_path = 'C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt'
    load(visits(), 'src/userLog.pkl')