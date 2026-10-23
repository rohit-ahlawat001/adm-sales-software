import pyttsx3
import speech_recognition as sr
import sounddevice as sd


def speak(text):
    """Read text aloud so callers can give the client audible feedback."""
    engine = pyttsx3.init()

    # Prefer the second installed voice when available to keep the assistant's
    # output consistent on machines that expose multiple system voices.
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)

    # Use a fixed speaking speed instead of each machine's local default.
    engine.setProperty('rate', 190)
    engine.say(text)
    engine.runAndWait()


def listen():
    """Record one voice command and return normalized text or an empty string."""
    recognizer = sr.Recognizer()

    # Record in a predictable format that the speech-recognition service can
    # consume, rather than depending on a microphone's native configuration.
    sample_rate = 16000
    recording_seconds = 10

    print("Speak now (recording for 5 seconds)...")

    # Capture one mono clip so callers do not need to manage microphone streams
    # or manual start/stop events for a basic voice command.
    recording = sd.rec(
        int(recording_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()

    # Convert the recorded NumPy samples into the raw bytes expected by
    # SpeechRecognition before sending them to the transcription service.
    audio = sr.AudioData(recording.tobytes(), sample_rate, 2)

    try:
        command = recognizer.recognize_google(audio, language='en-US')
        print(f"Client said: {command}")

        # Normalize case once so downstream command checks need no variants.
        return command.lower()
    except sr.UnknownValueError:
        # Unclear speech is normal input; return a safe value instead of
        # stopping the application with an exception.
        print("Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError:
        # Online transcription can fail because of a network or service issue;
        # return the same safe value so callers can retry or continue cleanly.
        print("Could not request results from Google Speech Recognition service.")
        return ""


# Keep this demonstration from starting microphone capture when the module is
# imported elsewhere only for its reusable `listen` and `speak` helpers.
if __name__ == "__main__":
    text = listen()
    if text:
        speak(text)
