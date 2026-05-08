# -*- coding: utf-8 -*-
__version__ = "3.0.1"

import sys
import webbrowser
from os import path
from threading import Thread

import requests
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon, QFont
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy,
    QSpacerItem
)

import general
import livedb
from coursera_dl import main_f
from utils import process_notification_html


def _about_dialog_text(version):
    return f"""
    <b>Coursera Full Course Downloader</b><br>
    Version: {version}<br><br>
    Developed by: Abdul Sheikh<br>
    Department of CSE(AI),<br>VIT ,Pune<br>
    Email: <u>abdulsheikh5687@gmail.com</u>
    """


def _help_dialog_text():
    return """
    <b>USING THE PROGRAM:</b><br>
    Using the program is very easy. Just enter the necessary things and hit download. Your download will start in a command prompt window. You can see the download progress in the command prompt window. It will take some moments for the processing to finish, and download to start.<br><br>
    Use CTRL+V to paste URL.<br><br>
    <b>STOP DOWNLOAD:</b><br>
    Press CTRL+C on the command prompt window. It can take several seconds to stop the download in cases. Do not press CTRL+C multiple times.<br><br>
    <b>RESUME DOWNLOAD:</b><br>
    If you want to RESUME the download later on, just provide the same information and download folder as before, and click on the Resume button instead of download. Your download will be resumed from previous position.<br><br>
    <b>IF THE DOWNLOAD SCREEN STALLS:</b><br>
    If the download screen does not change and does not show update for some time, then click on the command prompt window and press any button, your download should resume.<br><br>
    <b>You can not download an entire specialization. For specialization enter url of the course within it.</b><br><br>
    <b>FOUND A BUG?</b> Feel free to email at <u>abdulsheikh5687@gmail.com</u>
    """


class ResponsiveGridLayout(QGridLayout):
    """Custom grid layout that handles resizing better"""
    pass


class MainWindow(QMainWindow):
    show_update_message = pyqtSignal(str, str, str)
    show_notification_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursera Full Course Downloader")
        self.setMinimumSize(500, 550)  # Smaller minimum size for laptops
        self.resize(650, 600)
        
        # Enable maximize
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        # Set icon
        icon_path = path.abspath(path.join(path.dirname(__file__), "icon/icon.ico"))
        if path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.shouldResume = False
        self.notification = ""

        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        self.allowed_browsers = general.ALLOWED_BROWSERS

        from localdb import SimpleDB
        self.localdb = SimpleDB("data.bin")
        self.argdict = self.localdb.get_full_db()["argdict"]

        self.initUI()

        self.show_update_message.connect(self.display_update_message)
        # self.show_notification_signal.connect(self.show_notification)

        # Thread(target=self.connect_to_db, daemon=True).start()

    def initUI(self):
        # Menu Bar
        menubar = self.menuBar()
        menu = menubar.addMenu("Menu")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help)
        menu.addAction(about_action)
        menu.addAction(help_action)

        # Central Widget with Scroll Area for small screens
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        central_widget = QWidget()
        scroll.setWidget(central_widget)
        self.setCentralWidget(scroll)
        
        # Main Layout - Vertical with proper spacing
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        
        # ========== HEADER ==========
        header = QLabel("🎓 COURSERA FULL COURSE DOWNLOADER")
        header.setAlignment(Qt.AlignCenter)
        header.setWordWrap(True)  # Allow text wrap on small screens
        header.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(header)
        
        # ========== INFO BANNER ==========
        info = QLabel(
            "ℹ️ You must be logged in on coursera.org in a browser. "
            "You can only download courses that you are enrolled in."
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                color: #856404;
                padding: 8px;
                border-radius: 6px;
                font-size: 11px;
            }
        """)
        main_layout.addWidget(info)
        
        # ========== BROWSER SELECTION ==========
        browser_group = QGroupBox("Browser Authentication")
        browser_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(10)
        
        browser_label = QLabel("Select browser where you are logged in:")
        browser_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(self.allowed_browsers)
        self.browser_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        default_browser = self.localdb.read("browser")
        if default_browser in self.allowed_browsers:
            self.browser_combo.setCurrentText(default_browser)
        
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        browser_group.setLayout(browser_layout)
        main_layout.addWidget(browser_group)
        
        # ========== COURSE INFO - Responsive Grid ==========
        course_group = QGroupBox("Course Information")
        course_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        # Use QVBoxLayout for better responsiveness on small screens
        course_inner_layout = QVBoxLayout()
        course_inner_layout.setSpacing(12)
        
        # URL Row
        url_widget = QWidget()
        url_layout = QHBoxLayout()
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_widget.setLayout(url_layout)
        
        url_label = QLabel("Course URL:")
        url_label.setMinimumWidth(120)
        self.classname_edit = QLineEdit()
        self.classname_edit.setText(self.localdb.read("argdict")["classname"])
        self.classname_edit.setPlaceholderText("https://www.coursera.org/learn/course-name")
        self.classname_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.classname_edit)
        course_inner_layout.addWidget(url_widget)
        
        # Folder Row
        folder_widget = QWidget()
        folder_layout = QHBoxLayout()
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_widget.setLayout(folder_layout)
        
        folder_label = QLabel("Download Folder:")
        folder_label.setMinimumWidth(120)
        self.path_btn = QPushButton("📁 Browse Folder")
        self.path_btn.clicked.connect(self.getPath)
        
        folder_layout.addStretch()
        folder_layout.addWidget(self.path_btn)
        folder_layout.addStretch()
        course_inner_layout.addWidget(folder_widget)
        
        # Path Display Row
        path_widget = QWidget()
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_widget.setLayout(path_layout)
        
        path_spacer = QLabel("")
        path_spacer.setMinimumWidth(120)
        self.path_label = QLabel(self.localdb.read("argdict")["path"])
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #666; padding: 6px; background: #f8f9fa; border-radius: 4px;")
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        path_layout.addWidget(path_spacer)
        path_layout.addWidget(self.path_label)
        course_inner_layout.addWidget(path_widget)
        
        course_group.setLayout(course_inner_layout)
        main_layout.addWidget(course_group)
        
        # ========== VIDEO QUALITY ==========
        quality_group = QGroupBox("Video Quality")
        quality_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QRadioButton {
                spacing: 8px;
            }
        """)
        
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(20)
        
        self.res_720 = QRadioButton("720p (HD)")
        self.res_540 = QRadioButton("540p")
        self.res_360 = QRadioButton("360p")
        
        # Make radio buttons responsive
        for rb in [self.res_720, self.res_540, self.res_360]:
            rb.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        quality_layout.addWidget(self.res_720)
        quality_layout.addWidget(self.res_540)
        quality_layout.addWidget(self.res_360)
        quality_layout.addStretch()
        quality_group.setLayout(quality_layout)
        
        # Set default
        if self.localdb.read("argdict")["video_resolution"] == "540p":
            self.res_540.setChecked(True)
        elif self.localdb.read("argdict")["video_resolution"] == "360p":
            self.res_360.setChecked(True)
        else:
            self.res_720.setChecked(True)
        
        main_layout.addWidget(quality_group)
        
        # ========== SUBTITLE LANGUAGE ==========
        subtitle_group = QGroupBox("Subtitle Language")
        subtitle_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        
        subtitle_layout = QHBoxLayout()
        subtitle_layout.setSpacing(10)
        
        lang_label = QLabel("Select subtitle language:")
        lang_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        self.sl_combo = QComboBox()
        self.sl_combo.addItems(sorted(self.sllangschoices.keys()))
        self.sl_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        key = next(
            (k for k, v in self.sllangschoices.items() 
             if v == self.localdb.read("argdict")["sl"]),
            None,
        )
        self.sl_combo.setCurrentText(key if key else "English")
        
        subtitle_layout.addWidget(lang_label)
        subtitle_layout.addWidget(self.sl_combo)
        subtitle_group.setLayout(subtitle_layout)
        main_layout.addWidget(subtitle_group)
        
        # ========== BUTTONS - Responsive centering ==========
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_widget.setLayout(buttons_layout)
        
        self.resume_btn = QPushButton("⏸️ Resume Download")
        self.resume_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8590c;
            }
        """)
        self.resume_btn.clicked.connect(self.resumeBtnHandler)
        
        self.download_btn = QPushButton("⬇️ Download Course")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.download_btn.clicked.connect(self.downloadBtnHandler)
        
        # Add stretch to center buttons
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.resume_btn)
        buttons_layout.addWidget(self.download_btn)
        buttons_layout.addStretch()
        
        main_layout.addWidget(buttons_widget)
        
        # ========== NOTIFICATION ==========
        # self.notification_area = QTextBrowser()
        # self.notification_area.setMaximumHeight(100)
        # self.notification_area.setVisible(False)
        # self.notification_area.setStyleSheet("""
        #     QTextBrowser {
        #         background-color: #f8f9fa;
        #         border: 1px solid #ddd;
        #         border-radius: 6px;
        #         padding: 8px;
        #     }
        # """)
        # main_layout.addWidget(self.notification_area)
        
        # ========== FOOTER ==========
        footer = QWidget()
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(5)
        footer.setLayout(footer_layout)
        
        support = QLabel(
            '❤️ Like the software? You can connect with me on'
            '<a href="https://www.linkedin.com/in/abdul-sheikh-727b60246/" style="color:#fd7e14;">Linkedin</a>'
        )
        support.setOpenExternalLinks(True)
        support.setAlignment(Qt.AlignCenter)
        support.setWordWrap(True)
        
        feedback = QLabel(
            'Not quite liking the software? Send me feedback at <u>abdulsheikh5687@gmail.com</u>'
        )
        feedback.setAlignment(Qt.AlignCenter)
        feedback.setWordWrap(True)
        
        self.footer_link = QLabel(
            '<a href="https://coursera-downloader.rf.gd/" style="color:#007bff;">🌐 coursera-downloader.rf.gd</a>'
        )
        self.footer_link.setAlignment(Qt.AlignCenter)
        self.footer_link.setOpenExternalLinks(True)
        
        footer_layout.addWidget(support)
        footer_layout.addWidget(feedback)
        footer_layout.addWidget(self.footer_link)
        
        main_layout.addWidget(footer)
        
        # Add spacer at bottom for small screens
        main_layout.addStretch()

    # ========== ALL ORIGINAL FUNCTIONS (UNCHANGED) ==========
    def connect_to_db(self):
        id_token = livedb.authenticate_anonymously()
        livedb.log_usage_info(id_token)

        self.notification = livedb.get_notification(id_token)
        self.show_notification_signal.emit(self.notification)

        update_available, latest_version, latest_version_build_url, update_msg = (
            livedb.check_for_update(id_token)
        )

        if update_available:
            if self.localdb.read("show_update_prompt") != "false":
                self.show_update_message.emit(
                    latest_version, latest_version_build_url, update_msg
                )
            else:
                current_text = self.footer_link.text()
                self.footer_link.setText(
                    current_text + f' | <a href="{latest_version_build_url}" style="color:#fd7e14;">Update available!</a>'
                )

    def display_update_message(self, latest_version, latest_version_build_url=None, update_msg=None):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(
            f"A new version ({latest_version}) is available. Please update the app."
            f"\n\n{f'Update log: {update_msg}' if update_msg else ''}"
        )
        update_btn = msg_box.addButton("Update", QMessageBox.AcceptRole)
        dont_show_again_btn = msg_box.addButton("Don't show again", QMessageBox.DestructiveRole)
        msg_box.addButton("Later", QMessageBox.RejectRole)
        msg_box.exec_()
        clicked = msg_box.clickedButton()
        if clicked == update_btn and latest_version_build_url:
            webbrowser.open(latest_version_build_url)
        elif clicked == dont_show_again_btn:
            self.localdb.create("show_update_prompt", "false")

    def show_notification(self, notification):
        self.notification = notification
        if self.notification == "":
            self.notification_area.setVisible(False)
        else:
            processed_notification = process_notification_html(self.notification)
            self.notification_area.setHtml(processed_notification)
            self.notification_area.setVisible(True)
            self.notification_area.setOpenExternalLinks(True)
            self.notification_area.setCursor(QCursor(Qt.PointingHandCursor))
            self.notification_area.anchorClicked.connect(
                lambda url: webbrowser.open(url.toString())
            )

    def show_about(self):
        about_text = _about_dialog_text(__version__)
        dlg = QMessageBox(self)
        dlg.setWindowTitle("About - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(about_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def show_help(self):
        help_text = _help_dialog_text()
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(help_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def downloadBtnHandler(self):
        browser = self.browser_combo.currentText()
        cauth = general.loadcauth("coursera.org", browser)
        if cauth == "":
            QMessageBox.warning(
                self,
                "Error",
                "Could not load authentication from the browser.\nPlease make sure you are logged in on coursera.org in the selected browser and running the application as administrator.",
            )
            return

        self.localdb.update("argdict.ca", cauth)
        self.localdb.update("browser", browser)
        self.localdb.update("argdict.classname", self.classname_edit.text())
        self.localdb.update("argdict.path", self.path_label.text())
        
        if self.res_720.isChecked():
            self.localdb.update("argdict.video_resolution", "720p")
        elif self.res_540.isChecked():
            self.localdb.update("argdict.video_resolution", "540p")
        else:
            self.localdb.update("argdict.video_resolution", "360p")
        self.localdb.update("argdict.sl", self.sl_combo.currentText())

        if self.localdb.read("argdict")["path"] == "":
            QMessageBox.warning(self, "Error", "NO FOLDER SPECIFIED. PLEASE SELECT A FOLDER")
            return

        self.argdict = {}
        for key, value in self.localdb.get_full_db()["argdict"].items():
            if key == "classname":
                courseurl = self.localdb.read("argdict")["classname"]
                cname = general.urltoclassname(courseurl)
                if cname == "":
                    QMessageBox.warning(self, "Error", "INVALID COURSE NAME/ HOME PAGE URL")
                    return
                self.argdict[key] = cname
                continue
            if key == "sl":
                langcode = self.sllangschoices[self.localdb.read("argdict")["sl"]]
                if langcode == "":
                    self.argdict["ignore-formats"] = "srt"
                    self.argdict[key] = "en"
                    continue
                else:
                    self.argdict[key] = langcode
                    continue
            self.argdict[key] = value

        self.localdb.update("argdict", self.argdict)

        cmd = []
        self.argdict = general.move_to_first(self.argdict, "ca")
        for item in self.argdict.items():
            if (item[0] == "video_resolution") or (item[0] == "path"):
                flag = "--" + item[0]
            else:
                flag = "-" + item[0]
            flag = flag.replace("_", "-")
            if "classname" not in flag:
                cmd.append(flag)
            cmd.append(item[1])

        cmd.append("--download-quizzes")
        cmd.append("--download-notebooks")
        cmd.append("--disable-url-skipping")
        cmd.append("--unrestricted-filenames")
        cmd.append("--combined-section-lectures-nums")
        cmd.append("--jobs")
        cmd.append("1")

        if self.shouldResume:
            cmd.append("--resume")
            cmd.append("--cache-syllabus")

        try:
            QMessageBox.information(self, "Download", "INITIALIZING DOWNLOAD... PRESS CTRL+C TO STOP DOWNLOAD\nCheck the console for progress.")
            main_f(cmd)
        except KeyboardInterrupt:
            QMessageBox.information(self, "Stopped", "DOWNLOAD STOPPED, YOU CAN RESUME YOUR DOWNLOAD LATER")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(
                self,
                "Connection Error",
                "FAILED TO CONNECT TO COURSES SERVER. PLEASE CHECK YOUR INTERNET CONNECTION AND TRY AGAIN.",
            )
        except requests.exceptions.HTTPError as e:
            QMessageBox.warning(
                self,
                "HTTP Error",
                f"HTTP ERROR: {e}\nMAKE SURE YOU ARE LOGGED IN ON coursera.org ON A BROWSER AND YOU ARE ENROLLED INTO THE COURSE",
            )
        except requests.exceptions.SSLError as e:
            QMessageBox.warning(self, "SSL Error", f"SSL ERROR: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"SOMETHING WENT WRONG, PLEASE TRY AGAIN\n{e}")

    def resumeBtnHandler(self):
        self.shouldResume = True
        self.downloadBtnHandler()
        self.shouldResume = False

    def getPath(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Download Folder", "")
        if dir_path:
            self.path_label.setText(dir_path)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())