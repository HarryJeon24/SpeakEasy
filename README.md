# SpeakEasy
This repository contains a Python script for SpeakEasy chatbot application. 

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

## Prerequisites

1. Python 3.6 or higher installed on your computer.

2. Install the required Python libraries by entering the following commands in your terminal:

```terminal
pip install openai emora-stdm pyaudio gtts mutagen
```
3. For Mac, if an error along the lines of "Could not build wheels for pyaudio, since package 'wheel' is not installed" is given when installing PyAudio, please perform steps 1-5 in the solution from this article: https://stackoverflow.com/questions/73268630/error-could-not-build-wheels-for-pyaudio-which-is-required-to-install-pyprojec.

4. While the Mac installation maybe a tad more tedious, the interface is nicer and easier to work with than the Windows one.

## Setup

1. Clone this repository to your local machine.

2. Open the `main.py` and `evaluation.py` files and replace the path in the following lines of code:

```python
openai.api_key_path = 'path/to/your/chat_gpt_api_key.txt'
```

```python
SAVE_DIR = 'path/to/your/directory/to/save/USERINPUT.wav'
```

```python
audio_file = open('path/to/your/directory/to/USERINPUT.wav')
```

3.  Open the `main.py` and replace the path in the following line of code with the appropriate path to the `userLog.pkl` file on your computer:

```python
path = 'path/to/your/directory/to/save/userLog.pkl'
```

```python
load(df, 'path/to/your/userLog.pkl')
```

4. For Windows, open the `main.py` and `evaluation.py` files and comment out the following line of code:

```python
os.system("afplay bot_output.mp3") # Mac
```

Then, uncomment the following lines of code:

```python
 # os.system("start bot_output.mp3")  # Windows
 # time.sleep(MP3("bot_output.mp3").info.length)
```

5. For Mac, no changes need to be made to the code. However, the installation of packages may be difficult. If this is the case, please try with a Windows device. 

## Running the Application

1. Open a terminal or command prompt, navigate to the directory containing the `main.py` file, and run the following command:

```
python main.py
```

2. The application will start and prompt you to record your audio input. Press Enter to stop the recording.

3. The application will converse with you and save your name and feedback in the `userLog.pkl` file.

## Troubleshooting

If you encounter issues while running the application, make sure that you have correctly installed all the required libraries, set up the API key, and provided the correct paths to the API key and `userLog.pkl` files.
