import pyttsx3
import speech_recognition as sr
import sounddevice as sd

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

    sample_rate = 16000
    recording_seconds = 5

    print("Speak now (recording for 5 seconds)...")
    recording = sd.rec(
        int(recording_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    audio = sr.AudioData(recording.tobytes(), sample_rate, 2)

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
