# YouTube Downloader

🚀 **Overview**

This is a cross-platform YouTube video and audio downloader application built with Python and PyQt5. It provides a modern, intuitive graphical user interface (GUI) for easy downloading, leveraging the powerful `yt-dlp` library and `FFmpeg` for media processing. The application features automatic setup of `yt-dlp` and `FFmpeg`, making it incredibly user-friendly.

---

✨ **Features**

- **GUI Interface**: User-friendly graphical interface built with PyQt5.  
- **Video & Audio Download**: Download YouTube videos in various qualities or extract audio as MP3.  
- **Automatic Tool Setup**: Automatically downloads and sets up `yt-dlp` and `FFmpeg` executables upon first run. No manual installation of these tools is required for the end-user!  
- **Cross-Platform**: Designed to work seamlessly on Windows, macOS, and Linux.  
- **Real-time Progress**: Displays download progress and status in a dedicated log area and progress bar.  
- **Robust Error Handling**: Provides clear messages for network issues, missing tools, or download failures.

---

🛠️ **Installation**

### Prerequisites

- Python 3.x installed on your system.

### Steps

Clone the repository (or download the ZIP):

```bash
git clone https://github.com/husenhu/YT-Downloader-3.0.git
cd YT-Downloader-3.0
```

Install Python dependencies:

```pip install PyQt5 yt-dlp requests```

🚀 How to Run
Navigate to the project directory in your terminal:

```cd YT-Downloader-3.0```

Run the main application script:

```python main.py```

💡 Usage
- Automatic Tool Setup: Upon the first launch, the application will automatically check for, download, and set up yt-dlp and FFmpeg executables in a tools/ subfolder. This process will be displayed in the application's log area and progress bar. Please wait for this to complete.
- Enter URL: Once the tools are ready, paste the YouTube video URL into the "Video URL" input field.
- Select Format: Choose your desired download format from the dropdown menu ("Best (Video & Audio MP4)" or "MP3 (Audio Only)").
- Start Download: Click the "Download" button.
- Monitor Progress: The download progress will be shown in the log area and the progress bar.
- Find Downloads: All downloaded files will be saved in a downloads/ folder created in the same directory as the application.

🌐 How it Works
The application uses yt-dlp as the core downloader. yt-dlp is a command-line program that downloads videos from YouTube and many other video sites. FFmpeg is used by yt-dlp for various media manipulation tasks, such as converting video to MP3 or merging audio and video streams.
The Python script dynamically locates yt-dlp and FFmpeg within the tools/ directory. For multi-OS compatibility, it intelligently handles different executable names (e.g., .exe for Windows) and sets appropriate file permissions for Linux/macOS. The download and extraction of these tools are handled in a separate thread to keep the GUI responsive.

🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, bug reports, or want to add new features, please feel free to:
Fork the repository.
Create a new branch (git checkout -b feature/YourFeature).
Make your changes.
Commit your changes (git commit -m 'Add some feature').
Push to the branch (git push origin feature/YourFeature).
Open a Pull Request.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

Disclaimer: This tool is intended for personal use and for downloading content where you have the necessary rights or permissions. Please respect copyright laws and terms of service of the platforms you are downloading from.
