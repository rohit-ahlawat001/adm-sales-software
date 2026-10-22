import pyttsx3
import speech_recognition as sr

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 190)
    engine.say(text)
    engine.runAndWait()


def listen():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1

    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

    try:
        command = recognizer.recognize_google(audio, language='en-US')
        print(f"Client said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return ""


text = listen()
if text:
    speak(text)
