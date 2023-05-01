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

3.  Open the `main.py` and replace the path in the following line of code with the appropriate path to the `userlog.pkl` file on your computer:

```python
path = 'path/to/your/directory/to/save/userlog.pkl'
```

```python
load(df, 'path/to/your/userlog.pkl')
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

5. For Mac, to be filled...

## Running the Application

1. Open a terminal or command prompt, navigate to the directory containing the `main.py` file, and run the following command:

```
python main.py
```

2. The application will start and prompt you to record your audio input. Press Enter to stop the recording.

3. The application will converse with you and save your name and feedback in the `userlog.pkl` file.

## Troubleshooting

If you encounter issues while running the application, make sure that you have correctly installed all the required libraries, set up the API key, and provided the correct paths to the API key and `userlog.pkl` files.
