# -*- coding: utf-8 -*-
"""
RSVP Reader Module - Main GUI Application
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QSlider, QSpinBox, QComboBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QSize

from .analyzer import TextAnalyzer


class RSVPReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('eTech Reading - Fast Reading System')
        self.setGeometry(100, 100, 1000, 750)
        self.setMinimumSize(900, 650)
        
        self.current_analysis = None
        self.display_sequence = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_next_word)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:pressed {
                background-color: #445ab0;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QSlider::groove:horizontal {
                background: #e0e0e0;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #667eea;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSpinBox, QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #667eea;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #667eea;
                color: white;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel('eTech Reading')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #667eea; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel('Fast Reading System - Word by word visual presentation')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(subtitle)
        
        # Tab Widget
        tabs = QTabWidget()
        
        # Tab 1: Reader
        reader_tab = self.create_reader_tab()
        tabs.addTab(reader_tab, '📖 Reader')
        
        # Tab 2: Statistics
        stats_tab = self.create_stats_tab()
        tabs.addTab(stats_tab, '📊 Statistics')
        
        layout.addWidget(tabs)
        main_widget.setLayout(layout)
    
    def create_reader_tab(self):
        """Create reader tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Input area
        input_label = QLabel('📝 Paste Text:')
        input_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText('Paste the text you want to analyze here...')
        self.text_input.setMinimumHeight(100)
        self.text_input.setMaximumHeight(140)
        
        layout.addWidget(input_label)
        layout.addWidget(self.text_input)
        
        # Controls - Grid layout
        controls_group_box = QFrame()
        controls_group_box.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; padding: 10px;")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)
        
        # Row 1: Speed Control
        speed_row = QHBoxLayout()
        speed_label = QLabel('⏱️ Reading Speed (WPM):')
        speed_label.setMaximumWidth(150)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(1000)
        self.speed_slider.setValue(300)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(150)
        self.speed_display = QLabel('300 WPM')
        self.speed_display.setMaximumWidth(60)
        self.speed_display.setStyleSheet("background: white; border: 1px solid #ddd; padding: 4px; border-radius: 3px; text-align: center;")
        self.speed_slider.valueChanged.connect(self.update_speed_display)
        
        speed_row.addWidget(speed_label)
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_display)
        controls_layout.addLayout(speed_row)
        
        # Row 2: Font Size Control
        font_row = QHBoxLayout()
        font_label = QLabel('📏 Font Size:')
        font_label.setMaximumWidth(150)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(20)
        self.font_size_spin.setMaximum(80)
        self.font_size_spin.setValue(50)
        self.font_size_spin.setSuffix(' pt')
        self.font_size_spin.setMaximumWidth(100)
        
        font_row.addWidget(font_label)
        font_row.addWidget(self.font_size_spin)
        font_row.addStretch()
        controls_layout.addLayout(font_row)
        
        controls_group_box.setLayout(controls_layout)
        layout.addWidget(controls_group_box)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)
        
        analyze_btn = QPushButton('🔍 Analyze')
        analyze_btn.setMinimumHeight(36)
        analyze_btn.clicked.connect(self.analyze_text)
        
        start_btn = QPushButton('▶️ Start')
        start_btn.setMinimumHeight(36)
        start_btn.clicked.connect(self.start_reading)
        
        pause_btn = QPushButton('⏸️ Pause')
        pause_btn.setMinimumHeight(36)
        pause_btn.clicked.connect(self.pause_reading)
        
        stop_btn = QPushButton('⏹️ Stop')
        stop_btn.setMinimumHeight(36)
        stop_btn.clicked.connect(self.stop_reading)
        
        buttons_layout.addWidget(analyze_btn, 1)
        buttons_layout.addWidget(start_btn, 1)
        buttons_layout.addWidget(pause_btn, 1)
        buttons_layout.addWidget(stop_btn, 1)
        
        layout.addLayout(buttons_layout)
        
        # Display area
        display_label = QLabel('📺 Display Area')
        display_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        self.display_frame = QFrame()
        self.display_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #667eea;
                border-radius: 6px;
                padding: 20px;
            }
        """)
        self.display_frame.setMinimumHeight(180)
        self.display_frame.setMaximumHeight(220)
        
        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(0, 0, 0, 0)
        self.word_display = QLabel('Click the "Analyze" button to analyze text')
        self.word_display.setAlignment(Qt.AlignCenter)
        word_font = QFont('Courier New')
        word_font.setPointSize(self.font_size_spin.value() // 3)
        self.word_display.setFont(word_font)
        self.word_display.setStyleSheet("color: #333;")
        display_layout.addWidget(self.word_display)
        self.display_frame.setLayout(display_layout)
        
        layout.addWidget(display_label)
        layout.addWidget(self.display_frame)
        
        # Progress
        progress_label = QLabel('📊 Progress')
        progress_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(20)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel('0 / 0 Words')
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(self.progress_label)
        
        # Analysis info
        self.info_label = QLabel('')
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 8px; border-radius: 4px; font-size: 11px;")
        self.info_label.setMaximumHeight(50)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_stats_tab(self):
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel('📈 Reading Speed Comparison')
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Speed comparison table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels(['Speed (WPM)', '100 Words', '500 Words', '1000 Words', 'Category'])
        self.stats_table.setRowCount(6)
        self.stats_table.setMaximumHeight(200)
        
        speeds = [
            (100, 'Very Slow'),
            (200, 'Slow'),
            (300, 'Normal'),
            (500, 'Fast'),
            (800, 'Very Fast'),
            (1000, 'Ultra Fast')
        ]
        
        for row, (wpm, category) in enumerate(speeds):
            self.stats_table.setItem(row, 0, QTableWidgetItem(f'{wpm}'))
            self.stats_table.setItem(row, 1, QTableWidgetItem(self.calculate_time(100, wpm)))
            self.stats_table.setItem(row, 2, QTableWidgetItem(self.calculate_time(500, wpm)))
            self.stats_table.setItem(row, 3, QTableWidgetItem(self.calculate_time(1000, wpm)))
            self.stats_table.setItem(row, 4, QTableWidgetItem(category))
        
        self.stats_table.resizeColumnsToContents()
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # Info
        info_text = QLabel(
            '<b>What is eTech Reading?</b><br><br>'
            '<b>🎯 Technology:</b> Rapid Serial Visual Presentation (RSVP)<br>'
            'Word-by-word fast visual presentation. Instead of scrolling the page, '
            'words are displayed rapidly at a fixed position.<br><br>'
            '<b>💡 Focus Point:</b> A specific letter in each word is highlighted in <span style="color: red;"><b>red</b></span>.<br>'
            'The reader does not fully read each word, but gains comprehension by looking at the focus letter.<br><br>'
            '<b>⚡ Benefits:</b><br>'
            '• Increases reading speed 2-3 times<br>'
            '• Reduces eye strain<br>'
            '• Preserves comprehension ability'
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 15px; background-color: #f0f7ff; border-left: 4px solid #667eea; border-radius: 4px; line-height: 1.6;")
        layout.addWidget(info_text)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def analyze_text(self):
        """Analyze input text"""
        text = self.text_input.toPlainText().strip()
        
        if not text:
            self.info_label.setText('⚠️ Please enter text!')
            self.info_label.setStyleSheet('color: #d32f2f; background: #ffebee; padding: 8px; border-radius: 4px;')
            return
        
        try:
            self.current_analysis = TextAnalyzer.analyze_text(text)
            
            # Generate display sequence
            self.display_sequence = []
            for sentence in self.current_analysis:
                for word_info in sentence['words']:
                    self.display_sequence.append({
                        'word': word_info['clean'],
                        'before': word_info['before'],
                        'focus_letter': word_info['focus_letter'],
                        'after': word_info['after'],
                        'sentence_index': sentence['sentence_index'],
                        'word_index': word_info['word_index'],
                        'is_last_word': word_info['word_index'] == sentence['word_count'] - 1
                    })
            
            # Calculate stats
            total_words = len(self.display_sequence)
            total_sentences = len(self.current_analysis)
            total_chars = sum(len(s['original_sentence']) for s in self.current_analysis)
            
            wpm = self.speed_slider.value()
            reading_seconds = (total_words / wpm) * 60
            minutes = int(reading_seconds // 60)
            seconds = int(reading_seconds % 60)
            
            self.progress_bar.setMaximum(total_words)
            self.info_label.setText(
                f'✅ Analysis complete | {total_sentences} sentences • {total_words} words • '
                f'{total_chars} characters | ⏱️ Reading time: {minutes}m {seconds}s'
            )
            self.info_label.setStyleSheet('color: #1b5e20; background: #e8f5e9; padding: 8px; border-radius: 4px;')
            
        except Exception as e:
            self.info_label.setText(f'❌ Error: {str(e)}')
            self.info_label.setStyleSheet('color: #d32f2f; background: #ffebee; padding: 8px; border-radius: 4px;')
    
    def update_speed_display(self):
        """Update speed display"""
        wpm = self.speed_slider.value()
        self.speed_display.setText(f'{wpm} WPM')
    
    def start_reading(self):
        """Start reading"""
        if not self.display_sequence:
            self.info_label.setText('⚠️ You must first analyze the text with "Analyze"!')
            self.info_label.setStyleSheet('color: #f57c00; background: #fff3e0; padding: 8px; border-radius: 4px;')
            return
        
        if self.is_playing and not self.is_paused:
            return
        
        self.is_playing = True
        self.is_paused = False
        
        if self.current_index == 0:
            self.display_word(0)
        
        wpm = self.speed_slider.value()
        interval = int(60000 / wpm)  # milliseconds per word
        self.timer.start(interval)
    
    def pause_reading(self):
        """Pause/Resume reading"""
        if not self.is_playing:
            return
        
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.timer.stop()
        else:
            wpm = self.speed_slider.value()
            interval = int(60000 / wpm)
            self.timer.start(interval)
    
    def stop_reading(self):
        """Stop reading"""
        self.is_playing = False
        self.is_paused = False
        self.current_index = 0
        self.timer.stop()
        
        self.word_display.setText('Reading paused')
        self.progress_bar.setValue(0)
        self.progress_label.setText('0 / 0 Words')
    
    def display_word(self, index):
        """Display word with centered focus letter"""
        if index >= len(self.display_sequence):
            self.stop_reading()
            return
        
        word = self.display_sequence[index]
        
        # Create display with centered focus
        before = word['before']
        focus = word['focus_letter']
        after = word['after']
        
        html = f'{before}<span style="color: red; font-weight: bold;">{focus}</span>{after}'
        
        self.word_display.setText(html)
        
        # Update font size from spinner
        word_font = QFont('Courier New')
        word_font.setPointSize(self.font_size_spin.value())
        self.word_display.setFont(word_font)
        
        # Update progress
        self.current_index = index
        self.progress_bar.setValue(index + 1)
        self.progress_label.setText(f'{index + 1} / {len(self.display_sequence)} Words')
    
    def display_next_word(self):
        """Display next word in sequence"""
        if self.is_paused or not self.is_playing:
            return
        
        self.current_index += 1
        if self.current_index >= len(self.display_sequence):
            self.stop_reading()
            self.info_label.setText('✅ Reading complete! Happy reading...')
            self.info_label.setStyleSheet('color: #1b5e20; background: #e8f5e9; padding: 8px; border-radius: 4px;')
        else:
            self.display_word(self.current_index)
    
    @staticmethod
    def calculate_time(words, wpm):
        """Calculate reading time"""
        seconds = (words / wpm) * 60
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes}m {secs}s' if minutes > 0 else f'{secs}s'
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Space:
            if self.is_playing:
                self.pause_reading()
            else:
                self.start_reading()
        elif event.key() == Qt.Key_Escape:
            self.stop_reading()


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    reader = RSVPReader()
    reader.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
