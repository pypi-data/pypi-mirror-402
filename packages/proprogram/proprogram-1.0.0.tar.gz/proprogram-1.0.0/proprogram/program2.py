program2 = """\
import speech_recognition as sr
r=sr.Recognizer()
with sr.AudioFile("D:/clg/audio.wav") as source:
    audio=r.record(source)
try:
    text=r.recognize_google(audio)
    print("Recognized text:",text)
except sr.UnknownValueError:
    print("Sorry, could not understand the audio")
except sr.RequestError as e:
    print(f"Could not request results; {e}")
"""
