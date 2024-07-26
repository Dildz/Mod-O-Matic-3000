# Depencency imports
import customtkinter as ctk
from tkinter import Tk, filedialog, Toplevel, Label
import os
import shutil
import hashlib
import logging
import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
#WORKING_DIRECTORY = r"C:\Users\Dildz\Desktop"  # temp testing working-dir
WORKING_DIRECTORY = os.getcwd()
IGNORE_LIST = [
    os.path.join("BepInEx", "plugins", "spt"),
    os.path.join("BepInEx", "patchers", "spt-prepatch.dll"),
    os.path.join("BepInEx", "config", "BepInEx.cfg"),
    os.path.join("BepInEx", "config", "com.bepis.bepinex.configurationmanager.cfg")
]

# Class to create custom tooltips for buttons
class CustomToolTip:
    # Create a tooltip for a given widget
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.update_position)

    # Show the tooltip
    def show_tooltip(self, event=None):
        if not self.tooltip:
            self.tooltip = Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            label = Label(self.tooltip, text=self.text, background="white", relief='solid', borderwidth=1, wraplength=200)
            label.pack(ipadx=1)
        self.update_position(event)

    # Hide the tooltip
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.withdraw()

    # Update tooltip position
    def update_position(self, event=None):
        if self.tooltip:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25
            self.tooltip.wm_geometry(f"+{x}+{y}")
            self.tooltip.deiconify()

# Main class for the application
class FileCopyApp(ctk.CTkFrame):
    # Initialize the application
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Mod-O-Matic-3000")
        self.master.geometry("500x300")
        self.center_window(500, 300)
        self.master.configure(bg='gray20')
        self.master.wm_attributes("-alpha", 0.98)
        self.pack(fill="both", expand=True)
        self.working_directory = WORKING_DIRECTORY
        self.sptarkov_directory = ""
        self.task_complete = False
        self.setup_init_screen()

    # Center the window on the screen
    def center_window(self, width, height):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 3) - (height / 2)
        self.master.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    # Set up the initial screen
    def setup_init_screen(self):
        self.clear_widgets()
        self.init_label = ctk.CTkLabel(self, text="Set the location of your SPTarkov directory")
        self.init_label.place(relx=0.5, rely=0.3, anchor="center")
        self.select_folder_button = ctk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.select_folder_button.place(relx=0.5, rely=0.5, anchor="center")

    # Select the SPTarkov target directory
    def select_folder(self):
        self.sptarkov_directory = self.centered_filedialog()
        if self.sptarkov_directory:
            self.backup_folder = os.path.join(self.sptarkov_directory, "BepInEx", "mod-o-matic-3000-backup")
            self.cleanup_desktop_ini(self.sptarkov_directory)
            self.scan_and_backup_files()

    # Center the file dialog on the screen
    def centered_filedialog(self):
        temp_window = Toplevel(self.master)
        temp_window.withdraw()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        dialog_width = 800
        dialog_height = 600
        x = (screen_width // 2) - (dialog_width // 2)
        y = (screen_height // 3) - (dialog_height // 2)
        temp_window.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
        temp_window.update_idletasks()
        selected_directory = filedialog.askdirectory(parent=temp_window)
        temp_window.destroy()
        return selected_directory

    # Scan and backup the files in the SPTarkov target directory
    def scan_and_backup_files(self):
        files_to_backup = self.find_files_to_backup()
        if files_to_backup:
            self.create_backup_folder()
            self.setup_backup_screen(len(files_to_backup))
            self.after(100, self.backup_files, files_to_backup)
        else:
            self.setup_action_screen(backup_found=False)

    # Find if there are files to backup
    def find_files_to_backup(self):
        files_to_backup = []
        for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
            folder_path = os.path.join(self.sptarkov_directory, subfolder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.sptarkov_directory)
                    if not any(rel_path.startswith(ignore) for ignore in IGNORE_LIST):
                        files_to_backup.append((file_path, rel_path))
        return files_to_backup

    # Create the backup folder
    def create_backup_folder(self):
        if os.path.exists(self.backup_folder):
            shutil.rmtree(self.backup_folder)
        os.makedirs(self.backup_folder)

    # Setup the backup screen
    def setup_backup_screen(self, total_files):
        self.clear_widgets()
        self.progress_label = ctk.CTkLabel(self, text=f"Backing up 0/{total_files} files...")
        self.progress_label.place(relx=0.5, rely=0.4, anchor="center")
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_bar.set(0)

    # Backup existing mod-files
    def backup_files(self, files_to_backup):
        total_files = len(files_to_backup)
        for backed_up_files, (file_path, rel_path) in enumerate(files_to_backup, start=1):
            self.copy_with_progress(file_path, os.path.join(self.backup_folder, rel_path), backed_up_files, total_files, "Backing up")
        self.setup_action_screen(backup_found=True)

    # Copy files with progress bar
    def copy_with_progress(self, src, dst, current, total, action):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        logging.info(f"{action} {src} to {dst}")
        if hasattr(self, 'progress_label') and hasattr(self, 'progress_bar'):
            self.progress_label.configure(text=f"{action} {current}/{total} files...")
            self.progress_bar.set(current / total)
            self.master.update()
        time.sleep(0.01)

    # Setup the main action screen
    def setup_action_screen(self, backup_found):
        self.clear_widgets()
        info_text = "Mods backed up - Click the Mod Updates button if it's Monday" if backup_found else "No mod files found - Click the New Install button"
        self.info_label = ctk.CTkLabel(self, text=info_text)
        self.info_label.place(relx=0.5, rely=0.15, anchor="center")
        self.create_buttons(backup_found)

    # Create the action screen buttons
    def create_buttons(self, backup_found):
        self.new_install_button = ctk.CTkButton(self, text="New Install", command=self.confirm_new_install)
        self.new_install_button.place(relx=0.5, rely=0.4, anchor="center")
        CustomToolTip(self.new_install_button, "Copy all contents from 'New Installs' folder to the SPTarkov directory")
        self.mod_updates_button = ctk.CTkButton(self, text="Mod Updates", command=self.mod_updates)
        self.mod_updates_button.place(relx=0.5, rely=0.6, anchor="center")
        CustomToolTip(self.mod_updates_button, "Copy all contents from 'Monday Updates' folder to the SPTarkov directory")
        if backup_found:
            self.restore_backup_button = ctk.CTkButton(self, text="Restore Backup", command=self.restore_backup)
            self.restore_backup_button.place(relx=0.5, rely=0.8, anchor="center")
            CustomToolTip(self.restore_backup_button, "Restore all previously backed up files to their original locations")

    # Delete existing mods before new install process (if user confirms yes & a backup exists)
    def delete_existing_mods(self):
        mods_to_delete = []
        for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
            folder_path = os.path.join(self.sptarkov_directory, subfolder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.sptarkov_directory)
                    if not any(rel_path.startswith(ignore) for ignore in IGNORE_LIST):
                        mods_to_delete.append(file_path)

        total_mods = len(mods_to_delete)
        for count, file_path in enumerate(mods_to_delete, start=1):
            os.remove(file_path)
            logging.info(f"Deleted {file_path}")
            self.progress_label.configure(text=f"Deleting mods: {count}/{total_mods}")
            self.progress_bar.set(count / total_mods)
            self.master.update()
            time.sleep(0.01)

    # Confirm new install process popup
    def confirm_new_install(self):
        if os.path.exists(self.backup_folder):
            self.show_custom_messagebox(
                "Confirmation",
                "You already have mods installed.\nContinuing will replace any existing mods.\nAre you sure you want to proceed?\nYou can revert the changes using the backup.",
                self.new_install_with_deletion
            )
        else:
            self.new_install()

    # Show custom messagebox popup
    def show_custom_messagebox(self, title, message, on_yes=None, ok_only=False):
        popup = self.create_popup(title, message, ok_only)
        if not ok_only:
            self.create_confirmation_buttons(popup, on_yes)
        else:
            self.create_ok_button(popup)
        self.center_popup(popup)

    # Create the custom popup window
    def create_popup(self, title, message, ok_only):
        popup = Toplevel(self.master)
        popup.title(title)
        popup.geometry("300x150" if not ok_only else "300x190")
        popup.transient(self.master)
        popup.grab_set()
        label = Label(popup, text=message, wraplength=250)
        label.pack(pady=10)
        return popup

    # Create the OK button for the custom popup
    def create_ok_button(self, popup):
        button_frame = ctk.CTkFrame(popup, fg_color="white")
        button_frame.pack(pady=10)
        self.create_button(button_frame, "OK", popup.destroy, side="left")

    # Create the Yes/No buttons for the custom popup
    def create_confirmation_buttons(self, popup, on_yes):
        button_frame = ctk.CTkFrame(popup, fg_color="white")
        button_frame.pack(pady=10)
        self.create_button(button_frame, "Yes", lambda: [popup.destroy(), on_yes()], side="left")
        self.create_button(button_frame, "No", popup.destroy, side="right")

    # Create a button with custom styling
    def create_button(self, parent, text, command, side="top"):
        button = ctk.CTkButton(parent, text=text, command=command)
        button.pack(side=side, padx=10)
        button.configure(width=100, corner_radius=10, border_width=0, fg_color="#1f6aa5", hover_color="#1a5a8b")

    # Center the custom popup on the main window
    def center_popup(self, popup):
        self.master.update_idletasks()
        popup.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        popup.configure(bg="white")
        for widget in popup.winfo_children():
            widget.configure(bg="white")

    # New install process with deletion of existing mods
    def new_install_with_deletion(self):
        self.task_complete = False
        self.cleanup_desktop_ini_working_directory()
        self.setup_delete_screen()  # Setup screen for deletion process
        self.delete_existing_mods()  # Delete existing mods first
        self.setup_copy_screen()
        self.copy_files(['New Installs'])
        self.task_complete = True

    # New install process without deletion of existing mods
    def new_install(self):
        self.task_complete = False
        self.cleanup_desktop_ini_working_directory()
        self.setup_copy_screen()
        self.copy_files(['New Installs'])
        self.task_complete = True

    # Mod updates process
    def mod_updates(self):
        if datetime.datetime.today().weekday() != 0:
            self.show_custom_messagebox(
                "Not Monday",
                "Wait...it's not Monday-Update Day...why are you clicking this??\n\nWe don't want to upset J - aka DahFragMeister\n\nWe only update on Monday, otherwise it's 'frag-in-your-face-day'",
                ok_only=True
            )
            return
        self.task_complete = False
        self.cleanup_desktop_ini_working_directory()
        self.setup_copy_screen()
        if self.check_files_exist(['Monday Updates']):
            self.hide_buttons()
            self.execute_copy(['Monday Updates'])
        else:
            self.show_no_updates_popup()

    # Show popup when no updates are found
    def show_no_updates_popup(self):
        self.show_custom_messagebox(
            "No Updates",
            "There are no updates to copy.",
            ok_only=True
        )

    # Restore backup process
    def restore_backup(self):
        self.task_complete = False
        self.setup_restore_screen()
        files_to_restore = self.find_files_to_restore()
        total_files = len(files_to_restore)
        for restored_files, (backup_path, rel_path) in enumerate(files_to_restore, start=1):
            self.copy_with_progress(backup_path, os.path.join(self.sptarkov_directory, rel_path), restored_files, total_files, "Restoring")
        shutil.rmtree(self.backup_folder)
        logging.info("Backup folder deleted")
        self.task_complete = True
        self.display_completion_message("Files restored successfully! You can now close this window.")

    # Setup screen for deletion process
    def setup_delete_screen(self):
        self.clear_widgets()
        self.progress_label = ctk.CTkLabel(self, text="Preparing to delete existing mods...")
        self.progress_label.place(relx=0.5, rely=0.4, anchor="center")
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_bar.set(0)

    # Setup screen for copying process
    def setup_copy_screen(self):
        self.clear_widgets()
        self.create_progress_widgets("Copying mods to your SPT install directory...")

    # Setup screen for restore process
    def setup_restore_screen(self):
        self.clear_widgets()
        self.progress_label = ctk.CTkLabel(self, text="Preparing to restore files...")
        self.progress_label.place(relx=0.5, rely=0.4, anchor="center")
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_bar.set(0)

    # Create progress widgets for copying process
    def create_progress_widgets(self, initial_text):
        self.progress_label = ctk.CTkLabel(self, text=initial_text)
        self.progress_label.place(relx=0.5, rely=0.35, anchor="center")
        self.progress_label_copy = ctk.CTkLabel(self, text="Preparing to copy files...")
        self.progress_label_copy.place(relx=0.5, rely=0.45, anchor="center")
        self.progress_bar_copy = ctk.CTkProgressBar(self, width=400)
        self.progress_bar_copy.place(relx=0.5, rely=0.55, anchor="center")
        self.progress_bar_copy.set(0)
        self.progress_label_verify = ctk.CTkLabel(self, text="Verifying copied files...")
        self.progress_label_verify.place(relx=0.5, rely=0.45, anchor="center")
        self.progress_label_verify.lower()
        self.progress_bar_verify = ctk.CTkProgressBar(self, width=400)
        self.progress_bar_verify.place(relx=0.5, rely=0.55, anchor="center")
        self.progress_bar_verify.set(0)
        self.progress_bar_verify.lower()

    # Hide buttons during copying process
    def hide_buttons(self):
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()

    # Cleanup desktop.ini files in working directory
    def cleanup_desktop_ini_working_directory(self):
        self.cleanup_desktop_ini(self.working_directory)

    # Cleanup desktop.ini files in target directory
    def cleanup_desktop_ini(self, directory):
        for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
            folder_path = os.path.join(directory, subfolder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower() == 'desktop.ini':
                        os.remove(os.path.join(root, file))
                        logging.info(f"Deleted {os.path.join(root, file)} from directory")

    # Check if files exist in the working directory
    def check_files_exist(self, folders):
        for folder in folders:
            for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
                folder_path = os.path.join(self.working_directory, folder, subfolder)
                for root, dirs, files in os.walk(folder_path):
                    if files:
                        return True
        return False

    # Execute the copy process
    def execute_copy(self, folders):
        self.copy_files(folders)

    # Copy files to the SPTarkov target directory
    def copy_files(self, folders):
        self.progress_label_copy.configure(text="Preparing to copy files...")
        self.progress_bar_copy.set(0)
        total_files = self.total_files(folders)
        self.progress_label_copy.configure(text=f"Copying 0/{total_files}")
        self.after(100, self.start_copy, folders, total_files)

    # Calculate total number of files to copy
    def total_files(self, folders):
        return sum(len(files) for folder in folders for _, _, files in os.walk(os.path.join(self.working_directory, folder)))

    # Start the copy process
    def start_copy(self, folders, total_files):
        copied_files = 0
        backup_needed = False
        self.progress_bar_copy.set(0)
        for folder in folders:
            for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
                src_folder = os.path.join(self.working_directory, folder, subfolder)
                for root, dirs, files in os.walk(src_folder):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, src_folder)
                        dest_path = os.path.join(self.sptarkov_directory, subfolder, rel_path)
                        dest_dir = os.path.dirname(dest_path)
                        os.makedirs(dest_dir, exist_ok=True)
                        if os.path.exists(dest_path):
                            if not backup_needed:
                                self.create_backup_folder()
                                backup_needed = True
                            self.backup_file(dest_path, os.path.join(subfolder, rel_path))
                        shutil.copy2(src_path, dest_path)
                        copied_files += 1
                        logging.info(f"Copied {src_path} to {dest_path}")
                        self.progress_label_copy.configure(text=f"Copying {copied_files}/{total_files}")
                        self.progress_bar_copy.set(copied_files / total_files)
                        self.master.update()
                        time.sleep(0.01)
        self.progress_label_copy.place_forget()
        self.progress_bar_copy.place_forget()
        self.progress_label_verify.lift()
        self.progress_bar_verify.lift()
        self.after(100, self.start_verification, folders, total_files)

    # Start the verification process
    def start_verification(self, folders, total_files):
        verified_files = 0
        self.progress_label.configure(text="Verifying copied files by comparing hashes...")
        self.progress_bar_verify.set(0)
        for folder in folders:
            for subfolder in ['BepInEx/config', 'BepInEx/patchers', 'BepInEx/plugins']:
                src_folder = os.path.join(self.working_directory, folder, subfolder)
                for root, dirs, files in os.walk(src_folder):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, src_folder)
                        dest_path = os.path.join(self.sptarkov_directory, subfolder, rel_path)
                        if self.compare_files(src_path, dest_path):
                            verified_files += 1
                            logging.info(f"Verified {src_path} with {dest_path}")
                            self.progress_label_verify.configure(text=f"Verifying {verified_files}/{total_files}")
                            self.progress_bar_verify.set(verified_files / total_files)
                            self.master.update()
                            time.sleep(0.01)
                        else:
                            logging.error(f"Verification failed for {dest_path}")
                            self.progress_label.configure(text="File verification failed. Re-download the G-Drive folder & try again.")
                            return
        self.progress_label.configure(text="Files copied and verified successfully! You can now close this window.")
        self.progress_label_verify.configure(text=f"Verified {verified_files}/{total_files}")
        self.task_complete = True

    # Calculate hash value of a file
    def calculate_hash(self, file_path):
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    # Compare files using hash values
    def compare_files(self, file1, file2):
        hash1 = self.calculate_hash(file1)
        hash2 = self.calculate_hash(file2)
        return hash1 == hash2

    # Backup file process
    def backup_file(self, file_path, rel_path):
        backup_path = os.path.join(self.backup_folder, os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        logging.info(f"Backed up {file_path} to {backup_path}")

    # Display completion message
    def display_completion_message(self, message=None):
        self.progress_label.configure(text=message or "Files copied and verified successfully! You can now close this window.")

    # Clear all widgets from the screen
    def clear_widgets(self):
        for widget in self.winfo_children():
            widget.destroy()

    # Find files to restore from the backup folder
    def find_files_to_restore(self):
        files_to_restore = []
        for root, _, files in os.walk(self.backup_folder):
            for file in files:
                backup_path = os.path.join(root, file)
                rel_path = os.path.relpath(backup_path, self.backup_folder)
                files_to_restore.append((backup_path, rel_path))
        return files_to_restore

# Main function to run the application
if __name__ == "__main__":
    root = Tk()
    app = FileCopyApp(master=root)
    app.mainloop()

