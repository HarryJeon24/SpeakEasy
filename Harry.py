import os.path
import pickle
import time
from typing import Dict, Any, List
from emora_stdm import DialogueFlow, Macro, Ngrams
import re
import pyaudio
import wave
import openai
from gtts import gTTS
from src.utils import MacroGPTJSON, MacroNLG
from enum import Enum
import threading
from mutagen.mp3 import MP3
from nltk.tokenize import sent_tokenize
import nltk

# Download the required resources
nltk.download('punkt')

# Function words list (you can modify this list as needed)
function_words = [
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "of",
    "i", "me", "my", "mine", "you", "your", "yours", "he", "him", "his",
    "she", "her", "hers", "we", "us", "our", "ours", "they", "them", "their", "theirs",
    "it", "its", "who", "whom", "whose", "this", "that", "these", "those", "there",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might", "must", "can", "could"
]


# Preprocess text
def preprocess(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return words


# Calculate normalized function word counts
def count_function_words(text, function_words):
    words = preprocess(text)
    total_words = len(words)
    func_word_counts = {word: 0 for word in function_words}

    for word in words:
        if word in func_word_counts:
            func_word_counts[word] += 1

    normalized_counts = {word: count / total_words for word, count in func_word_counts.items()}

    return normalized_counts


# Calculate LSM
def language_style_matching(text1, text2, function_words):
    counts1 = count_function_words(text1, function_words)
    counts2 = count_function_words(text2, function_words)

    differences = [abs(counts1[word] - counts2[word]) for word in function_words]

    lsm = 1 - sum(differences) / len(function_words)

    return lsm

# Extract sentences from paragraphs
def extract_sentences(paragraph):
    return sent_tokenize(paragraph)

# Calculate mean LSM of each pair of sentences
def calculate_mean_lsm(paragraph1, paragraph2, function_words):
    sentences1 = extract_sentences(paragraph1)
    sentences2 = extract_sentences(paragraph2)
    total_lsm = 0
    num_pairs = 0

    for sentence1 in sentences1:
        for sentence2 in sentences2:
            lsm = language_style_matching(sentence1, sentence2, function_words)
            total_lsm += lsm
            num_pairs += 1

    mean_lsm = total_lsm / num_pairs if num_pairs > 0 else 0
    return mean_lsm


class V(Enum):
    effectiveness = 0,
    satisfactory = 0,
    correctness = 0,
    interpretability = 0,
    coherence = 0

transitions = {
    'state': 'start',
    '`Hello. How are you?` $RESPONSE="Hello. How are you?" #GTTS #USERINPUT': {
        '[good]': {
            '`Glad to hear that you are doing well :)`': {
                'error': {
                    '`See you later!`': 'feedback'
                }
            }
        },
        'error': {
            '`I hope your day gets better soon :(`': {
                'error': {
                    '`Take care!`': 'feedback'
                }
            }
        }
    }
}

transitions_feedback = {
    'state': 'feedback',
    '$RESPONSE="Congratulation! The evaluation process is over. Based on the conversation we just had, here are some '
    'suggestions." #GTTS #QUEST #SPEED #TIC #ACKNOW #ACKWARD #USERINPUT': {
        '$NATEX="yes great wonderful fantastic excellent happy glad perfect awesome thank" #SIMPLENATEX': {
            '`My pleasure.` $RESPONSE="My pleasure" #GTTS': 'evaluation',
        },
        'error': {
            '$RESPONSE="I am sorry." #GTTS': 'evaluation'
        }
    }
}
transitions_evaluation = {
    'state': 'evaluation',
    '$RESPONSE="Now, can you evaluate me? I will ask you a series of five questions. You can answer it in any way you '
    'want. The first question is how suitable do you think is my feedback?" #GTTS #USERINPUT': {
        '#GPTEFF': {
            '$RESPONSE="Thank you. The second question is how did you like the conversation with me?" #GTTS #USERINPUT': {
                '#GPTSAT': {
                    '$RESPONSE="Got it. Did I say anything wrong during the conversation?" #GTTS #USERINPUT': {
                        '#GPTCOR': {
                            '$RESPONSE="Okay, did you ever have a hard time understanding me?" #GTTS #USERINPUT': {
                                '#GPTINT': {
                                    '$RESPONSE="The last question is How connected did you feel during our '
                                    'conversation?" #GTTS #USERINPUT': {
                                        '#GPTCOH': {
                                            '#GET_EVAL': 'end'
                                        },
                                        'error': {
                                            '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
                                        }
                                    }
                                },
                                'error': {
                                    '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
                                }
                            },
                            'error' : {
                                '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
                            }
                        },
                        'error': {
                            '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
                        }
                    },
                    'error': {
                        '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
                    }
                }
            },
            'error': {
                '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
            }
        },
        'error': {
            '$RESPONSE="Sorry, I did not understand it." #GTTS': 'end'
        }
    }
}

def audio(text: str):
    tts = gTTS(text=text, lang='en')
    tts.save("bot_output.mp3")
    os.system("start bot_output.mp3")
    time.sleep(MP3("bot_output.mp3").info.length)


class MacroNatex(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if vars["CURRENT"] in vars["NATEX"]:
            return True
        else:
            return False


class MacrogTTS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'BOTLOG' not in vars:
            vars['BOTLOG'] = vars['RESPONSE']
        vars['BOTLOG'] = vars['BOTLOG'] + vars['RESPONSE']
        audio(vars['RESPONSE'])
        return vars['RESPONSE']


class MacroNumQuestions(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            vars['NUMQUEST'] = 0
        else:
            vars['NUMQUEST'] = vars['ANSWERS'].count("?")
        if float(vars['NUMQUEST']/vars['UTTERANCE']) < 0.39:
            a = "You should consider asking more questions."
        else:
            a = "Great job! You have asked enough questions today."
        audio(a)
        return a


class MacroAVGToken(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        total_time = vars['SPOKENTIME']/60
        num_words= len(vars['ANSWERS'].split())
        vars['WPM'] = num_words/total_time
        if vars['WPM'] < 120:
            a = "You are talking too slowly. You should talk faster."
        elif vars['WPM'] > 150:
            a = "You are talking too fast. You should talk slower."
        else:
            a = "You are at the right talking speed."
        audio(a)
        return a


class MacroTic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tokens = vars['ANSWERS'].split()
        vars['TIC'] = {}

        for token in tokens:
            if token in vars['TIC']:
                vars['TIC'][token] += 1
            else:
                vars['TIC'][token] = 1

        # Sort the word frequency dictionary by count
        sorted_words = sorted(vars['TIC'].items(), key=lambda x: x[1], reverse=True)

        # Extract the words at the desired positions
        a = ""
        if len(sorted_words) >= 6:
            a = f"{sorted_words[3][0]} {sorted_words[4][0]} {sorted_words[5][0]} {sorted_words[6][0]}"
        a = "You should use less of " + a + "You use these too frequently."
        audio(a)
        return a


class MacroAcknow(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        mean_lsm = calculate_mean_lsm(vars['BOTLOG'], vars['ANSWERS'], function_words)
        if mean_lsm >= 0.8:
            a = "You have successfully showed your attention to your partner."
        else:
            a = "You should show more attention to your partner. One good way is to acknowledge what " \
                                  "your partner said previously."
        audio(a)
        return a


class MacroAwkward(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        AWK = ["uh", "um", "like", "you know", "well", "so", "anyway", "actually", "i mean", "to be honest"]
        if 'USEDAWKWARD' not in vars:
            vars['USEDAWKWARD'] = 0

        for tran in AWK:
            vars['USEDAWKWARD'] += vars['BOTLOG'].lower().count(tran.lower())

        if vars['USEDAWKWARD'] < 10:
            a = "You did not make many awkward transitions."
        else:
            a = "Try to avoid using uh, um, like, you know, and i mean."

        audio(a)

        return a


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
        a = text
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = text.lower()
            vars['SPOKENTIME'] = duration
            vars['UTTERANCE'] = 1
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + text.lower()
            vars['SPOKENTIME'] = vars['SPOKENTIME'] + duration
            vars['UTTERANCE'] = vars['UTTERANCE'] + 1
        print("Your Input: ", a)

        return True


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    if os.path.isfile('C:/Users/Harry/PycharmProjects/conversational-ai/resources/visits.pkl'):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
    df.run()
    save(df, varfile)


def get_eval(vars: Dict[str, Any]):
    # Find all Enum members with '-1' in their names
    negative_attributes = [attr for attr in V if '-1' in attr.name]

    # Modify the EVAL string based on the negative attributes
    if negative_attributes:
        negative_attributes_str = ', '.join(attr.name for attr in negative_attributes)
        vars["EVAL"] = f"Thank you for your feedbacks. I will do my best to improve {negative_attributes_str} before " \
                       f"I see you again. Good bye."
    else:
        vars["EVAL"] = "Thank you for your feedbacks! Good bye."
    audio(vars["EVAL"])
    return vars["EVAL"]

macros = {
    "USERINPUT": MacroRecordAudio(),
    "GTTS": MacrogTTS(),
    'GET_EVAL': MacroNLG(get_eval),
    'GPTEFF': MacroGPTJSON('Assign score for the feedback. -1 means negative, 0 means neutral, 1 means positive.',
                                  {V.effectiveness.name: ["0"]}),
    'GPTSAT': MacroGPTJSON('Assign score for the feedback. -1 means negative, 0 means neutral, 1 means positive.',
                                  {V.satisfactory.name: ["0"]}),
    'GPTCOR': MacroGPTJSON('Assign score for the feedback. -1 means negative, 0 means neutral, 1 means positive.',
                          {V.correctness.name: ["0"]}),
    'GPTINT': MacroGPTJSON('Assign score for the feedback. -1 means negative, 0 means neutral, 1 means positive.',
                          {V.interpretability.name: ["0"]}),
    'GPTCOH': MacroGPTJSON('Assign score for the feedback. -1 means negative, 0 means neutral, 1 means positive.',
                          {V.coherence.name: ["0"]}),
    "QUEST": MacroNumQuestions(),
    "SPEED": MacroAVGToken(),
    "TIC": MacroTic(),
    "ACKNOW": MacroAcknow(),
    "ACKWARD": MacroAwkward(),
    "SIMPLENATEX": MacroNatex()

}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_feedback)
df.load_transitions(transitions_evaluation)
df.knowledge_base().load_json_file('C:/Users/Harry/PycharmProjects/conversational-ai/resources/ontology_quiz3.json')
df.add_macros(macros)

if __name__ == '__main__':
    load(df, 'C:/Users/Harry/PycharmProjects/conversational-ai/resources/visits.pkl')


