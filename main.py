import speech_recognition as sr
import webbrowser
import pyttsx3
import os
import subprocess
import requests # Make sure you have this installed
import cv2

# --- Configuration ---
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set a female voice (optional)
# On Windows, voices can be found in the registry. You might need to find the correct ID.
# On macOS, you can use voices like 'karen' or 'tessa'.
try:
    voices = engine.getProperty('voices')
    # You can print voices to see available options
    # for voice in voices:
    #     print(voice.id)
    engine.setProperty('voice', voices[1].id) # Index 1 is often a female voice on Windows
except (ImportError, IndexError, AttributeError):
    print("Could not set female voice, using default.")

# --- Core Functions ---
def speak(text):
    """Function to make the assistant speak."""
    print(f"Travis: {text}")
    engine.say(text)
    engine.runAndWait()

def ask_ai(question):
    """
    Function to send a question to an external AI model.
    We will use Groq here as it's very fast and has a free tier.
    """
    speak("Thinking...")
    api_key = os.environ.get("GROQ_API_KEY") # IMPORTANT: Set this as an environment variable
    
    if not api_key:
        speak("I am sorry, the AI brain API key is not configured.")
        return "API key not found."

    client = requests.Session()
    try:
        response = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192", # A powerful and fast model
                "messages": [{"role": "user", "content": question}],
                "max_tokens": 1024,
            }
        )
        response.raise_for_status() # Raises an exception for bad status codes
        
        json_response = response.json()
        if json_response.get("choices"):
            return json_response["choices"][0]["message"]["content"]
        else:
            return "Sorry, I received an empty response from the AI brain."

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return "Sorry, I couldn't connect to my AI brain."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An unexpected error occurred while thinking."

def open_face_detection_camera():
    """Opens the camera and performs real-time face detection."""
    
    # Load the pre-trained model for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Sorry, I could not open the camera.")
        return

    speak("Opening face detection camera. Press Q to close.")

    while True:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to grayscale for the classifier
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # Draw rectangles around the faces
        for (x, y, w, h) in faces:
            # Drawing a green rectangle (BGR format)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Display the resulting frame
        cv2.imshow('Face Detection - Press Q to close', frame)

        # Wait for the 'q' key to be pressed to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    speak("Face detection camera closed.")

def open_camera():
    """Opens the default system camera and displays the feed."""
    cap = cv2.VideoCapture(0) # 0 is the default camera
    if not cap.isOpened():
        speak("Sorry, I could not open the camera.")
        return

    speak("Camera feed is live. Press Q to close the window.")

    while True:
        # Read frame from camera
        ret, frame = cap.read()
        if not ret:
            break

        # Display the resulting frame
        cv2.imshow('Camera Feed - Press Q to close', frame)

        # Wait for the 'q' key to be pressed to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    speak("Camera closed.")

def process_command(c):
    """Function to process the user's command."""
    c = c.lower()
    
    # --- System & Application Control ---
    if "open notepad" in c:
        speak("Opening Notepad.")
        subprocess.Popen(['notepad.exe']) # For Windows
        # For macOS: subprocess.Popen(['open', '-a', 'TextEdit'])
    
    elif "open camera" in c and "detection" not in c:
        # This makes sure "open camera" doesn't trigger on "open detection camera"
        open_camera()

    elif "open detection camera" in c:
        open_face_detection_camera()
    
    # ... inside your process_command function
    elif "open camera" in c:
        open_camera() # This now calls our new OpenCV function
    # ... rest of your commands
    
    elif "open file explorer" in c:
        speak("Opening File Explorer.")
        subprocess.Popen(['explorer']) # For Windows
        # For macOS: subprocess.Popen(['open', '.'])

    elif "open settings" in c:
        speak("Opening settings.")
        os.system('start ms-settings:') # For Windows
        # For macOS: subprocess.Popen(['open', '/System/Applications/System Settings.app'])

    elif "open whatsapp" in c:
        speak("Opening WhatsApp.")
        # This requires WhatsApp Desktop to be installed
        # The command might differ based on your installation
        os.startfile("whatsapp.exe") # A more direct way on Windows

    # --- Web Browse ---
    elif "open google" in c:
        speak("Opening Google.")
        webbrowser.open("https://google.com")
        
    elif "open youtube" in c:
        speak("Opening Youtube.")
        webbrowser.open("https://youtube.com")

    # --- AI Question Answering ---
    elif c.startswith(("who is", "what is", "tell me about", "question")):
        # Remove trigger word for a cleaner question
        question = c.replace("who is", "").replace("what is", "").replace("tell me about", "").replace("question", "").strip()
        answer = ask_ai(question)
        speak(answer)

    else:
        speak("I'm not sure how to do that. Can you be more specific?")

# --- Main Loop ---
def activate_travis():
    """The main activation logic, triggered by the hotkey."""
    speak("Yes?")
    try:
        with sr.Microphone() as source:
            print("Listening for your command...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        process_command(command)

    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
    except sr.RequestError as e:
        speak("Could not connect to the speech service.")
        print(f"Speech Service Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during command processing: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    speak("Initializing Travis. I am online and ready.")
    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for activation word ('Travis')...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=10) # Listens for the wake word
            
            word = recognizer.recognize_google(audio)
            
            if "travis" in word.lower():
                speak("Yes Boss?")
                with sr.Microphone() as source:
                    print("Listening for your command...")
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                command = recognizer.recognize_google(audio)
                print(f"You said: {command}")
                process_command(command)

        except sr.UnknownValueError:
            # This is expected when there's silence, so we just loop again
            pass
        except sr.RequestError as e:
            speak("Could not connect to the speech service.")
            print(f"Speech Service Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")