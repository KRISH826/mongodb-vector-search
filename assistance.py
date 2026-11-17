
import asyncio
import os
import webbrowser
import edge_tts
from playsound import playsound
import speech_recognition as sr

# Assistant ke bolne (Voice Response) ka function
async def _generate_voice(text):
    # "hi-IN-MadhurNeural" (Male Hindi/Hinglish) ya "hi-IN-SwaraNeural" (Female)
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save("response.mp3")

def speak(text):
    print("Assistant:", text)
    asyncio.run(_generate_voice(text))
    playsound("response.mp3")
    os.remove("response.mp3")  # Bolne ke baad temporary audio file delete kar dega

# Aapki awaaz sunne ka function
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nSun raha hoon... Boliye!")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(  # type: ignore[attr-defined]
            audio, language="en-IN"
        )
        print(f"Aapne kaha: {command}")
        return command.lower()
    except Exception:
        speak("Maaf kijiye, mujhe aapki awaaz samajh nahi aayi.")
        return ""

# Main Program
speak("Namaste! Main aapka AI assistant hoon. Batayein main aapki kya madad kar sakta hoon?")

command = listen()

if "open google" in command:
    speak("Bilkul, main aapke liye Google khol raha hoon.")
    webbrowser.open("https://google.com")

elif "open visual studio code" in command or "open vs code" in command:
    speak("Theek hai, Visual Studio Code open kar raha hoon.")
    os.system("code")

elif command != "":
    speak("Maaf kijiye, abhi mujhe yeh command nahi sikhayi gayi hai.")
