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
function_words_list = [
    "i", "me", "my", "mine", "you", "your", "yours", "he", "him", "his",
    "she", "her", "hers", "we", "us", "our", "ours", "they", "them", "their", "theirs",
    "it", "its", "this", "that", "these", "those",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might", "must", "can", "could",
    "and", "or", "but", "so", "if", "then", "else", "though", "although", "because", "since", "unless",
    "a", "an", "the", "some", "any",
    "first", "next", "last", "many", "much", "several", "few", "less",
    "more", "most", "several", "such", "only", "own", "just", "than",
    "too", "very", "also", "well", "even", "like", "yeah", "right",
    "actually", "basically", "certainly", "definitely", "finally", "generally", "honestly",
    "however", "indeed", "maybe", "naturally", "obviously", "perhaps", "possibly",
    "probably", "quite", "really", "simply", "surely", "truly", "usually", "you know"
]


class V(Enum):
    effectiveness = 0,
    satisfactory = 0,
    correctness = 0,
    interpretability = 0,
    coherence = 0,
    detail = 0,
    blank = 0,


transitions = {
    'state': 'start',
    '$RESPONSE="Hello. How are you?" #GTTS #USERINPUT': {
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
                    '`Take care!`': 'evaluation_state'
                }
            }
        }
    }
}

transitions_feedback = {
    'state': 'feedback',
    '#CONGRATS #QUEST #SPEED #TIC #ACKNOW #AWKWARD #USERINPUT': {
        '#GPTDETAIL': {
            '#DETAIL': 'evaluation_state'
        },
        'error': {
            '$RESPONSE="Sorry. I do not understand." #GTTS': 'evaluation_state'
        }
    }
}
transitions_evaluation = {
    'state': 'evaluation_state',
    '$RESPONSE="Now, can you evaluate me? I will ask you a series of five questions. You can answer it in any way you '
    'want. The first question is how connected did you feel during our conversation?" #GTTS #USERINPUT': {
        '#GPTCOH': {
            '$RESPONSE="Thank you. The second question is how did you like the conversation with me?" #GTTS #USERINPUT': {
                '#GPTSAT': {
                    '$RESPONSE="Got it. Did I say anything wrong during the conversation?" #GTTS #USERINPUT': {
                        '#GPTCOR': {
                            '$RESPONSE="Okay, did you ever have a hard time understanding me?" #GTTS #USERINPUT': {
                                '#GPTINT': {
                                    '$RESPONSE="The last question is how suitable do you think is my feedback?" #GTTS '
                                    '#USERINPUT': {
                                        '#GPTEFF': {
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
                            'error': {
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
    os.system("afplay bot_output.mp3")  # Mac
    # os.system("start bot_output.mp3")  # Window
    # time.sleep(MP3("bot_output.mp3").info.length)  # Window


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


class MacrogTTS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'BOTLOG' not in vars:
            vars['BOTLOG'] = vars['RESPONSE']
        vars['BOTLOG'] = vars['BOTLOG'] + vars['RESPONSE']
        audio(vars['RESPONSE'])
        return vars['RESPONSE']


class MacroCongrats(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        audio("Congratulations! The evaluation process is over. Based on the conversation we just had, here are some "
              "suggestions.")
        return True


def get_eval(vars: Dict[str, Any]):
    # Recursive function to iterate over all dictionaries and check for '-1' values
    def check_for_negative_values(d: Dict[str, Any]):
        negative_attributes = []
        for key, value in d.items():
            if isinstance(value, dict):
                # If the value is a dictionary, call the function recursively
                sub_dict_neg_attrs = check_for_negative_values(value)
                negative_attributes.extend([f"{key}.{sub_key}" for sub_key in sub_dict_neg_attrs])
            elif value == "-1":
                # If the value is '-1', add the key to the list of negative attributes
                negative_attributes.append(key)
        return negative_attributes

    # Call the recursive function to get all negative attributes
    negative_attributes = check_for_negative_values(vars)

    # Modify the EVAL string based on the negative attributes
    if negative_attributes:
        negative_attributes_str = ', '.join('and ' + attr for attr in negative_attributes)
        vars["EVAL"] = f"Thank you for your feedbacks. I will do my best to improve {negative_attributes_str} before " \
                       f"I see you again. Good bye."
    else:
        vars["EVAL"] = "Thank you for your feedbacks! Good bye."

    audio(vars["EVAL"])
    return vars["EVAL"]


class MacroNumQuestions(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            vars['NUMQUEST'] = 0
        else:
            vars['NUMQUEST'] = vars['ANSWERS'].count("?")
        if float(vars['NUMQUEST'] / vars['UTTERANCE']) < 0.39:
            a = "You should consider asking more questions."
        else:
            a = "Great job! You have asked enough questions today."
        audio(a)
        return a


class MacroAVGToken(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        total_time = vars['SPOKENTIME'] / 60
        num_words = len(vars['ANSWERS'].split())
        vars['WPM'] = num_words / total_time
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
        common_words = ['the', 'of', 'and', 'to', 'a', 'in', 'that', 'it', 'with', 'for', 'as', 'at', 'on', 'but',
                        'by', 'not', 'or', 'be', 'from', 'this']

        number_of_words_outputted = 3
        a = ""
        for word in range(len(sorted_words)):
            if sorted_words[word][0] not in common_words:
                number_of_words_outputted -= 1
                if number_of_words_outputted == 0:
                    a += f'the word {sorted_words[word][0]}'
                    break
                else:
                    a += f'the word {sorted_words[word][0]}, '

        a = "You should use less of " + a + ". You use these too frequently."
        audio(a)

        return a


class MacroAcknow(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        #mean_lsm = calculate_mean_lsm(vars['BOTLOG'], vars['ANSWERS'], function_words_list)
        mean_lsm = language_style_matching(vars['BOTLOG'], vars['ANSWERS'], function_words_list)
        vars['LSM'] = mean_lsm
        if mean_lsm >= 0.8:
            a = "You have successfully showed your attention to your partner."
        else:
            a = "You should show more attention to your partner. One good way is to acknowledge what " \
                "your partner said previously."
        audio(a)
        return a


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


# Extract sentences from paragraphs
def extract_sentences(paragraph):
    return sent_tokenize(paragraph)


# Calculate LSM
def language_style_matching(text1, text2, function_words):
    counts1 = count_function_words(text1, function_words)
    counts2 = count_function_words(text2, function_words)

    differences = [abs(counts1[word] - counts2[word]) for word in function_words]

    lsm = 1 - sum(differences) / len(function_words)

    return lsm


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


# Preprocess text
def preprocess(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return words


class MacroAwkward(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        AWK = ["uh", "um", "like", "you know", "well", "so", "anyway", "actually", "i mean", "to be honest"]
        if 'USEDAWKWARD' not in vars:
            vars['USEDAWKWARD'] = 0

        for tran in AWK:
            vars['USEDAWKWARD'] += vars['BOTLOG'].lower().count(tran.lower())

        if vars['USEDAWKWARD'] < 10:
            a = "You did not make many awkward transitions. Would you like to know more detail information about the " \
                "feedback?"
        else:
            a = "Try to avoid using uh, um, like, you know, and i mean. Would you like to know more detail " \
                "information about the feedback?"

        audio(a)

        return a


class MacroDetail(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if vars['detail'] == 'yes':
            a = "Here is the detailed report. Your LSM score which shows the similarity between your response and my " \
                "response was " + str(round(vars['LSM'], 2)) + ", higher than 0.8 is a good score. I have counted a total of " \
                + str(round(vars['USEDAWKWARD'], 2)) + " awkward transitions used. You have asked " + str(round(vars['NUMQUEST'], 2)) + \
                " questions. Your talking speed was " + str(round(vars['WPM'], 2)) + " words per minutes."
            audio(a)
            return a
        else:
            a = "okay"
            audio(a)
            return a


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


macros = {
    "USERINPUT": MacroRecordAudio(),
    "GTTS": MacrogTTS(),
    'CONGRATS': MacroCongrats(),
    'GET_EVAL': MacroNLG(get_eval),
    'GPTDETAIL': MacroGPTJSON('Does the user want to know the detail about the feedback? Respond in yes or no.',
                              {V.detail.name: "yes"}),
    'GPTEFF': MacroGPTJSON(
        'Considering the user input about the conversation, assign a score: -1 for negative, 0 for neutral, '
        '1 for positive.', {V.effectiveness.name: "0"}),
    'GPTSAT': MacroGPTJSON(
        'Considering the user input about the satisfaction of the conversation, assign a score to satisfactiory: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign the score to effectiveness.', {V.satisfactory.name: "0"}),
    'GPTCOR': MacroGPTJSON(
        'Considering the user input about the correctness of the conversation, assign a score to correctness: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign score to effectiveness.', {V.correctness.name: "0"}),
    'GPTINT': MacroGPTJSON(
        'Considering the user input about the interpretability of the conversation, assign a score to interpretability: -1 for negative, 0 for '
        'neutral, 1 for positive. Do not assign score to effectiveness.', {V.interpretability.name: "0"}),
    'GPTCOH': MacroGPTJSON(
        'Considering the user input about the coherence of the conversation, assign a score to coherence: -1 for negative, 0 for neutral, '
        '1 for positive. Do not assign score to effectiveness.', {V.coherence.name: "0"}),
    "QUEST": MacroNumQuestions(),
    "SPEED": MacroAVGToken(),
    "TIC": MacroTic(),
    "ACKNOW": MacroAcknow(),
    "AWKWARD": MacroAwkward(),
    "DETAIL": MacroDetail()
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_feedback)
df.load_transitions(transitions_evaluation)
df.add_macros(macros)

if __name__ == '__main__':
    load(df, 'C:/Users/Harry/PycharmProjects/conversational-ai/resources/visits.pkl')
