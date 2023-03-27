import json
import os.path
import pickle
import time
from typing import Dict, Any, List
import requests
from emora_stdm import DialogueFlow, Macro, Ngrams
import re
import pyaudio
import wave
transitions = {
    'state': 'start',
    '#TIME #WEATHER #ASKNAME': {
        '[{no, fuck, don, nah, not}] #APPEND': {
            '`Sorry for asking your name...`': 'end'
        },
        '#GetName #APPEND': {
            '`Hi, ` $NAME`. Nice to meet you. What do you want me to recommend?`': {
                '[{movie}] #APPEND': {
                    '': 'movie'
                },
                '[{music, song}] #APPEND': {
                    '': 'music'
                },
                'error': {
                    '`Sorry, I cannot make recommendation for this topic.`': 'end'
                }
            }
        },
        'error': {
            '`Welcome back, `$NAME `. Did you get to try \"` $REC `\"?`': {
                'error': {
                    '`Ok. What else do you want me to recommend?`': {
                        '[{movie}]': {
                            '': 'movie'
                        },
                        '[{music, song}]': {
                            '': 'music'
                        },
                        'error': {
                            '`Sorry, I cannot make recommendation for this topic.`': 'end'
                        }
                    }
                }
            }
        }
    }
}

transitions_music = {
    'state': 'music',
    '`How about ` #MUSICREC `?`': {
        '[{already, <not, like>, another, don, hate, remember, other, nah, no, nope}]': {
            '`Ok.`': 'music',
        },
        '[{what, detail, explain, who, how, where, when, about}]': {
            '$DETAIL': {
                '[{already, <not, like>, another, don, hate, remember, other, nah, no, nope}]': {
                    '`Ok.`': 'music',
                },
                'error': {
                    '`Enjoy.`': 'end'
                }
            }
        },
        'error': {
            '`Enjoy.`': 'end'
        }
    }
}
transitions_movie = {
    'state': 'movie',
    '`How about ` #MOVIEREC `?`': {
        '[{already, <not, like>, another, don, hate, remember, other, nah, no, nope}] #APPEND': {
            '`Ok.`': 'movie',
        },
        '[{what, detail, explain, who, how, where, when, about}] #APPEND':{
            '$DETAIL': {
                '[{already, <not, like>, another, don, hate, remember, other, nah, no, nope}]': {
                    '`Ok.`': 'movie',
                },
                'error': {
                    '`Enjoy.`': 'end'
                }
            }
        },
        'error': {
            '`Enjoy.`': 'end'
        }
    }
}

class MacroAppendAns(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = ngrams.raw_text()
            vars['SPOKENTIME'] = 15
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + ngrams.raw_text()
            vars['SPOKENTIME'] += 15
        return
class MacroNumQuestions(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            vars['NUMQUEST'] = 0
        else:
            vars['NUMQUEST'] = vars['ANSWERS'].count("?")
        return vars['NUMQUEST']

class MacroAVGToken(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vars['AVGToken'] = len(vars['ANSWERS'])/vars['SPOKENTIME']
        return vars['AVGTOKEN']
class MacroTic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tokens = vars['ANSWERS'].split()
        vars['TIC'] = {}

        for token in tokens:
            if token in vars['TIC']:
                vars['TIC'][token] += 1
            else:
                vars['TIC'][token] = 1

        return vars['TIC']
class MacroAcknow(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            return
        if ngrams.raw_text() in vars['ANSWERS']:
            vars['ACKNOW'] += 1
        return vars['ACKNOW']

class MacroAckward(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        AWK = []
        for tran in AWK:
            if ngrams.raw_text() in AWK:
                vars['USEDAWKWARD'] += tran
        return vars['USEDAWKWARD']

class MacroRecordAudio(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        # Define audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "output.wav"

        # Create PyAudio object
        audio = pyaudio.PyAudio()

        # Start audio stream
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print("Recording...")

        # Record audio data
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")

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

        return
class MacroMovieRec(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vars['REC'] = "NA"
        if 'GENRE' not in vars or vars['GENRE'] == "fantasy":
            vars['GENRE'] = "romantic comedy"
            if vars['REC'] == "About Time":
                vars['DETAIL'] = "A pair of teenagers with cystic fibrosis meet in a hospital and fall in love, " \
                                 "though their disease means they must avoid close physical contact."
                vars['REC'] = "Five Feet Apart"
            vars['DETAIL'] = "The film is about a young man with the ability to time travel who tries to change his " \
                             "past in hopes of improving his future"
            vars['REC'] = "About Time"

        elif vars['GENRE'] == "romantic comedy":
            vars['GENRE'] = "horror"
            vars['DETAIL'] = "In 1971, Roger and Carolyn Perron move into a farmhouse in Harrisville, Rhode Island, " \
                             "with their five daughters. Paranormal events occur within the first few nights."
            vars['REC'] = "The Conjuring"
        elif vars['GENRE'] == "horror":
            vars['GENRE'] = "action"
            vars['DETAIL'] = "Its story follows John Wick (Keanu Reeves), a legendary hitman who is forced out of " \
                             "retirement to seek revenge against the men who killed his puppy, a final gift from his " \
                             "recently deceased wife"
            vars['REC'] = "John Wick"
        elif vars['GENRE'] == "action":
            vars['GENRE'] = "musical"
            vars['DETAIL'] = "It's a musical that presents the story of Maria, who takes a job as governess to a " \
                             "large family while she decides whether to become a nun."
            vars['REC'] = "The Sound of Music"
        else:
            vars['GENRE'] = "fantasy"
            vars['DETAIL'] = "The main story arc concerns Harry's conflict with Lord Voldemort, a dark wizard who " \
                             "intends to become immortal, overthrow the wizard governing body known as the Ministry " \
                             "of Magic and subjugate all wizards and Muggles (non-magical people)."
            vars['REC'] = "Harry Potter"
        return vars['REC']
class MacroMusicRec(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'GENRE' not in vars or vars['GENRE'] == "rock":
            vars['GENRE'] = "children"
            vars['DETAIL'] = "It's a fun children's song by Parry Gripp."
            vars['REC'] = "Raining Tacos"
        elif vars['GENRE'] == "children":
            vars['GENRE'] = "classic"
            vars['DETAIL'] = "The first movement was usually in Sonata Form, consisting of three sections, " \
                             "Exposition, Development and Recapitulation."
            vars['REC'] = "5th Symphony Beethoven"
        elif vars['GENRE'] == "classic":
            vars['GENRE'] = "pop"
            vars['DETAIL'] = "It's a pop music by Ed Sheeran."
            vars['REC'] = "Shape of You"
        else:
            vars['GENRE'] = "rock"
            vars['DETAIL'] = "It's a classic rock song by AC/DC."
            vars['REC'] = "Thunderstruck"
        return vars['REC']
class MacroAskName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ask_name' not in vars:
            vars['ask_name'] = "May I have your name?"
        elif vars['ask_name'] == "May I have your name?" or vars['ask_name'] == "What's your name?":
            vars['ask_name'] = "What should I call you?"
        else:
            vars['ask_name'] = "What's your name?"
        return vars['ask_name']


class MacroGetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        r = re.compile(r"(\b\w+\b)\W*$")
        m = r.search(ngrams.text())
        if m is None: return False
        name = m.group(1)

        if 'NAME' not in vars or vars['NAME'] != name:
            vars['NAME'] = name
            return True
        else:
            return False


class MacroTime(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        current_time = time.strftime('%H')
        if current_time < '12':
            return "Good morning; "
        elif current_time < '17':
            return "Good afternoon; "
        else:
            return "Good evening; "


class MacroWeather(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        url = 'https://api.weather.gov/gridpoints/FFC/52,88/forecast'
        r = requests.get(url)
        d = json.loads(r.text)
        periods = d['properties']['periods']
        today = periods[0]
        if today['shortForecast'].__contains__('Sunny'):
            return "it's sunny today. "
        elif today['shortForecast'].__contains__('Cloudy'):
            return "it's cloudy today. "
        elif today['shortForecast'].__contains__('Shower'):
            return "it's rainy today. "
        else:
            return "it's clear today. "


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    if os.path.isfile('C:/Users/Harry/PycharmProjects/SpeakEasy/visits.pkl'):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
    df.run()
    save(df, varfile)

macros = {
    'GetName': MacroGetName(),
    'TIME': MacroTime(),
    'WEATHER': MacroWeather(),
    'ASKNAME': MacroAskName(),
    "MOVIEREC": MacroMovieRec(),
    "MUSICREC": MacroMusicRec(),
    "APPEND": MacroAppendAns()
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_music)
df.load_transitions(transitions_movie)
# df.knowledge_base().load_json_file('C:/Users/Harry/PycharmProjects/SpeakEasy/ontology')
df.add_macros(macros)

if __name__ == '__main__':
    load(df, 'C:/Users/Harry/PycharmProjects/SpeakEasy/visits.pkl')