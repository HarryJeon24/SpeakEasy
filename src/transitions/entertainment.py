from enum import Enum
from typing import Dict, Any, List

import openai
from emora_stdm import DialogueFlow, Macro, Ngrams

from src import utils

import requests
import random
from src.transitions.evaluation import audio

class V(Enum):
    call_names = 0  # str
    favorite_movie = 1  # dict
    favorite_movie_bool = 2  # bool
    favorite_movie_genre = 3  # str
    favorite_movie_genre_bool = 4  # bool
    favorite_movie_theme = 5  # str
    favorite_movie_theme_bool = 6  # bool
    favorite_movie_character = 7  # str
    favorite_movie_character_bool = 8  # bool
    favorite_song = 9  # dict
    favorite_song_bool = 10  # bool
    music_liked_aspect = 11  # str
    music_liked_aspect_bool = 12  # bool
    music_genre_preference = 13  # str
    music_genre_preference_bool = 14  # bool
    music_theme_preference = 15  # str
    music_theme_preference_bool = 16  # bool
    music_artist_preference = 17  # str
    music_artist_preference_bool = 18  # bool
    user_answer = 19  # bool


class Macrotalkmovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Let\'s talk about movies."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macrotalkmusic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Let\'s talk about music."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macrofavmovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "What is your favorite movie?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macrofavmusic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "What is your favorite song?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroRecommendMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        api_key = 'e99e2a85cdf530f4446d8f3654b7c853'
        response = requests.get(f'https://api.themoviedb.org/3/discover/movie?api_key={api_key}')
        data = response.json()
        results = data['results']
        user_name = vars.get('NAME')
        recommendations = vars.get(user_name, {'recommendations': []}).get('recommendations', [])
        recommended_titles = [r['track_name'] for r in recommendations]
        movie = None
        while movie is None or movie['title'] in recommended_titles:
            movie = random.choice(results)
        title = movie['title']
        movie_id = movie['id']
        overview_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US')
        overview_data = overview_response.json()
        overview = overview_data['overview']
        recommendation = {
            'title': title,
            'overview': overview,
        }
        if user_name in vars:
            vars[user_name]['recommendations'].append(recommendation)
        vars['favorite_movie'] = recommendation

        # audio
        output = "How about " + title + "? It is about " + overview
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)

        return output


class MacroGetMovieOverview(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        recommendation = vars['favorite_movie']
        overview = recommendation['overview']
        return overview


class MacroRecommendSong(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        auth_response = requests.post("https://accounts.spotify.com/api/token", {
            "grant_type": "client_credentials",
            "client_id": "7dba0e6b311e4f469f9d4bec2b69f375",
            "client_secret": "4c9347f3494645cb9d230a704474c235"
        })
        access_token = auth_response.json()['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        genres = ['pop', 'rock', 'hip hop', 'country', 'jazz', 'classical']
        genre_id = genres[random.randint(0, 5)]
        response = requests.get("https://api.spotify.com/v1/search", headers=headers,
                                params={"q": genre_id, "type": "track", "limit": "1"})
        response_data = response.json()
        track_data = response_data['tracks']['items'][0]
        track_name = track_data['name']
        artist_name = track_data.get('artists', [{}])[0].get('name', '')
        user_name = vars.get('NAME')
        recommendations = vars.get(user_name, {'recommendations': []}).get('recommendations', [])
        recommended_tracks = [r['track_name'] for r in recommendations]
        while track_name in recommended_tracks:
            genre_id = genres[random.randint(0, 5)]
            response = requests.get("https://api.spotify.com/v1/search", headers=headers,
                                    params={"q": genre_id, "type": "track", "limit": "1"})
            response_data = response.json()
            track_data = response_data['tracks']['items'][0]
            track_name = track_data['name']
            artist_name = track_data.get('artists', [{}])[0].get('name', '')
        recommendation = {
            'track_name': track_name,
            'artist_name': artist_name,
        }
        if user_name in vars:
            vars[user_name]['recommendations'].append(recommendation)
        vars['favorite_song'] = recommendation

        # audio
        output = "How about " + track_name + " by " + artist_name + "?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)

        return output


class MacroGetSongArtist(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        recommendation = vars['favorite_song']
        artist_name = recommendation['artist_name']
        return artist_name


class MacroGetFavMovie(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Oh, " + str(vars[V.favorite_movie.name]) + " sounds interesting! What genre is it?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class Macroget_favorite_movie_bool(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        return vars[V.favorite_movie_bool.name]


class MacroGetFavMovieG(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Oh, I also like " + str(vars[V.favorite_movie_genre.name]) + " movies. Can you tell me about the" \
                                                                               " theme of your favorite movie?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_movie_genre_preference_bool(vars: Dict[str, Any]):
    return vars[V.favorite_movie_genre_bool.name]


class MacroGetFavMovieT(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "So, the theme of your favorite movie is " \
                 + str(vars[V.favorite_movie_theme.name]) + " Who is your favorite character in that movie?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_movie_theme_preference_bool(vars: Dict[str, Any]):
    return vars[V.favorite_movie_theme_bool.name]


class MacroGetFavMovieC(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok! Can you tell me more about " + str(vars[V.favorite_movie_character.name]) + "?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_movie_character_preference_bool(vars: Dict[str, Any]):
    return vars[V.favorite_movie_character_bool.name]


class MacroThankRec(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Thank you for sharing! Now, I want to recommend you a movie!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroWhoC(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok! Who is your favorite character in the movie?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroWhatT(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok! Can you tell me about the theme of your favorite movie?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroOK(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroGetFavMusic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Oh, " + str(vars[V.favorite_song.name]) + " is such a good song. What do you like about it?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_favorite_music_bool(vars: Dict[str, Any]):
    return vars[V.favorite_song_bool.name]


class MacroGetMusicA(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Interesting! I can see why you like " + str(vars[V.favorite_song.name]) +\
                 " in the song. What genre is " + str(vars[V.favorite_song.name]) + "."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_music_liked_aspect_bool(vars: Dict[str, Any]):
    return vars.get(V.music_liked_aspect_bool.name)


class MacroGetMusicG(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Oh, I also enjoy " + str(vars.get(V.music_genre_preference.name)) +\
                 " music. Can you tell me more about the theme of " + str(vars[V.favorite_song.name]) + "?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_music_genre_preference_bool(vars: Dict[str, Any]):
    return vars.get(V.music_genre_preference_bool.name)


class MacroGetMusicT(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "That\'s really cool. So, the theme of " + str(vars[V.favorite_song.name]) +\
                 " is " + str(vars.get(V.music_theme_preference.name)) + \
                 ". Who is your favorite artist for that type of music?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_music_theme_preference_bool(vars: Dict[str, Any]):
    return vars.get(V.music_theme_preference_bool.name)


class MacroGetMusicAr(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Great choice! I love " + str(vars.get(V.music_artist_preference.name)) +\
                 " too. Can you tell me more about their music?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_music_artist_preference_bool(vars: Dict[str, Any]):
    return vars.get(V.music_artist_preference_bool.name)


class MacroThankRec2(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Thank you for sharing! Now, I want to recommend you a song!"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroWhoFav(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Who is your favorite artist for that type of music?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroMoreT(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok! Can you tell me more about the theme of " + str(vars[V.favorite_song.name]) + "?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroWhatG(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "What genre is " + str(vars[V.favorite_song.name]) + " from?"
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


class MacroAnother(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        output = "Ok, then let\'s find another one."
        vars['BOTLOG'] = vars['BOTLOG'] + output
        audio(output)
        return output


def get_call_name(vars: Dict[str, Any]):
    ls = vars[V.call_names.name]
    return ls[random.randrange(len(ls))]


class Macroget_user_answer(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        return vars[V.user_answer.name]


transitions = {
    'state': 'start',
    '`Hello, what is your name?`': {
        '#SET_CALL_NAMES': {
            '`Nice to meet you,` #GET_CALL_NAME `.`': 'select_topic'
        }
    }
}

transitions_select_topic = {
    'state': 'select_topic',
    '#TALK_MOVIE': 'movie',
    '#TALK_MUSIC': 'music',
}

transitions_movie = {
    'state': 'movie',
    '#TALK_MOVIE #FAV_MOVIE #USERINPUT #SET_MOVIE_PREFERENCE': {
        '#GET_MOVIE_PREFERENCE_BOOL': {
            '#GET_MOVIE_PREFERENCE #USERINPUT #SET_MOVIE_GENRE_PREFERENCE': {
                '#GET_MOVIE_GENRE_PREFERENCE_BOOL': {
                    '#GET_MOVIE_GENRE_PREFERENCE #USERINPUT #SET_MOVIE_THEME_PREFERENCE': {
                        'state': 'movie_theme',
                        '#GET_MOVIE_THEME_PREFERENCE_BOOL': {
                            '#GET_MOVIE_THEME_PREFERENCE #USERINPUT #SET_MOVIE_CHARACTER_PREFERENCE': {
                                'state': 'movie_character',
                                '#GET_MOVIE_CHARACTER_PREFERENCE_BOOL': {
                                    '#GET_MOVIE_CHARACTER_PREFERENCE #USERINPUT': {
                                        'error': {
                                            '#THANK_REC': 'movie_rec',
                                        }
                                    }
                                },
                                'error': {
                                    '#THANK_REC': 'movie_rec'
                                }
                            }
                        },
                        'error': {
                            '#WHO_FAV_C #USERINPUT #SET_MOVIE_CHARACTER_PREFERENCE': 'movie_character'
                        }
                    }
                },
                'error': {
                    '#WHAT_FAV_T #USERINPUT #SET_MOVIE_THEME_PREFERENCE': 'movie_theme'
                }
            }
        },
        'error': {
            '#OK': 'music'
        }
    }
}

transitions_movie_rec = {
    'state': 'movie_rec',
    '#GET_MOVIE #USERINPUT #SET_USER_ANSWER': {
        '#GET_USER_ANSWER': {
            '#OK': 'music'
        },
        'error': {
            '#ANOTHER': 'movie_rec'
        }
    }
}

transitions_music = {
    'state': 'music',
    '#TALK_MUSIC #FAV_SONG #USERINPUT #SET_MUSIC_PREFERENCE': {
        '#GET_MUSIC_PREFERENCE_BOOL': {
            '#GET_MUSIC_PREFERENCE #USERINPUT #SET_MUSIC_LIKED_ASPECT': {
                '#GET_MUSIC_LIKED_ASPECT_BOOL': {
                    '#GET_MUSIC_LIKED_ASPECT #USERINPUT #SET_MUSIC_GENRE_PREFERENCE': {
                        'state': 'genre',
                        '#GET_MUSIC_GENRE_PREFERENCE_BOOL': {
                            '#GET_MUSIC_GENRE_PREFERENCE #USERINPUT #SET_MUSIC_THEME_PREFERENCE': {
                                'state': 'music_pref',
                                '#GET_MUSIC_THEME_PREFERENCE_BOOL': {
                                    '#GET_MUSIC_THEME_PREFERENCE #USERINPUT #SET_MUSIC_ARTIST_PREFERENCE': {
                                        'state': 'artist',
                                        '#GET_MUSIC_ARTIST_PREFERENCE_BOOL': {
                                            '#GET_MUSIC_ARTIST_PREFERENCE #USERINPUT': {
                                                'error': {
                                                    '#THANK_REC2': 'music_rec',
                                                }
                                            }
                                        },
                                        'error': {
                                            '#THANK_REC2': 'music_rec'
                                        }
                                    }
                                },
                                'error': {
                                    '#WHO_FAV #USERINPUT #SET_MUSIC_ARTIST_PREFERENCE': 'artist'
                                }
                            }
                        },
                        'error': {
                            '#MORE_T #USERINPUT #SET_MUSIC_THEME_PREFERENCE': 'music_pref'
                        }
                    }
                },
                'error': {
                    '#WHAT_G #USERINPUT #SET_MUSIC_GENRE_PREFERENCE': 'genre'
                }
            }
        },
        'error': {
            '#OK': 'travel'
        }
    }
}

transitions_music_rec = {
    'state': 'music_rec',
    '#GET_MOVIE #USERINPUT #SET_USER_ANSWER': {
        '#GET_USER_ANSWER': {
            '#OK': 'travel'
        },
        'error': {
            '#ANOTHER': 'music_rec'
        }
    }
}

# macros = {
#     'GET_CALL_NAME': MacroNLG(get_call_name),
#     'SET_CALL_NAMES': MacroGPTJSON(
#         'How does the speaker want to be called?',
#         {V.call_names.name: ["Mike", "Michael"]}),
#     'GET_MOVIE_PREFERENCE': MacroNLG(get_favorite_movie),
#     'GET_MOVIE_PREFERENCE_BOOL': MacroNLG(get_favorite_movie_bool),
#     'SET_MOVIE_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s favorite movie?',
#         {V.favorite_movie.name: "Forrest Gump", V.favorite_movie_bool.name: True},
#         {V.favorite_movie.name: "none", V.favorite_movie_bool.name: False}
#     ),
#     'GET_MOVIE_GENRE_PREFERENCE': MacroNLG(get_movie_genre_preference),
#     'GET_MOVIE_GENRE_PREFERENCE_BOOL': MacroNLG(get_movie_genre_preference_bool),
#     'SET_MOVIE_GENRE_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s preferred movie genre?',
#         {V.favorite_movie_genre.name: "Action", V.favorite_movie_genre_bool.name: True},
#         {V.favorite_movie_genre.name: "none", V.favorite_movie_genre_bool.name: False}
#     ),
#     'GET_MOVIE_THEME_PREFERENCE': MacroNLG(get_movie_theme_preference),
#     'GET_MOVIE_THEME_PREFERENCE_BOOL': MacroNLG(get_movie_theme_preference_bool),
#     'SET_MOVIE_THEME_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s movie about? Summarize it in a short sentence or two.',
#         {V.favorite_movie_theme.name: "It is about a dog and a child who love each other.",
#          V.favorite_movie_theme_bool.name: True},
#         {V.favorite_movie_theme.name: "none", V.favorite_movie_theme_bool.name: False}
#     ),
#     'GET_MOVIE_CHARACTER_PREFERENCE': MacroNLG(get_movie_character_preference),
#     'GET_MOVIE_CHARACTER_PREFERENCE_BOOL': MacroNLG(get_movie_character_preference_bool),
#     'SET_MOVIE_CHARACTER_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s favorite character?',
#         {V.favorite_movie_character.name: "Hermione Granger", V.favorite_movie_character_bool.name: True},
#         {V.favorite_movie_character.name: "none", V.favorite_movie_character_bool.name: False}
#     ),
#     'GET_MUSIC_PREFERENCE': MacroNLG(get_favorite_music),
#     'GET_MUSIC_PREFERENCE_BOOL': MacroNLG(get_favorite_music_bool),
#     'SET_MUSIC_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s favorite music/song?',
#         {V.favorite_song.name: "Love Story", V.favorite_song_bool.name: True},
#         {V.favorite_song.name: "none", V.favorite_song_bool.name: False}
#     ),
#     'GET_MUSIC_LIKED_ASPECT': MacroNLG(get_music_liked_aspect),
#     'GET_MUSIC_LIKED_ASPECT_BOOL': MacroNLG(get_music_liked_aspect_bool),
#     'SET_MUSIC_LIKED_ASPECT': MacroGPTJSON(
#         'What does the speaker like about the song?',
#         {V.music_liked_aspect.name: "the melody", V.music_liked_aspect_bool.name: True},
#         {V.music_liked_aspect.name: "none", V.music_liked_aspect_bool.name: False}
#     ),
#     'GET_MUSIC_GENRE_PREFERENCE': MacroNLG(get_music_genre_preference),
#     'GET_MUSIC_GENRE_PREFERENCE_BOOL': MacroNLG(get_music_genre_preference_bool),
#     'SET_MUSIC_GENRE_PREFERENCE': MacroGPTJSON(
#         'What is the speaker\'s favorite genre of music?',
#         {V.music_genre_preference.name: "pop", V.music_genre_preference_bool.name: True},
#         {V.music_genre_preference.name: "none", V.music_genre_preference_bool.name: False}
#     ),
#     'GET_MUSIC_THEME_PREFERENCE': MacroNLG(get_music_theme_preference),
#     'GET_MUSIC_THEME_PREFERENCE_BOOL': MacroNLG(get_music_theme_preference_bool),
#     'SET_MUSIC_THEME_PREFERENCE': MacroGPTJSON(
#         'What is the theme of the speaker\'s favorite song?',
#         {V.music_theme_preference.name: "love", V.music_theme_preference_bool.name: True},
#         {V.music_theme_preference.name: "none", V.music_theme_preference_bool.name: False}
#     ),
#     'GET_MUSIC_ARTIST_PREFERENCE': MacroNLG(get_music_artist_preference),
#     'GET_MUSIC_ARTIST_PREFERENCE_BOOL': MacroNLG(get_music_artist_preference_bool),
#     'SET_MUSIC_ARTIST_PREFERENCE': MacroGPTJSON(
#         'Who is the speaker\'s favorite artist for that genre?',
#         {V.music_artist_preference.name: "Taylor Swift", V.music_artist_preference_bool.name: True},
#         {V.music_artist_preference.name: "none", V.music_artist_preference_bool.name: False}
#     ),
#     'GET_USER_ANSWER': MacroNLG(get_user_answer),
#     'SET_USER_ANSWER': MacroGPTJSON(
#         'Does the speaker seem satisfied?',
#         {V.music_artist_preference.name: True},
#         {V.music_artist_preference.name: False}
#     ),
#     'GET_MOVIE': MacroRecommendMovie(),
#     'GET_SONG': MacroRecommendSong(),
#     'SONG_GET_ARTIST': MacroGetSongArtist(),
#     'MOVIE_GET_OVERVIEW': MacroGetMovieOverview(),
# }

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_select_topic)
df.load_transitions(transitions_movie)
df.load_transitions(transitions_movie_rec)
df.load_transitions(transitions_music)
df.load_transitions(transitions_music_rec)
#df.add_macros(macros)


if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
