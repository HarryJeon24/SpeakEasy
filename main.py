import os.path
import pickle
from emora_stdm import DialogueFlow, Macro, Ngrams
from typing import List
import re
import time
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
from src.transitions.entertainment import transitions_select_topic, transitions_movie, transitions_music, \
    transitions_movie_rec, transitions_music_rec
import src.transitions.entertainment as ent
from src.transitions.travel import transitions_travel, travel_question, travel_other_location
import src.transitions.travel as tra
from src.transitions.healthAndIntro import health_transitions, food_transitions
import src.transitions.babel as babel
from src.transitions.babel import transitions_babel, transitions_outro
import src.transitions.healthAndIntro as hlth


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
                                            'error': 'health'
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

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(health_transitions)
    df.load_transitions(transitions_babel)
    df.load_transitions(transitions_outro)
    df.load_transitions(food_transitions)
    df.load_transitions(transitions_feedback)
    df.load_transitions(transitions_evaluation)
    df.load_transitions(transitions_music)
    df.load_transitions(transitions_movie)
    df.load_transitions(transitions_select_topic)
    df.load_transitions(transitions_music_rec)
    df.load_transitions(transitions_movie_rec)
    df.load_transitions(transitions_travel)
    df.load_transitions(travel_question)
    df.load_transitions(travel_other_location)
    df.add_macros(macros)
    return df


def audio(text: str):
    tts = gTTS(text=text, lang='en')
    tts.save("bot_output.mp3")
    os.system("afplay bot_output.mp3")  # Mac
    # os.system("start bot_output.mp3")  # Windows
    # time.sleep(MP3("bot_output.mp3").info.length)


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
        # SAVE_DIR = "/src"  #Harry
        SAVE_DIR = "/Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy2/src"  # Max
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

        # C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt
        # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/chat_gpt_api_key.txt
        openai.api_key_path = '/Users/maxbagga/Desktop/Emory 8th Semester/CS 329/chat_gpt_api_key.txt'
        # C:/Users/Harry/PycharmProjects/SpeakEasy/src/USERINPUT.wav
        # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy/srcUSERINPUT.wav
        audio_file = open("/Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy2/src/USERINPUT.wav", "rb")
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
        intro = f'My name is SpeakEasy. I am a chatbot designed to help you improve your conversations. ' \
                f'We are going to engage in a few minutes long conversation and I will provide some ' \
                f'feedback on your conversational skills. Whenever the screen displays ' \
                f'"Recording... Press Enter to stop" please begin speaking and press Enter when you are ' \
                f'finished. When you see "U:" press enter once again. Before we get started, '
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

    # Introduction
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

    # Entertainment
    'TALK_MOVIE': ent.Macrotalkmovie(),
    'TALK_MUSIC': ent.Macrotalkmusic(),
    'FAV_MOVIE': ent.Macrofavmovie(),
    'FAV_SONG': ent.Macrofavmusic(),
    'GET_MOVIE_PREFERENCE': ent.MacroGetFavMovie(),
    'GET_MOVIE_PREFERENCE_BOOL': ent.Macroget_favorite_movie_bool(),
    'SET_MOVIE_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s favorite movie?',
        {ent.V.favorite_movie.name: "Forrest Gump", ent.V.favorite_movie_bool.name: True},
        {ent.V.favorite_movie.name: "none", ent.V.favorite_movie_bool.name: False}
    ),
    'GET_MOVIE_GENRE_PREFERENCE': ent.MacroGetFavMovieG(),
    'GET_MOVIE_GENRE_PREFERENCE_BOOL': MacroNLG(ent.get_movie_genre_preference_bool),
    'SET_MOVIE_GENRE_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s preferred movie genre?',
        {ent.V.favorite_movie_genre.name: "Action", ent.V.favorite_movie_genre_bool.name: True},
        {ent.V.favorite_movie_genre.name: "none", ent.V.favorite_movie_genre_bool.name: False}
    ),
    'GET_MOVIE_THEME_PREFERENCE': ent.MacroGetFavMovieT(),
    'GET_MOVIE_THEME_PREFERENCE_BOOL': MacroNLG(ent.get_movie_theme_preference_bool),
    'SET_MOVIE_THEME_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s movie about? Summarize it in a short sentence or two.',
        {ent.V.favorite_movie_theme.name: "It is about a dog and a child who love each other.",
         ent.V.favorite_movie_theme_bool.name: True},
        {ent.V.favorite_movie_theme.name: "none", ent.V.favorite_movie_theme_bool.name: False}
    ),
    'GET_MOVIE_CHARACTER_PREFERENCE': ent.MacroGetFavMovieC(),
    'GET_MOVIE_CHARACTER_PREFERENCE_BOOL': MacroNLG(ent.get_movie_character_preference_bool),
    'SET_MOVIE_CHARACTER_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s favorite character?',
        {ent.V.favorite_movie_character.name: "Hermione Granger", ent.V.favorite_movie_character_bool.name: True},
        {ent.V.favorite_movie_character.name: "none", ent.V.favorite_movie_character_bool.name: False}
    ),
    'THANK_REC': ent.MacroThankRec(),
    'WHO_FAV_C': ent.MacroWhoC(),
    'WHAT_FAV_T': ent.MacroWhatT(),
    'OK': ent.MacroOK(),
    'GET_MUSIC_PREFERENCE': ent.MacroGetFavMusic(),
    'GET_MUSIC_PREFERENCE_BOOL': MacroNLG(ent.get_favorite_music_bool),
    'SET_MUSIC_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s favorite music/song?',
        {ent.V.favorite_song.name: "Love Story", ent.V.favorite_song_bool.name: True},
        {ent.V.favorite_song.name: "none", ent.V.favorite_song_bool.name: False}
    ),
    'GET_MUSIC_LIKED_ASPECT': ent.MacroGetMusicA(),
    'GET_MUSIC_LIKED_ASPECT_BOOL': MacroNLG(ent.get_music_liked_aspect_bool),
    'SET_MUSIC_LIKED_ASPECT': MacroGPTJSON(
        'What does the speaker like about the song?',
        {ent.V.music_liked_aspect.name: "the melody", ent.V.music_liked_aspect_bool.name: True},
        {ent.V.music_liked_aspect.name: "none", ent.V.music_liked_aspect_bool.name: False}
    ),
    'GET_MUSIC_GENRE_PREFERENCE': ent.MacroGetMusicG(),
    'GET_MUSIC_GENRE_PREFERENCE_BOOL': MacroNLG(ent.get_music_genre_preference_bool),
    'SET_MUSIC_GENRE_PREFERENCE': MacroGPTJSON(
        'What is the speaker\'s favorite genre of music?',
        {ent.V.music_genre_preference.name: "pop", ent.V.music_genre_preference_bool.name: True},
        {ent.V.music_genre_preference.name: "none", ent.V.music_genre_preference_bool.name: False}
    ),
    'GET_MUSIC_THEME_PREFERENCE': ent.MacroGetMusicT(),
    'GET_MUSIC_THEME_PREFERENCE_BOOL': MacroNLG(ent.get_music_theme_preference_bool),
    'SET_MUSIC_THEME_PREFERENCE': MacroGPTJSON(
        'What is the theme of the speaker\'s favorite song?',
        {ent.V.music_theme_preference.name: "love", ent.V.music_theme_preference_bool.name: True},
        {ent.V.music_theme_preference.name: "none", ent.V.music_theme_preference_bool.name: False}
    ),
    'GET_MUSIC_ARTIST_PREFERENCE': ent.MacroGetMusicAr(),
    'GET_MUSIC_ARTIST_PREFERENCE_BOOL': MacroNLG(ent.get_music_artist_preference_bool),
    'SET_MUSIC_ARTIST_PREFERENCE': MacroGPTJSON(
        'Who is the speaker\'s favorite artist for that genre?',
        {ent.V.music_artist_preference.name: "Taylor Swift", ent.V.music_artist_preference_bool.name: True},
        {ent.V.music_artist_preference.name: "none", ent.V.music_artist_preference_bool.name: False}
    ),
    'THANK_REC2': ent.MacroThankRec2(),
    'WHO_FAV': ent.MacroWhoFav(),
    'MORE_T': ent.MacroMoreT(),
    'WHAT_G': ent.MacroWhatG(),
    'GET_USER_ANSWER': ent.Macroget_user_answer(),
    'SET_USER_ANSWER': MacroGPTJSON(
        'Does the speaker seem satisfied?',
        {ent.V.user_answer.name: True},
        {ent.V.user_answer.name: False}
    ),
    'GET_MOVIE': ent.MacroRecommendMovie(),
    'ANOTHER': ent.MacroAnother(),
    'GET_SONG': ent.MacroRecommendSong(),
    'SONG_GET_ARTIST': ent.MacroGetSongArtist(),
    'MOVIE_GET_OVERVIEW': ent.MacroGetMovieOverview(),

    # Travel
    'WHEREF': tra.MacroWhereF(),
    'GET_LOCATION': tra.Macroget_location(),
    'SET_LOCATION': MacroGPTJSON(
        'What place does the speaker mention?',
        {tra.V.location.name: ["Austria", "Europe", "Chicago"]}),

    'FAV_PART': tra.MacroFavPart(),
    'GET_FAVORITE': tra.MacroGetFavThing(),
    'SET_FAVORITE': MacroGPTJSON(
        'What does the speaker like about the place they mentioned?',
        {tra.V.favoriteThing.name: ["great weather", "good food", "feels like home"]}),
    'GOOGLE': tra.MacroGoogle(),
    'SUCKS': tra.MacroSucks(),
    'RB': tra.MacroRB(),
    'RATHER_LIVE': tra.MacroRatherLive(),
    'SOUND': tra.MacroSound(),
    'GET_LOCATION2': tra.Macroget_location2(),
    'OYSTER': tra.MacroOyster(),

    'HAVE_YOU': tra.MacroHaveYou(),
    'WHAT_ACT': tra.MacroWhatAct(),
    'GET_ACTIVITY': tra.Macroget_activity(),
    'SET_ACTIVITY': MacroGPTJSON(
        'What did the speaker do (in present tense)?',
        {tra.V.favoriteThing.name: ["go to the museum", "eat good food", "go swimming"]}),
    'ISEE': tra.MacroISEE(),
    'MENEITHER': tra.MacroMeNeither(),

    'OTHER_PLACE': tra.MacroOtherPlace(),
    'GET_LOCATION3': tra.MacroGET_LOCATION3(),
    'SOLO': tra.MacroSolo(),
    'SOLOP': tra.MacroSoloP(),
    'SOLON': tra.MacroSoloN(),
    'THANKCHAT': tra.MacroThankC(),
    'FRI': tra.MacroFRI(),
    'FRIP': tra.MacroFRIP(),
    'FRIN': tra.MacroFRIN(),
    
    'GET_USER_OPINION': MacroNLG(tra.get_user_opinion),
    'SET_USER_OPINION': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {tra.V.user_opinion.name: True},
        {tra.V.user_opinion.name: False}),

    'GET_USER_VISITED': MacroNLG(tra.get_user_visited),
    'SET_USER_VISITED': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {tra.V.user_visited.name: True},
        {tra.V.user_visited.name: False}),

    'GET_USER_FAMILY': MacroNLG(tra.get_user_family),
    'SET_USER_FAMILY': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {tra.V.user_family.name: True},
        {tra.V.user_family.name: False}),

    'GET_USER_SOLO': MacroNLG(tra.get_user_solo),
    'SET_USER_SOLO': MacroGPTJSON(
        'The speaker was asked whether they have solo traveled. Is the speaker\'s answer likely to be "yes"?',
        {tra.V.user_solo.name: True},
        {tra.V.user_solo.name: False}),

    'GET_USER_FRIENDS': MacroNLG(tra.get_user_friends),
    'SET_USER_FRIENDS': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"? They were just asked whether they travel with friends',
        {tra.V.user_friends.name: True},
        {tra.V.user_friends.name: False}),

    # Evaluation
    'GET_EVAL': MacroNLG(evaluation.get_eval),
    'CONGRATS': evaluation.MacroCongrats(),
    'GPTDETAIL': MacroGPTJSON('Does the user want to know the detail about the feedback? Respond in yes or no.',
                              {evaluation.V.detail.name: "yes"}),
    'GPTEFF': MacroGPTJSON(
        'Considering the user input about the conversation, assign a score: -1 for negative, 0 for neutral, '
        '1 for positive.', {evaluation.V.effectiveness.name: "0"}),
    'GPTSAT': MacroGPTJSON(
        'Considering the user input about the satisfaction of the conversation, assign a score to satisfactiory: -1 '
        'for negative, 0 for neutral, 1 for positive. Do not assign the score to effectiveness.',
        {evaluation.V.satisfactory.name: "0"}),
    'GPTCOR': MacroGPTJSON(
        'Considering the user input about the correctness of the conversation, assign a score to correctness: -1 for'
        ' negative, 0 for neutral, 1 for positive. Do not assign score to effectiveness.',
        {evaluation.V.correctness.name: "0"}),
    'GPTINT': MacroGPTJSON(
        'Considering the user input about the interpretability of the conversation, assign a score to '
        'interpretability: -1 for negative, 0 for neutral, 1 for positive. Do not assign score to effectiveness.',
        {evaluation.V.interpretability.name: "0"}),
    'GPTCOH': MacroGPTJSON(
        'Considering the user input about the coherence of the conversation, assign a score to coherence: -1 for'
        ' negative, 0 for neutral, 1 for positive. Do not assign score to effectiveness.',
        {evaluation.V.coherence.name: "0"}),
    "QUEST": evaluation.MacroNumQuestions(),
    "SPEED": evaluation.MacroAVGToken(),
    "TIC": evaluation.MacroTic(),
    "ACKNOW": evaluation.MacroAcknow(),
    "AWKWARD": evaluation.MacroAwkward(),
    "DETAIL": evaluation.MacroDetail(),

    # BABEL Macros
    'GET_USER_STRLN': MacroNLG(babel.get_user_strln),
    'GET_USER_STRLN_STR': MacroNLG(babel.get_user_strln_str),
    'SET_USER_STRLN': MacroGPTJSON(
        'Does the speaker have a preferred storyline from the movie "Babel"? The options are "Morocco", '
        '"Richard/Susan", "United States/Mexico", and "Japan". Otherwise, choose "N/A".',
        {babel.V.user_strln.name: True, babel.V.user_strln_str.name: "Japan"},
        {babel.V.user_strln.name: False, babel.V.user_strln_str.name: "N/A"}),
    'GET_USER_COMM': MacroNLG(babel.get_user_comm),
    'GET_USER_COMM_STR': MacroNLG(babel.get_user_comm_str),
    'SET_USER_COMM': MacroGPTJSON(
        'What does the speaker think of the way the movie "Babel" explores cultural differences and '
        'communication? Complete the sentence: "The speaker is saying that...".',
        {babel.V.user_comm.name: True, babel.V.user_comm_str.name: "the movie did a good job."},
        {babel.V.user_comm.name: False, babel.V.user_comm_str.name: "N/A"}),
    'GET_USER_ACTOR': MacroNLG(babel.get_user_actor),
    'GET_USER_ACTOR_STR': MacroNLG(babel.get_user_actor_str),
    'SET_USER_ACTOR': MacroGPTJSON(
        'Who is the speaker\'s favorite actor or actress?',
        {babel.V.user_comm.name: True, babel.V.user_comm_str.name: "Brad Pitt"},
        {babel.V.user_comm.name: False, babel.V.user_comm_str.name: "N/A"}),
    'GET_USER_MESSAGE': MacroNLG(babel.get_user_message),
    'GET_USER_MESSAGE_STR': MacroNLG(babel.get_user_message_str),
    'SET_USER_MESSAGE': MacroGPTJSON(
        'Summarize the speaker\'s opinion on this questions: "What message about human connection do you think '
        'the filmmakers were trying to convey in "Babel"?"',
        {babel.V.user_message.name: True, babel.V.user_message_str.name: "I think it emphasized our shared humanity."},
        {babel.V.user_message.name: False, babel.V.user_message_str.name: "N/A"}),
    'GET_USER_REASON': MacroNLG(babel.get_user_reason),
    'GET_USER_REASON_STR': MacroNLG(babel.get_user_reason_str),
    'SET_USER_REASON': MacroGPTJSON(
        'Why does the speaker not like the movie? The options are "storyline", "casting", '
        '"direction", "visuals", and "soundtrack".',
        {babel.V.user_reason.name: True, babel.V.user_reason_str.name: "because the storyline is bad."},
        {babel.V.user_reason.name: False, babel.V.user_reason_str.name: "N/A"}),
    'GET_USER_INTEREST': MacroNLG(babel.get_user_interest),
    'SET_USER_INTEREST': MacroGPTJSON(
        'Is the speaker\'s answer likely to be "yes"?',
        {babel.V.user_interest.name: True},
        {babel.V.user_interest.name: False}),

    # Text Macros
    'THINK_MOVIE': babel.MacroThinkMovie(),
    'LIKE_MOVIE': babel.MacroLikeMovie(),
    'CULTURAL': babel.MacroCultural(),
    'ACTOR': babel.MacroActor(),
    'FILMMAKERS': babel.MacroFilmmakers(),
    'HUMANITY': babel.MacroHumanity(),
    'PERSONALLY': babel.MacroPersonally(),
    'ALSO': babel.MacroAlso(),
    'PERFORMANCES': babel.MacroPerformances(),
    'COMMUNICATION': babel.MacroCommunication(),
    'OPINION': babel.MacroOpinion(),
    'CONTINUE': babel.MacroContinue(),
    'AMAZING': babel.MacroAmazing(),
    'SHARING': babel.MacroSharing(),
    'THANKYOU': babel.MacroThankYou(),

    # Health & Food
    'HEALTHY': hlth.MacroHealthy(),
    'PHY': hlth.MacroPhy(),
    'SET_LIFESTYLE': MacroGPTJSON(
        'Is the speaker indicating that they have a healthy lifestyle, true or false?',
        {hlth.V.healthy.name: True},
        {hlth.V.healthy.name: False}
    ),
    'GET_LIFESTYLE': MacroNLG(hlth.get_lifestyle),
    'SET_EXERCISE': MacroGPTJSON(
        'the speaker is indicating that they exercise, true or false?',
        {hlth.V.exercise.name: True},
        {hlth.V.exercise.name: False}
    ),
    'GET_EXERCISE': MacroNLG(hlth.get_exercise),
    'EXP': hlth.MacroExP(),
    'EXN': hlth.MacroExN(),
    'SET_BUDDY': MacroGPTJSON(
        'Is the speaker indicating that they have friends, true or false?',
        {hlth.V.buddy.name: True},
        {hlth.V.buddy.name: False}
    ),
    'GET_BUDDY': MacroNLG(hlth.get_buddy),
    'BUP': hlth.MacroBuP(),
    'BUN': hlth.MacroBuN(),
    'SET_BALANCE': MacroGPTJSON(
        'What is the user indicating that they need to work on?',
        {hlth.V.balance.name: "managing homework"},
        {hlth.V.balance.name: "nothing"}
    ),
    'BALANCE': hlth.MacroBalance(),
    'GET_BALANCE': hlth.MacroGetBalance(),
    'BAL_FOOD': hlth.MacroBalFood(),
    'SET_FOOD': MacroGPTJSON(
        'What is the user\'s favorite place to eat?',
        {hlth.V.food.name: "chipotle"},
        {hlth.V.food.name: "none"}
    ),
    'FOOD': hlth.MacroFood(),
    'GET_FOOD': hlth.MacroGetFood(),
    'SET_EATING': MacroGPTJSON(
        'Is the speaker indicating that they have a healthy diet, true or false?',
        {hlth.V.healthy_diet.name: True},
        {hlth.V.healthy_diet.name: False}
    ),
    'GET_EATING': MacroNLG(hlth.get_eating),
    'EATP': hlth.MacroEATP(),
    'EATN': hlth.MacroEATN(),
    'VEGMOVIE': hlth.MacroVegMovie(),
    'FOOD2MOVIE': hlth.MacroFoodToMovie
}


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    # 'C:/Users/Harry/PycharmProjects/SpeakEasy/src'
    # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy/src
    path = f'/Users/maxbagga/Desktop/Emory 8th Semester/CS 329/SpeakEasy2/{varfile}'
    if os.path.isfile(path):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
        df.vars()['ANSWERS'] = ""
        df.vars()['UTTERANCE'] = 0
        df.vars()['BOTLOG'] = ""
        df.vars()['SPOKENTIME'] = 0
    df.run()
    save(df, varfile)


if __name__ == '__main__':
    # C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt
    # /Users/maxbagga/Desktop/Emory 8th Semester/CS 329/chat_gpt_api_key.txt
    openai.api_key_path = '/Users/maxbagga/Desktop/Emory 8th Semester/CS 329/chat_gpt_api_key.txt'
    load(visits(), 'src/userLog.pkl')