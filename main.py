import subprocess
import os
import sys
import requests
import zipfile
import tarfile
import shutil
import stat # For setting file permissions on Linux/macOS

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QTextEdit, QProgressBar,
    QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QFont, QDesktopServices # For opening URLs

# --- Helper function to find executables ---
def find_executable(name, path_list):
    """
    Searches for an executable with the given name in the provided list of paths.
    Considers the .exe extension for Windows.
    """
    for path in path_list:
        # Try the name directly
        full_path = os.path.join(path, name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
        # Try with .exe extension for Windows
        if sys.platform == "win32":
            full_path_exe = os.path.join(path, name + ".exe")
            if os.path.isfile(full_path_exe) and os.access(full_path_exe, os.X_OK):
                return full_path_exe
    return None

# --- Worker Thread for Downloading Tools ---
class SetupWorker(QThread):
    """
    Thread for downloading and extracting yt-dlp and ffmpeg.
    """
    update_status = pyqtSignal(str)
    update_progress_bar = pyqtSignal(int, str) # value, text
    setup_finished = pyqtSignal(bool, str) # success, message

    def __init__(self, tools_dir):
        super().__init__()
        self.tools_dir = tools_dir

    def run(self):
        try:
            # Create tools directory if it doesn't exist
            if not os.path.exists(self.tools_dir):
                os.makedirs(self.tools_dir)
                self.update_status.emit(f"Created tools directory: {self.tools_dir}")

            # --- Download yt-dlp ---
            yt_dlp_name = "yt-dlp"
            if sys.platform == "win32":
                yt_dlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                yt_dlp_filename = "yt-dlp.exe"
            else:
                yt_dlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
                yt_dlp_filename = "yt-dlp"

            yt_dlp_path = os.path.join(self.tools_dir, yt_dlp_filename)

            if not os.path.exists(yt_dlp_path):
                self.update_status.emit(f"Downloading {yt_dlp_filename}...")
                self._download_file(yt_dlp_url, yt_dlp_path, "yt-dlp")
                if sys.platform != "win32": # Set execute permissions for Linux/macOS
                    os.chmod(yt_dlp_path, os.stat(yt_dlp_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                self.update_status.emit(f"{yt_dlp_filename} downloaded.")
            else:
                self.update_status.emit(f"{yt_dlp_filename} already exists.")

            # --- Download FFmpeg ---
            ffmpeg_name = "ffmpeg"
            ffprobe_name = "ffprobe"
            ffmpeg_path_in_tools = os.path.join(self.tools_dir, ffmpeg_name)
            ffprobe_path_in_tools = os.path.join(self.tools_dir, ffprobe_name)

            if sys.platform == "win32":
                ffmpeg_archive_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.zip"
                ffmpeg_archive_filename = "ffmpeg-release-full.zip"
            elif sys.platform == "darwin": # macOS
                # Note: This URL might need updating for newer FFmpeg versions.
                ffmpeg_archive_url = "https://evermeet.cx/ffmpeg/ffmpeg-latest.zip" # Using latest for better future-proofing
                ffmpeg_archive_filename = "ffmpeg-latest.zip"
            else: # Linux
                # Note: This URL is for AMD64 static builds. Adjust for other architectures if needed.
                ffmpeg_archive_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
                ffmpeg_archive_filename = "ffmpeg-release-amd64-static.tar.xz"

            temp_archive_path = os.path.join(self.tools_dir, ffmpeg_archive_filename)
            temp_extract_dir = os.path.join(self.tools_dir, "ffmpeg_temp_extract")

            if not os.path.exists(ffmpeg_path_in_tools) or not os.path.exists(ffprobe_path_in_tools):
                self.update_status.emit(f"Downloading {ffmpeg_archive_filename}...")
                self._download_file(ffmpeg_archive_url, temp_archive_path, "FFmpeg")
                self.update_status.emit(f"Extracting {ffmpeg_archive_filename}...")

                # Extract to a temporary directory and get the actual root of extracted content
                extracted_root_dir = self._extract_to_temp_dir(temp_archive_path, temp_extract_dir)

                # Search for ffmpeg and ffprobe within the extracted root dir and its common subfolders
                search_paths_for_exec = [extracted_root_dir]
                # Add a 'bin' subfolder to search paths, common for Windows FFmpeg builds
                search_paths_for_exec.append(os.path.join(extracted_root_dir, "bin"))

                extracted_ffmpeg_path = find_executable(ffmpeg_name, search_paths_for_exec)
                extracted_ffprobe_path = find_executable(ffprobe_name, search_paths_for_exec)

                if not extracted_ffmpeg_path or not extracted_ffprobe_path:
                    raise Exception(f"FFmpeg or FFprobe executables not found after extraction in {search_paths_for_exec}. Please check the archive content.")

                # Move ffmpeg/ffprobe to the main tools_dir
                shutil.move(extracted_ffmpeg_path, ffmpeg_path_in_tools)
                shutil.move(extracted_ffprobe_path, ffprobe_path_in_tools)

                if sys.platform != "win32": # Set execute permissions for Linux/macOS
                    os.chmod(ffmpeg_path_in_tools, os.stat(ffmpeg_path_in_tools).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    os.chmod(ffprobe_path_in_tools, os.stat(ffprobe_path_in_tools).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

                self.update_status.emit(f"{ffmpeg_name} and {ffprobe_name} extracted and moved.")

                # Clean up temporary extraction directory and archive
                if os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir)
                    self.update_status.emit(f"Cleaned up temporary extraction directory: {os.path.basename(temp_extract_dir)}.")
                os.remove(temp_archive_path)
                self.update_status.emit(f"Cleaned up {ffmpeg_archive_filename}.")
            else:
                self.update_status.emit(f"{ffmpeg_name} and {ffprobe_name} already exist.")

            self.setup_finished.emit(True, "Tool setup completed successfully!")

        except requests.exceptions.RequestException as e:
            self.setup_finished.emit(False, f"Network error during tool download: {e}")
        except (zipfile.BadZipFile, tarfile.ReadError) as e:
            self.setup_finished.emit(False, f"Archive extraction error: {e}. The downloaded file might be corrupted.")
        except Exception as e:
            self.setup_finished.emit(False, f"An error occurred during tool setup: {e}")

    def _download_file(self, url, destination, tool_name):
        """Downloads a file with progress updates."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status() # Raise an exception for HTTP errors

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = int(downloaded_size * 100 / total_size)
                            self.update_progress_bar.emit(progress, f"Downloading {tool_name}: {progress}%")
            self.update_progress_bar.emit(100, f"Downloading {tool_name}: 100%")
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Failed to download {tool_name} from {url}: {e}")

    def _extract_to_temp_dir(self, archive_path, temp_extract_path):
        """Extracts a zip or tar.xz archive to a temporary directory.
        Returns the path to the actual root directory of the extracted content."""
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path) # Clean up previous temp extraction
        os.makedirs(temp_extract_path)

        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_path)
        elif archive_path.endswith('.tar.xz'):
            with tarfile.open(archive_path, 'r:xz') as tar_ref:
                tar_ref.extractall(temp_extract_path)
        else:
            raise ValueError("Unsupported archive format. Only .zip and .tar.xz are supported.")

        # Find the actual root directory inside the extracted path
        # This handles cases where extraction creates a single top-level folder
        extracted_contents = os.listdir(temp_extract_path)
        if len(extracted_contents) == 1 and os.path.isdir(os.path.join(temp_extract_path, extracted_contents[0])):
            return os.path.join(temp_extract_path, extracted_contents[0])
        return temp_extract_path # Otherwise, executables are directly in temp_extract_path


# --- Worker Thread for Downloading YouTube Video ---
class DownloadWorker(QThread):
    """
    A separate thread to run the yt-dlp download process so the GUI doesn't freeze.
    """
    # Signals to send output and status to the GUI
    update_progress = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str) # bool: success, str: message
    update_progress_bar = pyqtSignal(int, str) # value, text

    def __init__(self, url, output_path, format_choice, yt_dlp_exec, ffmpeg_exec):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.format_choice = format_choice
        self.yt_dlp_exec = yt_dlp_exec
        self.ffmpeg_exec = ffmpeg_exec

    def run(self):
        """
        The download logic that will be executed in a separate thread.
        """
        self.update_progress.emit(f"Starting download from: {self.url}\n")
        self.update_progress.emit(f"Saving to: {self.output_path}\n")
        self.update_progress_bar.emit(0, "Downloading...")

        try:
            command = [
                self.yt_dlp_exec,
                "--external-downloader", "aria2c",
                "--external-downloader-args", "-x 16 -s 16 -k 1M",
                "--ffmpeg-location", self.ffmpeg_exec,
                "-o", os.path.join(self.output_path, "%(title)s.%(ext)s"),
            ]

            if self.format_choice == "mp3":
                command.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            elif self.format_choice == "best":
                command.append("-f")
                command.append("bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best")
            else:
                command.append("-f")
                command.append(self.format_choice)

            command.append(self.url)

            # Run the subprocess and capture output in real-time
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True,
                bufsize=1, # Line-buffered
                universal_newlines=True # For cross-platform compatibility
            )

            for line in process.stdout:
                self.update_progress.emit(line) # Send each line of output to the GUI
                # Try to update the progress bar from yt-dlp output
                if "%" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if part.endswith("%"):
                                progress_str = part.replace("%", "")
                                if '.' in progress_str: # Handle float percentages
                                    progress_value = int(float(progress_str))
                                else:
                                    progress_value = int(progress_str)
                                self.update_progress_bar.emit(progress_value, f"Downloading: {progress_value}%")
                                break
                    except ValueError:
                        pass # Ignore if parsing fails

            process.wait() # Wait for the process to finish

            if process.returncode == 0:
                self.download_finished.emit(True, "Download completed successfully!")
            else:
                self.download_finished.emit(False, f"Download failed with error code: {process.returncode}")

        except FileNotFoundError:
            self.download_finished.emit(False, "Error: yt-dlp or ffmpeg executable not found. Ensure paths are correct and executables exist.")
        except Exception as e:
            self.download_finished.emit(False, f"An unexpected error occurred: {e}")

# --- Main Application Window ---
class YouTubeDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader 3.0")
        self.setGeometry(100, 100, 800, 600) # Window size

        self.setup_worker = None # Worker thread for initial setup
        self.download_worker = None # Worker thread for video download

        self.tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
        self.yt_dlp_exec = None
        self.ffmpeg_exec = None

        self.init_ui()
        self.start_tool_setup() # Start automatic tool setup

    def init_ui(self):
        """Initializes the GUI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- URL Input ---
        url_layout = QHBoxLayout()
        url_label = QLabel("Video URL:")
        url_label.setFont(QFont("Inter", 10))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube video URL here...")
        self.url_input.setFont(QFont("Inter", 10))
        self.url_input.setStyleSheet("border-radius: 8px; padding: 5px; border: 1px solid #ccc;")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # --- Format Selection and Download Button ---
        options_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_label.setFont(QFont("Inter", 10))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Best (Video & Audio MP4)", "MP3 (Audio Only)"])
        self.format_combo.setFont(QFont("Inter", 10))
        self.format_combo.setStyleSheet("border-radius: 8px; padding: 5px; border: 1px solid #ccc;")

        self.download_button = QPushButton("Download")
        self.download_button.setFont(QFont("Inter", 10, QFont.Bold))
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green */
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                border: none;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
                box-shadow: inset 1px 1px 3px rgba(0, 0, 0, 0.2);
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False) # Disable until tools are set up

        options_layout.addWidget(format_label)
        options_layout.addWidget(self.format_combo)
        options_layout.addStretch(1) # Push button to the right
        options_layout.addWidget(self.download_button)
        main_layout.addLayout(options_layout)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Initializing...")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                background-color: #e0e0e0;
                text-align: center;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                width: 20px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # --- Output Log / Status ---
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setFont(QFont("Consolas", 9))
        self.output_log.setStyleSheet("border-radius: 8px; padding: 5px; background-color: #f0f0f0;")
        main_layout.addWidget(self.output_log)

        # --- Status Bar (for short messages) ---
        self.statusBar().showMessage("Starting tool setup...")

    def start_tool_setup(self):
        """Initiates the automatic download and setup of yt-dlp and ffmpeg."""
        self.output_log.clear()
        self.output_log.append("Checking for required tools (yt-dlp, ffmpeg)...")
        self.download_button.setEnabled(False)
        self.url_input.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.progress_bar.setFormat("Setting up tools...")
        self.progress_bar.setValue(0)

        self.setup_worker = SetupWorker(self.tools_dir)
        self.setup_worker.update_status.connect(self.output_log.append)
        self.setup_worker.update_progress_bar.connect(self.progress_bar.setValue)
        self.setup_worker.update_progress_bar.connect(lambda val, text: self.progress_bar.setFormat(text))
        self.setup_worker.setup_finished.connect(self.on_tool_setup_finished)
        self.setup_worker.start()

    def on_tool_setup_finished(self, success, message):
        """Handles the completion of the tool setup process."""
        self.output_log.append(f"\n{message}")
        self.statusBar().showMessage(message, 5000)

        if success:
            self.yt_dlp_exec = find_executable("yt-dlp", [self.tools_dir])
            self.ffmpeg_exec = find_executable("ffmpeg", [self.tools_dir])

            if self.yt_dlp_exec and self.ffmpeg_exec:
                self.download_button.setEnabled(True)
                self.url_input.setEnabled(True)
                self.format_combo.setEnabled(True)
                self.progress_bar.setValue(100)
                self.progress_bar.setFormat("Tools ready. Enter URL.")
                self.statusBar().showMessage("Application ready for download.", 3000)
            else:
                QMessageBox.critical(self, "Setup Error", "Required tools not found after setup. Please check logs.")
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat("Setup Failed!")
                self.statusBar().showMessage("Error: Tools not found after setup.", 5000)
        else:
            QMessageBox.critical(self, "Tool Setup Failed", message)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Setup Failed!")
            self.statusBar().showMessage("Error: Tool setup failed.", 5000)

    def start_download(self):
        """Starts the video download process in a separate thread."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Empty Input", "Please enter a YouTube video URL.")
            return

        selected_format_text = self.format_combo.currentText()
        if "mp3" in selected_format_text.lower():
            format_choice = "mp3"
        else:
            format_choice = "best" # Default to best video/audio

        output_folder = "downloads" # Can be changed to user input later
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            self.output_log.append(f"Directory '{output_folder}' created.\n")

        self.output_log.clear()
        self.output_log.append("Starting video download process...")
        self.download_button.setEnabled(False) # Disable button during download
        self.url_input.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.progress_bar.setFormat("Downloading video...")
        self.progress_bar.setValue(0)


        # Create and start the worker thread
        self.download_worker = DownloadWorker(url, output_folder, format_choice, self.yt_dlp_exec, self.ffmpeg_exec)
        self.download_worker.update_progress.connect(self.output_log.append)
        self.download_worker.update_progress_bar.connect(self.progress_bar.setValue)
        self.download_worker.update_progress_bar.connect(lambda val, text: self.progress_bar.setFormat(text))
        self.download_worker.download_finished.connect(self.on_download_finished)
        self.download_worker.start() # Start the thread

    def on_download_finished(self, success, message):
        """Handles the completion of the video download process."""
        self.download_button.setEnabled(True) # Re-enable button
        self.url_input.setEnabled(True)
        self.format_combo.setEnabled(True)
        self.output_log.append(f"\n{message}")
        self.statusBar().showMessage(message, 5000)
        self.progress_bar.setValue(100 if success else 0)
        self.progress_bar.setFormat("Done!" if success else "Failed!")

        if not success:
            QMessageBox.critical(self, "Download Failed", message)
        else:
            QMessageBox.information(self, "Download Complete", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec_())
