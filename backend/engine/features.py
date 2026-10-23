# """A simple voice assistant that answers only from local PDF or text files.

# Put documents in the `documents` folder next to this file, then run this file.
# The flow is: voice -> text -> find matching document passages -> voice answer.
# """

# `Path` builds folder paths safely on Windows, macOS, and Linux.
from pathlib import Path
# `re` lets us extract individual words from a question or document passage.
import re

# pyttsx3 converts the final text answer into speech (text-to-speech).
import pyttsx3
# PdfReader opens PDFs and extracts their written text page by page.
from pypdf import PdfReader
# sounddevice records sound from the computer microphone.
import sounddevice as sd
# SpeechRecognition sends recorded audio to Google for speech-to-text.
import speech_recognition as sr


# This is the single folder the assistant searches for PDFs and text files.
DOCUMENTS_FOLDER = Path(__file__).parent / "documents"
# Use one fixed reply whenever the documents do not support an answer. This is
# the guardrail that stops the assistant from pretending that it knows.
NOT_FOUND_MESSAGE = (
    "I could not find an answer in the provided documents. "
    "Please ask another question or add a document with that information."
)

# These common words do not help decide whether a document answers a question.
STOP_WORDS = {
    "a", "an", "and", "are", "be", "can", "do", "for", "how", "i", "in",
    "is", "it", "me", "of", "on", "or", "the", "this", "to", "what", "when",
    "where", "which", "who", "will", "with", "you", "your",
}


def speak(text):
    """Read the assistant's text response aloud for the caller."""
    # Create a text-to-speech engine for the current response.
    engine = pyttsx3.init()
    # A fixed rate keeps the response comfortable to hear on each computer.
    engine.setProperty("rate", 190)
    # Put the response into the engine's speech queue.
    engine.say(text)
    # Wait until speaking finishes, so the next question is not recorded early.
    engine.runAndWait()


def listen(recording_seconds=5):
    """Record one question and return its text, or an empty string on failure."""
    # The recognizer turns an audio clip into written words.
    recognizer = sr.Recognizer()
    # 16 kHz mono audio is a common format for speech recognition.
    sample_rate = 16000

    print(f"Speak now (recording for {recording_seconds} seconds)...")
    # Record exactly one microphone clip. `int(...)` calculates its samples.
    recording = sd.rec(
        int(recording_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    # Do not start transcription until microphone recording has completed.
    sd.wait()

    # SpeechRecognition needs raw bytes, not the NumPy audio array.
    audio = sr.AudioData(recording.tobytes(), sample_rate, 2)

    try:
        # Google converts the clip into English text. This needs internet access.
        question = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {question}")
        # Lowercase text makes exit commands and word matching consistent.
        return question.lower()
    except sr.UnknownValueError:
        # The audio was received, but speech could not be confidently understood.
        print("I could not understand the audio. Please try again.")
    except sr.RequestError:
        # The online speech service or the network is unavailable.
        print("Google Speech Recognition is unavailable. Check your internet connection.")

    # An empty string lets the chat loop safely ask for another attempt.
    return ""


def important_words(text):
    """Return useful lowercase words for the beginner-friendly search step."""
    # Remove punctuation, then make every word lowercase before comparing.
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    # A set removes duplicate words; stop words are too common to be useful.
    return {word for word in words if word not in STOP_WORDS and len(word) > 1}


def split_into_chunks(text, words_per_chunk=100):
    """Split a page into small passages so search returns focused evidence."""
    # Searching smaller passages gives a more focused answer than a full page.
    words = text.split()
    return [
        " ".join(words[start : start + words_per_chunk])
        for start in range(0, len(words), words_per_chunk)
    ]


def load_document_chunks(folder=DOCUMENTS_FOLDER):
    """Read PDF and .txt files once and return searchable passages with sources.

    `pypdf` extracts embedded PDF text. Scanned/image-only PDFs need OCR before
    this simple project can search them.
    """
    # Accept a string or a Path so this function is easy to reuse in tests.
    folder = Path(folder)
    if not folder.exists():
        print(f"Documents folder not found: {folder}")
        return []

    # Every item will contain passage text plus the source name and page number.
    chunks = []
    for file_path in folder.rglob("*"):
        # Ignore subfolders; only actual files can be read as documents.
        if not file_path.is_file():
            continue

        try:
            if file_path.suffix.lower() == ".pdf":
                # Open each PDF once when the program starts, not per question.
                reader = PdfReader(file_path)
                for page_number, page in enumerate(reader.pages, start=1):
                    # Some pages have no selectable text, so use an empty string.
                    page_text = page.extract_text() or ""
                    for passage in split_into_chunks(page_text):
                        # Keep evidence metadata to show where an answer came from.
                        chunks.append({
                            "text": passage,
                            "source": file_path.name,
                            "page": page_number,
                        })
            elif file_path.suffix.lower() == ".txt":
                # .txt support makes it easy to try the assistant without a PDF.
                file_text = file_path.read_text(encoding="utf-8")
                for passage in split_into_chunks(file_text):
                    chunks.append({
                        "text": passage,
                        "source": file_path.name,
                        "page": None,
                    })
        except Exception as error:
            # One unreadable document should not stop the rest from loading.
            print(f"Skipped {file_path.name}: {error}")

    return chunks


def find_matching_chunks(question, chunks, maximum_results=2):
    """Rank passages by shared important words and return the best matches."""
    # Extract the meaningful words from what the caller asked.
    question_words = important_words(question)
    if not question_words:
        # A question containing only words such as "what" cannot be searched.
        return []

    # Requiring two matching words for longer questions avoids weak matches.
    minimum_matches = 1 if len(question_words) <= 2 else 2
    matches = []
    for chunk in chunks:
        # `&` finds words present in both the question and this passage.
        shared_words = question_words & important_words(chunk["text"])
        if len(shared_words) >= minimum_matches:
            # More shared question words means a more relevant passage.
            score = len(shared_words) / len(question_words)
            matches.append((score, chunk))

    # Sort highest score first, then return only the best two passages.
    matches.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in matches[:maximum_results]]


def answer_question(question, chunks):
    """Return document evidence, or a safe response when evidence is absent."""
    # Retrieval happens before answering, which keeps every answer grounded.
    matches = find_matching_chunks(question, chunks)
    if not matches:
        return NOT_FOUND_MESSAGE

    # Build one response from the matching passages and their source details.
    answer_parts = ["Here is the most relevant information I found:"]
    for chunk in matches:
        source = chunk["source"]
        if chunk["page"] is not None:
            # PDFs have pages; text files do not, so omit a page for text files.
            source += f", page {chunk['page']}"
        answer_parts.append(f"From {source}: {chunk['text']}")

    return " ".join(answer_parts)


def run_voice_document_chat():
    """Start the voice loop. Say 'exit', 'quit', or 'stop' to end it."""
    # Load once at startup. This prevents rereading every PDF after each question.
    chunks = load_document_chunks()
    if not chunks:
        # Explain the setup issue aloud and stop rather than entering a broken loop.
        message = (
            f"No readable PDF or text files were found in {DOCUMENTS_FOLDER}. "
            "Add documents there and try again."
        )
        print(message)
        speak(message)
        return

    # Tell the caller that document loading was successful.
    welcome_message = "I am ready. Ask a question about your documents, or say exit."
    print(welcome_message)
    speak(welcome_message)

    while True:
        # One loop iteration handles one caller question.
        question = listen()
        if not question:
            # Audio errors should not end the whole assistant.
            continue
        if question in {"exit", "quit", "stop"}:
            # End only when the caller explicitly uses an exit command.
            speak("Goodbye.")
            break

        # Search the loaded documents, print the evidence, and speak it aloud.
        answer = answer_question(question, chunks)
        print(f"Assistant: {answer}")
        speak(answer)


if __name__ == "__main__":
    # Start voice chat only when this file is run directly, not when imported.
    run_voice_document_chat()
