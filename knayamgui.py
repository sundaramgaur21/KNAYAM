import tkinter as tk
from tkinter import messagebox
import datetime
import pyttsx3
import speech_recognition as sr
import winrm
import threading

# Initialize WinRM session for server communication
session = winrm.Session('http://192.168.244.129:5985/wsman', auth=('Administrator', 'Imawsm12!'))

# Initialize speech engine
engine = pyttsx3.init()

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen for voice commands
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        try:
            command = r.recognize_google(audio)
            return command.lower()
        except sr.UnknownValueError:
            return "I didn't understand that."

# Greet user based on the time of day
def greet():
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        return "Good morning sir, how can I assist you today?"
    elif current_hour < 18:
        return "Good afternoon sir, how can I assist you today?"
    else:
        return "Good evening sir, how can I assist you today?"

# Define assistant functions using your server commands
def clear_c_drive():
    response = session.run_cmd('del /q /s C:\\temp\\*')
    return response.std_out.decode()

def disk_space_check():
    response = session.run_cmd('wmic logicaldisk get size,freespace,caption')
    output = response.std_out.decode().strip().split('\n')[1:]
    disk_info = []
    for line in output:
        if line.strip():
            parts = line.split()
            caption = parts[0]
            free_space_gb = int(parts[1]) / (1024 ** 3)
            total_space_gb = int(parts[2]) / (1024 ** 3)
            disk_info.append(f"Drive {caption}: Free space: {free_space_gb:.2f} GB, Total space: {total_space_gb:.2f} GB.")
    return "\n".join(disk_info)

def report_cpu_utilisation():
    response = session.run_cmd('wmic cpu get loadpercentage')
    output = response.std_out.decode().strip().split("\n")
    cpu_percentage = output[1].strip()
    return f"CPU Utilisation: {cpu_percentage}%"

def report_uptime():
    response = session.run_cmd('wmic os get lastbootuptime')
    last_boot_time = response.std_out.decode().strip().split("\n")[1].strip()
    if last_boot_time:
        last_boot_time = last_boot_time[:14]
        try:
            last_boot = datetime.datetime.strptime(last_boot_time, '%Y%m%d%H%M%S')
            uptime = datetime.datetime.now() - last_boot
            days, seconds = uptime.days, uptime.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"System uptime: {days} days, {hours} hours, {minutes} minutes."
        except ValueError as e:
            return "Error parsing uptime."
    return "Could not retrieve uptime."

def check_network_config():
    response = session.run_cmd('ipconfig /all')
    return response.std_out.decode()

def reboot_server():
    session.run_cmd('shutdown /r /t 0')
    return "Rebooting server..."

def shutdown_server():
    session.run_cmd('shutdown /s /t 0')
    return "Shutting down server..."

def manage_services():
    speak("Please type the service name you want to manage.")
    service_name = input("Enter service name: ").strip()
    response = session.run_cmd(f'sc query "{service_name}"')
    if 'RUNNING' in response.std_out.decode():
        speak(f"{service_name} is running. Would you like to stop or restart it?")
        action = listen().lower()
        if 'stop' in action:
            session.run_cmd(f'sc stop "{service_name}"')
            return f"Stopped {service_name}."
        elif 'restart' in action:
            session.run_cmd(f'sc restart "{service_name}"')
            return f"Restarted {service_name}."
    elif 'STOPPED' in response.std_out.decode():
        speak(f"{service_name} is stopped. Would you like to start it?")
        action = listen().lower()
        if 'start' in action:
            session.run_cmd(f'sc start "{service_name}"')
            return f"Started {service_name}."
    else:
        return f"Service {service_name} doesn't exist."

def report_memory_usage():
    response = session.run_cmd('wmic os get freephysicalmemory,totalvisiblememorysize')
    output = response.std_out.decode().strip().split("\n")
    memory_values = [x.strip() for x in output[-1].split() if x.strip().isdigit()]
    if len(memory_values) == 2:
        free_memory = int(memory_values[0])
        total_memory = int(memory_values[1])
        used_memory = total_memory - free_memory
        memory_percentage = (used_memory / total_memory) * 100
        return f"Memory usage: {memory_percentage:.2f}%."
    else:
        return "Memory data is incomplete."

def patch_history():
    response = session.run_cmd('wmic qfe list')
    return response.std_out.decode()

def what_can_you_do():
    functionalities = (
        "I can perform the following tasks:\n"
        "1. Clear C drive\n"
        "2. Check disk space\n"
        "3. Report CPU utilization\n"
        "4. Report uptime\n"
        "5. Check network configuration\n"
        "6. Manage services\n"
        "7. Report memory usage\n"
        "8. Patch history\n"
        "9. Reboot server\n"
        "10. Shutdown server"
    )
    return functionalities

# Main GUI class
class KNAYAMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KNAYAM - Your Friendly Neighbourhood Personal Assistant")

        # Create GUI layout
        self.create_widgets()

    def create_widgets(self):
        # Title and slogan
        title_label = tk.Label(self.root, text="KNAYAM", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=5)

        slogan_label = tk.Label(self.root, text="Your Friendly Neighbourhood Personal Assistant", font=("Helvetica", 12))
        slogan_label.grid(row=1, column=0, columnspan=3, pady=5)

        # White box for conversation display
        self.text_box = tk.Text(self.root, height=15, width=60, bg="white")
        self.text_box.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        
        # Activate, deactivate, and exit buttons
        tk.Button(self.root, text="Activate Assistant", bg="green", command=self.activate_assistant).grid(row=3, column=0)
        tk.Button(self.root, text="Deactivate Assistant", bg="red", command=self.deactivate_assistant).grid(row=3, column=1)
        tk.Button(self.root, text="Exit", bg="black", fg="white", command=self.exit_program).grid(row=3, column=2)
        
        # Function buttons
        buttons = [
            ("Clear C Drive", self.clear_c_drive),
            ("Check Disk Space", self.check_disk_space),
            ("Report CPU Utilisation", self.report_cpu_utilisation),
            ("Report Uptime", self.report_uptime),
            ("Check Network Config", self.check_network_config),
            ("Manage Services", self.manage_services),
            ("Report Memory Usage", self.report_memory_usage),
            ("Check Patch History", self.check_patch_history),
            ("Reboot Server", self.reboot_server),
            ("Shutdown Server", self.shutdown_server),
            ("What Can You Do?", self.what_can_you_do),
            ("Voice Command", self.voice_command)
        ]
        for i, (text, command) in enumerate(buttons):
            tk.Button(self.root, text=text, command=command).grid(row=4 + i // 3, column=i % 3, padx=5, pady=5)

        # Copyright at the bottom center
        copyright_label = tk.Label(self.root, text="© Sundaram Gaur, 2024", font=("Helvetica", 10))
        copyright_label.grid(row=9, column=0, columnspan=3, pady=5)

    def activate_assistant(self):
        self.update_text_box("KNAYAM: " + greet())
        self.listen_for_command()

    def deactivate_assistant(self):
        self.update_text_box("KNAYAM: Deactivating... Goodbye.")
        self.listening = False

    def exit_program(self):
        self.root.quit()

    # Update text box
    def update_text_box(self, text):
        self.text_box.insert(tk.END, text + "\n")
        self.text_box.see(tk.END)
        speak(text)

    # Listen for command and handle execution
    def listen_for_command(self):
        threading.Thread(target=self._listen_for_command).start()

    def _listen_for_command(self):
        while True:
            self.update_text_box("Listening...")
            command = listen()
            self.update_text_box(f"You: {command}")
            self.execute_command(command)

    def execute_command(self, command):
        if "clear c drive" in command:
            self.clear_c_drive()
        elif "check disk space" in command:
            self.check_disk_space()
        elif "cpu utilization" in command:
            self.report_cpu_utilisation()
        elif "uptime" in command:
            self.report_uptime()
        elif "network configuration" in command:
            self.check_network_config()
        elif "manage services" in command:
            self.manage_services()
        elif "memory usage" in command:
            self.report_memory_usage()
        elif "patch history" in command:
            self.check_patch_history()
        elif "reboot server" in command:
            self.reboot_server()
        elif "shutdown server" in command:
            self.shutdown_server()
        elif "what can you do" in command:
            self.what_can_you_do()
        elif "deactivate" in command:
            self.deactivate_assistant()
        elif "exit" in command:
            self.exit_program()
        else:
            self.update_text_box("KNAYAM: I didn't understand that. Please try again.")

    # Task-specific button functions
    def clear_c_drive(self):
        confirmation = messagebox.askyesno("Confirm Action", "Are you sure you want to clear C drive?")
        if confirmation:
            result = clear_c_drive()
            self.update_text_box("KNAYAM: " + result)

    def check_disk_space(self):
        result = disk_space_check()
        self.update_text_box("KNAYAM: Please see the outputs in the terminal.")
        print(result)

    def report_cpu_utilisation(self):
        result = report_cpu_utilisation()
        self.update_text_box("KNAYAM: " + result)

    def report_uptime(self):
        result = report_uptime()
        self.update_text_box("KNAYAM: " + result)

    def check_network_config(self):
        result = check_network_config()
        self.update_text_box("KNAYAM: Please see the outputs in the terminal.")
        print(result)

    def reboot_server(self):
        result = reboot_server()
        self.update_text_box("KNAYAM: " + result)

    def shutdown_server(self):
        result = shutdown_server()
        self.update_text_box("KNAYAM: " + result)

    def manage_services(self):
        result = manage_services()
        self.update_text_box("KNAYAM: " + result)

    def report_memory_usage(self):
        result = report_memory_usage()
        self.update_text_box("KNAYAM: " + result)

    def check_patch_history(self):
        result = patch_history()
        self.update_text_box("KNAYAM: Please see the outputs in the terminal.")
        print(result)

    def what_can_you_do(self):
        result = what_can_you_do()
        self.update_text_box("KNAYAM: " + result)

    def voice_command(self):
        self.update_text_box("KNAYAM: Voice command activated.")
        self.listen_for_command()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = KNAYAMApp(root)
    root.mainloop()
