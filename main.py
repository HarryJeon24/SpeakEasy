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
from emora_stdm import DialogueFlow
import src.utils
from src.utils import MacroGPTJSON, MacroNLG
import pyaudio
import wave
from gtts import gTTS
import threading

class V(Enum):
    person_name = 0  # str
    person_feeling = 1  # str
    implemented_advice = 2  # str
    activity = 3  # str
    category = 4  # str


def visits() -> DialogueFlow:
    transitions = {
        'state': 'start',
        '#TIME #ASK_NAME #USERINPUT': {
            '#SET_NAME': {
                # new user
                '#GET_NAME #IF($NEW_USER=True) `Hi,` $NAME `. Nice to meet you. How are you doing?` #FIRST_TIME #USERINPUT': {
                    '#SET_FEELING': {
                        '#GET_FEELING `What have you been up to recently?` $RESPONSE="What have you been up to recently?" #GTTS #USERINPUT': {
                            '#SET_TOPIC': {
                                '#GET_TOPIC #USERINPUT': {
                                    'error': {
                                        '`I also spend a good amount of time` $TOPIC`. Is it part of your everyday routine?` #ROUTINE #USERINPUT': {
                                            'error': 'health'
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                '#GET_NAME #IF($NEW_USER=False)`Welcome back,` $NAME `! How have you been?` #RETURN #USERINPUT': {
                    '#SET_FEELING': {
                        '#GET_FEELING `Did you get a chance to work on those speaking tips I gave you last time?` $RESPONSE="Did you get a chance to work on those speaking tips I gave you last time?" #GTTS #USERINPUT': {
                            '#SET_LISTENED': {
                                '#GET_LISTENED #USERINPUT': {
                                    '#SET_RATING': {
                                        '`Thanks for evaluating my feedback! Now, I\'d love to hear more about you. What have you been up to recently?` $RESPONSE="Thanks for evaluating my feedback! Now, I\'d love to hear more about you. What have you been up to recently?" #GTTS #USERINPUT': {
                                            '#SET_TOPIC': {
                                                '#GET_TOPIC #USERINPUT': {
                                                    'error': {
                                                        '`I spend alot of time` $TOPIC`too. Is it part of your daily schedule?` #ROUTINE #USERINPUT': {
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
                                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
                            }
                        }
                    }

                }
            },
            'error': {
                '`Sorry, I didn\'t catch that.` $RESPONSE="Sorry, I didn\'t catch that." #GTTS': 'end'
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
        vars["FEELING"] = "I'm happy to hear you are doing well! I'm not so bad myself. "
    elif feeling == "bad":
        vars["FEELING"] = "I'm sorry to hear that:( I hope things get better soon."
    else:
        vars["FEELING"] = "Glad to hear you are doing okay. I'm doing alright too."
    tts = gTTS(text=vars["FEELING"], lang='en')
    tts.save("bot_output.mp3")
    os.system("start bot_output.mp3")
    time.sleep(7)
    return vars["FEELING"]


def get_listened(vars: Dict[str, Any]):
    listened = vars[V.implemented_advice.name]
    if listened == "yes":
        a = "I'm glad you were able to practice my tips. How helpful would you say the advice was on a scale of 1 to 5 (with 5 being very helpful)?"
    elif listened == "no":
        a = "Hopefully you get a chance to practice them going forwards. How helpful do you think my advice was on a scale of 1 to 5 (with 5 being very helpful)?"
    else:
        a = "Gotcha. How helpful do you think my advice was on a scale of 1 to 5 (with 5 being very helpful)?"
    tts = gTTS(text=a, lang='en')
    tts.save("bot_output.mp3")
    os.system("start bot_output.mp3")
    time.sleep(15)
    return a


class MacroTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        hour = time.strftime("%H")

        if int(hour) < 12:
            vars["TIME"] = "Good morning!"
        if 12 < int(hour) < 17:
            vars["TIME"] = "Good afternoon!"
        else:
            vars["TIME"] = "Good evening!"
        tts = gTTS(text=vars["TIME"], lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(1)
        return vars["TIME"]


class MacroFirstTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        a = "Hi," + vars["NAME"] + ". Nice to meet you. How are you doing?"
        tts = gTTS(text=a, lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(5)
        return True

class MacroReturn(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        a = "Welcome back," + vars["NAME"] + "! How have you been?"
        tts = gTTS(text=a, lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(5)
        return True

class MacroRoutine(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        options = ("I also spend a good amount of time" + vars["TOPIC"] + ". Is it part of your everyday routine?", "I spend alot of time" + vars["TOPIC"] + "too. Is it part of your daily schedule?")
        a = random.choice(options)
        tts = gTTS(text=a, lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(7)
        return True

class MacroAskName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        options = (
            "What's your name?", "What can I call you?", "Can I have your name?", "What do you call yourself?")
        vars["ASK_NAME"] = random.choice(options)
        tts = gTTS(text=vars["ASK_NAME"], lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(3)
        return vars["ASK_NAME"]

def get_topic(vars: Dict[str, Any]):
    topic = vars[V.activity.name]
    vars['TOPIC'] = topic
    a = topic + " is excellent. It's nice to keep yourself busy while doing what you enjoy."
    tts = gTTS(text=a, lang='en')
    tts.save("bot_output.mp3")
    os.system("start bot_output.mp3")
    time.sleep(7)
    return a


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


# Macro's for audios
class MacrogTTS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tts = gTTS(text= vars['RESPONSE'], lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(10)
        return True

class MacroRecordAudio(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        # Define audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024


        # Specify the directory to save the file
        SAVE_DIR = "C:/Users/Harry/PycharmProjects/SpeakEasy/src"
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
        audio_file = open("C:/Users/Harry/PycharmProjects/SpeakEasy/src/USERINPUT.wav", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        vars['USERINPUT'] = text
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = text.lower()
            vars['SPOKENTIME'] = duration
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + text.lower()
            vars['SPOKENTIME'] = vars['SPOKENTIME'] + duration
        print("Your Input: ", vars['USERINPUT'])

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

    # Audio
    "GTTS": MacrogTTS(),
    "USERINPUT": MacroRecordAudio(),
    "FIRST_TIME": MacroFirstTime(),
    "ROUTINE": MacroRoutine(),
    "RETURN": MacroReturn(),
}


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    if os.path.isfile('C:/Users/Harry/PycharmProjects/SpeakEasy/src'):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
    df.run()
    save(df, varfile)


if __name__ == '__main__':
    openai.api_key_path = 'C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt'
    load(visits(), 'src/userLog.pkl')