import winrm
import speech_recognition as sr
import pyttsx3
from datetime import datetime

# Initialize text-to-speech
engine = pyttsx3.init()

# WinRM credentials
username = 'administrator'
password = 'Imawsm12!'
server_ip = '192.168.244.129'  # Replace with your VM's IP

# Create WinRM session
session = winrm.Session(f'http://{server_ip}:5985/wsman', auth=(username, password))

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listen for voice input and return recognized command."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Could you repeat?")
        return listen()
    except sr.RequestError:
        speak("Sorry, there seems to be an issue with the speech recognition service.")
        return ""

def confirm(command):
    """Confirm the command with the user."""
    speak(f"Did you mean: {command}? Please say yes or no.")
    
    while True:
        response = listen().lower()
        if 'yes' in response:
            return True
        elif 'no' in response:
            speak("I am sorry sir, please be more specific on what I can assist you today with.")
            return False

def greet_user():
    """Greet the user based on the current time."""
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting} Sir, welcome back. How can I assist you today?"

def clear_c_drive():
    """Clear C drive temporary files."""
    response = session.run_cmd('del /q /s C:\\temp\\*')
    return response.std_out.decode()  # Decode to string

def disk_space_check():
    """Check disk space."""
    response = session.run_cmd('wmic logicaldisk get size,freespace,caption')
    output = response.std_out.decode().strip().split('\n')[1:]  # Get all lines except the header
    disk_info = []
    for line in output:
        if line.strip():  # Ignore empty lines
            parts = line.split()
            caption = parts[0]  # Drive letter (e.g., C:)
            free_space_gb = int(parts[1]) / (1024 ** 3)  # Convert bytes to GB
            total_space_gb = int(parts[2]) / (1024 ** 3)  # Convert bytes to GB
            disk_info.append(f"Drive {caption}: Free space: {free_space_gb:.2f} GB, Total space: {total_space_gb:.2f} GB.")
    return "\n".join(disk_info)

def report_cpu_utilisation():
    """Report CPU utilisation."""
    response = session.run_cmd('wmic cpu get loadpercentage')
    output = response.std_out.decode().strip().split("\n")
    cpu_percentage = output[1].strip()  # Get the second line which is the actual CPU percentage
    return f"{cpu_percentage}%"

def report_uptime():
    """Report system up time."""
    response = session.run_cmd('wmic os get lastbootuptime')
    last_boot_time = response.std_out.decode().strip().split("\n")[1].strip()  # Get the second line
    if last_boot_time:
        last_boot_time = last_boot_time[:14]  # Trim to remove timezone info if present
        try:
            last_boot = datetime.strptime(last_boot_time, '%Y%m%d%H%M%S')
            uptime = datetime.now() - last_boot
            
            # Calculate days, hours, minutes, and seconds
            days, seconds = uptime.days, uptime.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            
            # Create a readable format
            uptime_message = f"{days} days, {hours} hours, {minutes} minutes, and {seconds} seconds."
            return uptime_message
        except ValueError as e:
            print(f"Error parsing uptime: {e}")
            return "Could not parse uptime."
    return "Could not retrieve uptime."

def check_network_config():
    """Check network configurations."""
    response = session.run_cmd('ipconfig /all')
    return response.std_out.decode()  # Decode to string

def reboot_server():
    """Reboot the server."""
    session.run_cmd('shutdown /r /t 0')  # Immediate reboot

def shutdown_server():
    """Shutdown the server."""
    session.run_cmd('shutdown /s /t 0')  # Immediate shutdown

def manage_services():
    """Manage services."""
    speak("Please type the service name you want to manage and hit enter.")
    service_name = input("Enter service name: ").strip()  # Get user input from terminal
    response = session.run_cmd(f'sc query "{service_name}"')

    if 'RUNNING' in response.std_out.decode():
        speak(f"{service_name} is running. Would you like to stop or restart it?")
        action = listen().lower()
        if 'stop' in action:
            action_response = session.run_cmd(f'sc stop "{service_name}"')
            return f"Stopped {service_name}." if 'STOPPED' in action_response.std_out.decode() else f"{service_name} is already stopped."
        elif 'restart' in action:
            action_response = session.run_cmd(f'sc restart "{service_name}"')
            return f"Restarted {service_name}."
    elif 'STOPPED' in response.std_out.decode():
        speak(f"{service_name} is stopped. Would you like to start it?")
        action = listen().lower()
        if 'start' in action:
            action_response = session.run_cmd(f'sc start "{service_name}"')
            return f"Started {service_name}."
        elif 'restart' in action:
            action_response = session.run_cmd(f'sc restart "{service_name}"')
            return f"Restarted {service_name}."
    else:
        return f"{service_name} doesn't exist."

def report_memory_usage():
    """Report memory usage as a percentage."""
    response = session.run_cmd('wmic os get freephysicalmemory,totalvisiblememorysize')
    output = response.std_out.decode().strip().split("\n")
    memory_values = [x.strip() for x in output[-1].split() if x.strip().isdigit()]
    
    if len(memory_values) == 2:
        free_memory = int(memory_values[0])
        total_memory = int(memory_values[1])
        
        # Convert KB to MB for percentage calculation
        used_memory = total_memory - free_memory
        memory_percentage = (used_memory / total_memory) * 100
        
        return f"Memory usage is currently at {memory_percentage:.2f}%."
    else:
        return "Memory data is incomplete."

def patch_history():
    """Check patch history."""
    response = session.run_cmd('wmic qfe list')
    return response.std_out.decode()  # Decode to string

def what_can_you_do():
    """List functionalities."""
    functionalities = [
        "I can do the following tasks:",
        "1. Clear the C drive",
        "2. Disk space check",
        "3. Report CPU utilisation",
        "4. Report up time",
        "5. Check network configurations",
        "6. Manage services",
        "7. Report memory usage",
        "8. Patch history",
        "9. Reboot server",
        "10. Shutdown server",
        "Which one do you want me to assist you with?"
    ]
    output = "\n".join(functionalities)
    print(output)  # Print the list in the terminal first
    return output

def main():
    speak(greet_user())  # Dynamic greeting based on time of day
    
    while True:
        command = listen().lower()

        if 'what can you do' in command:
            functionalities = what_can_you_do()
            speak(functionalities)

        elif 'clear the c drive' in command:
            if confirm("clear the C drive"):
                response = clear_c_drive()
                speak("C drive cleanup completed.")
                print(response)  # Print output
                speak(response)  # Read output
                speak("Is there anything else I can help you with?")

        elif 'space check' in command:
            if confirm("check disk space"):
                response = disk_space_check()
                print(response)  # Print output
                speak(f"Disk space: {response} in GB.")# Read output
                speak("Is there anything else I can help you with?")

        elif 'report cpu utilisation' in command:
            if confirm("report CPU utilisation"):
                response = report_cpu_utilisation()
                print(response)  # Print output
                speak(f"CPU utilisation: {response}.") # Read output
                speak("Is there anything else I can help you with?")

        elif 'report up time' in command:
            if confirm("report system up time"):
                response = report_uptime()
                print(response)  # Print output
                speak(f"System has been up for: {response}.")
                speak("Is there anything else I can help you with?")

        elif 'check network configurations' in command:
            if confirm("check network configurations"):
                response = check_network_config()
                speak("I have fetched the details in terminal, sir.")
                print(response)  # Print output
                speak("Is there anything else I can help you with?")

        elif 'reboot the server' in command:
            if confirm("reboot the server"):
                speak("Rebooting the server now.")
                reboot_server()
                speak("Is there anything else I can help you with?")

        elif 'shutdown the server' in command:
            if confirm("shutdown the server"):
                speak("Shutting down the server now.")
                shutdown_server()
                speak("Is there anything else I can help you with?")

        elif 'manage services' in command:
            if confirm("manage services"):
                response = manage_services()
                print(response)  # Print output
                speak(response)
                speak("Is there anything else I can help you with?")

        elif 'report memory usage' in command:
            if confirm("report memory usage"):
                response = report_memory_usage()
                print(response)  # Print output
                speak(f"Memory usage: {response}.")
                speak("Is there anything else I can help you with?")

        elif 'patch history' in command:
            if confirm("check patch history"):
                response = patch_history()
                print(response)  # Print output
                speak("Patch history has been retrieved. Please check the terminal.")
                speak("Is there anything else I can help you with?")

        elif 'no thank you' in command:
            speak("You're welcome Sir. Have a great day!")
            break

        else:
            speak("Sorry, could you please repeat what you said?")

if __name__ == "__main__":
    main()
