from enum import Enum
from typing import Dict, Any, List

import openai
from emora_stdm import DialogueFlow, Macro, Ngrams

from src import utils
from src.utils import MacroGPTJSON, MacroNLG

import requests
import random


class V(Enum):
    call_names = 0  # str
    favorite_movie = 1  # dict
    favorite_movie_genre = 2  # str
    favorite_movie_theme = 3  # str
    favorite_movie_character = 4  # str
    favorite_song = 5  # dict
    music_liked_aspect = 6  # str
    music_genre_preference = 7  # str
    music_theme_preference = 8  # str
    music_artist_preference = 9  # str


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
        return title


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
        return track_name


class MacroGetSongArtist(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        recommendation = vars['favorite_song']
        artist_name = recommendation['artist_name']
        return artist_name


def main() -> DialogueFlow:
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
        '#GATE `Let\'s talk about movies.`': 'movie',
        '#GATE `Let\'s talk about music.`': 'music',
        '`That\'s all I can talk about.`': {
            'state': 'end',
            'score': 0.1
        }
    }

    transitions_movie = {
        'state': 'movie',
        '`Do you have a favorite movie?`': {
            '[{yes, of course, sure, definitely}]': {
                '`Amazing! What is your favorite movie?`': {
                    '#SET_MOVIE_PREFERENCE': {
                        'state': 'movie_talk',
                        '`Oh, ` #GET_MOVIE_PREFERENCE `sounds interesting! What genre is it?`': {
                            '#SET_MOVIE_GENRE_PREFERENCE': {
                                '`Oh, I also like` #GET_MOVIE_GENRE_PREFERENCE `movies. Can you tell me about the '
                                'theme of your favorite movie?`': {
                                    '#SET_MOVIE_THEME_PREFERENCE': {
                                        '`Interesting! So, the theme of your favorite movie is` '
                                        '#GET_MOVIE_THEME_PREFERENCE ` Who is your favorite character in that '
                                        'movie?`': {
                                            '#SET_MOVIE_CHARACTER_PREFERENCE': {
                                                '`Ok! Can you tell me more about` #GET_MOVIE_CHARACTER_PREFERENCE ` ?`': {
                                                    'error': {
                                                        '`Thank you for sharing! Now, I want to recommend you a movie!`': 'movie_rec',
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'error': {
                '`Oh, let\'s find you a movie then!`': 'movie_rec'
            }
        }
    }

    transitions_movie_rec = {
        'state': 'movie_rec',
        '`How about "` #GET_MOVIE `"?`': {
            '<{another, already}, {film, movie}>': 'movie_rec',
            '[{theme, topic, about, summary, synopsis}]': {
                '`Here is a brief overview: `#MOVIE_GET_OVERVIEW': {
                    '<{another, already}, {film, movie}>': 'movie_rec',
                    'error': {
                        '`Enjoy!`': 'select_topic'
                    }
                }
            },
            '[{great, thanks, ok, perfect, amazing}]': {
                '`Enjoy!`': 'select_topic'
            },
            'error': {
                '`Sorry, I don\'t understand that. Do you want another movie recommendation?`': {
                    '[{yes, ok, sure}]': 'movie_rec',
                    'error': {
                        '`Ok!`': 'select_topic'
                    }
                }
            }
        }
    }

    transitions_music = {
        'state': 'music',
        '`Do you have a favorite song?`': {
            '[{yes, of course, sure, definitely}]': {
                '`Amazing! What is your favorite song?`': {
                    '#SET_MUSIC_PREFERENCE': {
                        'state': 'music_talk',
                        '`Oh, ` #GET_MUSIC_PREFERENCE `is such a good song. What do you like about it?`': {
                            '#SET_MUSIC_LIKED_ASPECT': {
                                '`Interesting! I can see why you like ` #GET_MUSIC_LIKED_ASPECT `in the song. '
                                'What genre is` #GET_MUSIC_PREFERENCE `from?`': {
                                    '#SET_MUSIC_GENRE_PREFERENCE': {
                                        '`Oh, I also enjoy ` #GET_MUSIC_GENRE_PREFERENCE `music. Can you tell me '
                                        'more about the theme of` #GET_MUSIC_PREFERENCE `?`': {
                                            '#SET_MUSIC_THEME_PREFERENCE': {
                                                '`That\'s really cool. So, the theme of` #GET_MUSIC_PREFERENCE `is` '
                                                '#GET_MUSIC_THEME_PREFERENCE `. Who is your favorite artist for '
                                                'that genre?`': {
                                                    '#SET_MUSIC_ARTIST_PREFERENCE': {
                                                        '`Great choice! I love ` #GET_MUSIC_ARTIST_PREFERENCE `too. '
                                                        'Can you tell me more about their music?`': {
                                                            'error': {
                                                                '`Thank you for sharing! Now, I want to recommend you a song!`': 'music_rec',
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'error': {
                '`Oh, let\'s find you a recommendation then!`': 'music_rec'
            }
        }
    }

    transitions_music_rec = {
        'state': 'music_rec',
        '`How about "` #GET_SONG `"?`': {
            '<{another, already}, {song, music}>': 'music_rec',
            '[{artist, singer, who}]': {
                '`The song\'s artist is `#SONG_GET_ARTIST`.`': {
                    '<{another, already}, {song, music}>': 'music_rec',
                    'error': {
                        '`Enjoy!`': 'select_topic'
                    }
                }
            },
            '[{great, thanks, ok, perfect, amazing}]': {
                '`Enjoy!`': 'select_topic'
            },
            'error': {
                '`Sorry, I don\'t understand that. Do you want another music recommendation?`': {
                    '[{yes, ok, sure}]': 'music_rec',
                    'error': {
                        '`Ok!`': 'select_topic'
                    }
                }
            }
        }
    }

    macros = {
        'GET_CALL_NAME': MacroNLG(get_call_name),
        'SET_CALL_NAMES': MacroGPTJSON(
            'How does the speaker want to be called?',
            {V.call_names.name: ["Mike", "Michael"]}),
        'GET_MOVIE_PREFERENCE': MacroNLG(get_favorite_movie),
        'SET_MOVIE_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s favorite movie?',
            {V.favorite_movie.name: "Forrest Gump"},
            {V.favorite_movie.name: "that movie"}
        ),
        'GET_MOVIE_GENRE_PREFERENCE': MacroNLG(get_movie_genre_preference),
        'SET_MOVIE_GENRE_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s preferred movie genre?',
            {V.favorite_movie_genre.name: "Action"},
            {V.favorite_movie_genre.name: "that genre"}
        ),
        'GET_MOVIE_THEME_PREFERENCE': MacroNLG(get_movie_theme_preference),
        'SET_MOVIE_THEME_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s movie about? Summarize it in a short sentence or two.',
            {V.favorite_movie_theme.name: "It is about a dog and a child who love each other."},
            {V.favorite_movie_theme.name: "something"}
        ),
        'GET_MOVIE_CHARACTER_PREFERENCE': MacroNLG(get_movie_character_preference),
        'SET_MOVIE_CHARACTER_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s favorite character?',
            {V.favorite_movie_character.name: "Hermione Granger"},
            {V.favorite_movie_character.name: "that character"}
        ),
        'GET_MUSIC_PREFERENCE': MacroNLG(get_favorite_music),
        'SET_MUSIC_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s favorite music/song?',
            {V.favorite_song.name: "Love Story"},
            {V.favorite_song.name: "N/A"}
        ),
        'GET_MUSIC_LIKED_ASPECT': MacroNLG(get_music_liked_aspect),
        'SET_MUSIC_LIKED_ASPECT': MacroGPTJSON(
            'What does the speaker like about the song?',
            {V.music_liked_aspect.name: "the melody"},
            {V.music_liked_aspect.name: "N/A"}
        ),
        'GET_MUSIC_GENRE_PREFERENCE': MacroNLG(get_music_genre_preference),
        'SET_MUSIC_GENRE_PREFERENCE': MacroGPTJSON(
            'What is the speaker\'s favorite genre of music?',
            {V.music_genre_preference.name: "pop"},
            {V.music_genre_preference.name: "N/A"}
        ),
        'GET_MUSIC_THEME_PREFERENCE': MacroNLG(get_music_theme_preference),
        'SET_MUSIC_THEME_PREFERENCE': MacroGPTJSON(
            'What is the theme of the speaker\'s favorite song?',
            {V.music_theme_preference.name: "love"},
            {V.music_theme_preference.name: "N/A"}
        ),
        'GET_MUSIC_ARTIST_PREFERENCE': MacroNLG(get_music_artist_preference),
        'SET_MUSIC_ARTIST_PREFERENCE': MacroGPTJSON(
            'Who is the speaker\'s favorite artist for that genre?',
            {V.music_artist_preference.name: "Taylor Swift"},
            {V.music_artist_preference.name: "N/A"}
        ),
        'GET_MOVIE': MacroRecommendMovie(),
        'GET_SONG': MacroRecommendSong(),
        'SONG_GET_ARTIST': MacroGetSongArtist(),
        'MOVIE_GET_OVERVIEW': MacroGetMovieOverview(),
    }

    df = DialogueFlow('start', end_state='end')
    df.load_transitions(transitions)
    df.load_transitions(transitions_select_topic)
    df.load_transitions(transitions_movie)
    df.load_transitions(transitions_movie_rec)
    df.load_transitions(transitions_music)
    df.load_transitions(transitions_music_rec)
    df.add_macros(macros)
    return df


def get_favorite_movie(vars: Dict[str, Any]):
    return vars[V.favorite_movie.name]


def get_movie_genre_preference(vars: Dict[str, Any]):
    return vars[V.favorite_movie_genre.name]


def get_movie_theme_preference(vars: Dict[str, Any]):
    return vars[V.favorite_movie_theme.name]


def get_movie_character_preference(vars: Dict[str, Any]):
    return vars[V.favorite_movie_character.name]


def get_favorite_music(vars: Dict[str, Any]):
    return vars[V.favorite_song.name]


def get_music_liked_aspect(vars: Dict[str, Any]):
    return vars.get(V.music_liked_aspect.name)


def get_music_genre_preference(vars: Dict[str, Any]):
    return vars.get(V.music_genre_preference.name)


def get_music_theme_preference(vars: Dict[str, Any]):
    return vars.get(V.music_theme_preference.name)


def get_music_artist_preference(vars: Dict[str, Any]):
    return vars.get(V.music_artist_preference.name)


def get_call_name(vars: Dict[str, Any]):
    ls = vars[V.call_names.name]
    return ls[random.randrange(len(ls))]


if __name__ == '__main__':
    openai.api_key_path = utils.OPENAI_API_KEY_PATH
    main().run()
