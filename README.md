# SpeakEasy
This repository contains a Python script for SpeakEasy chatbot application. 

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

## Prerequisites

1. Python 3.6 or higher installed on your computer.

2. Install the required Python libraries.

## Setup

1. Clone this repository to your local machine.

2. Open the `main.py` and 'evaluation.py' files and replace the path in the following linex of code:

```python
openai.api_key_path = 'path/to/your/chat_gpt_api_key.txt'
```

```python
SAVE_DIR = 'path/to/your/directory/to/save/USERINPUT.wav'
```

```python
audio_file = open('path/to/your/directory/to/USERINPUT.wav')
```

3. Replace the path in the following line of code with the appropriate path to the `visits.pkl` file on your computer:

```python
load(df, 'path/to/your/visits.pkl')
```

4. For Windows, to be filled...

5. For Mac, to be filled...

## Running the Application

1. Open a terminal or command prompt, navigate to the directory containing the `main.py` file, and run the following command:

```
python main.py
```

2. The application will start and prompt you to record your audio input. Press Enter to stop the recording.

3. The application will transcribe your speech, respond using text-to-speech, and store the transcriptions in the `visits.pkl` file.

## Troubleshooting

If you encounter issues while running the application, make sure that you have correctly installed all the required libraries, set up the API key, and provided the correct paths to the API key and `visits.pkl` files.
