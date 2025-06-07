import sys
import psutil
import subprocess
import threading
import time
import cv2
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QHBoxLayout)
from PyQt5.QtCore import QTimer

# Helper function to get CPU temp (Pi-specific)
def get_cpu_temp():
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(temp.replace("temp=", "").replace("'C\n", ""))
    except Exception:
        return 0.0

# Helper function for stress test
def stress_test():
    def cpu_load():
        x = 0
        while running[0]:
            x += np.sin(x)

    running = [True]
    threads = [threading.Thread(target=cpu_load) for _ in range(psutil.cpu_count())]
    for t in threads:
        t.start()
    time.sleep(10)
    running[0] = False
    for t in threads:
        t.join()

# Helper function for internet speed test
def run_speed_test(label):
    label.setText("Running speed test...")
    try:
        result = subprocess.check_output(["speedtest-cli", "--simple"]).decode()
        label.setText(result)
    except Exception as e:
        label.setText(f"Error: {e}")

# Main App
class PiBenchmarkApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daniel's Raspberry Pi Jam - Benchmark Suite")
        self.resize(1200, 800)

        layout = QVBoxLayout()

        # CPU/RAM/Temp labels
        self.cpu_label = QLabel("CPU Usage: ")
        self.ram_label = QLabel("RAM Usage: ")
        self.temp_label = QLabel("CPU Temp: ")

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.temp_label)

        # Plot widgets
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.ram_plot = pg.PlotWidget(title="RAM Usage (%)")
        self.net_plot = pg.PlotWidget(title="Network I/O (MB)")

        layout.addWidget(self.cpu_plot)
        layout.addWidget(self.ram_plot)
        layout.addWidget(self.net_plot)

        # Buttons
        button_layout = QHBoxLayout()

        stress_btn = QPushButton("Run Stress Test")
        stress_btn.clicked.connect(lambda: threading.Thread(target=stress_test).start())
        button_layout.addWidget(stress_btn)

        self.speed_label = QLabel("Speed Test: Not Run")
        speed_btn = QPushButton("Run Internet Speed Test")
        speed_btn.clicked.connect(lambda: threading.Thread(target=run_speed_test, args=(self.speed_label,)).start())
        button_layout.addWidget(speed_btn)

        layout.addLayout(button_layout)
        layout.addWidget(self.speed_label)

        # Video test
        self.video_label = QLabel("Video FPS: Not Running")
        video_btn = QPushButton("Run Video Render Test")
        video_btn.clicked.connect(lambda: threading.Thread(target=self.video_test).start())
        layout.addWidget(video_btn)
        layout.addWidget(self.video_label)

        self.setLayout(layout)

        # Plot data buffers
        self.cpu_data = []
        self.ram_data = []
        self.net_in_data = []
        self.net_out_data = []

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_stats(self):
        # CPU
        cpu = psutil.cpu_percent()
        self.cpu_label.setText(f"CPU Usage: {cpu:.1f}%")
        self.cpu_data.append(cpu)
        if len(self.cpu_data) > 60:
            self.cpu_data.pop(0)
        self.cpu_plot.plot(self.cpu_data, clear=True)

        # RAM
        ram = psutil.virtual_memory().percent
        self.ram_label.setText(f"RAM Usage: {ram:.1f}%")
        self.ram_data.append(ram)
        if len(self.ram_data) > 60:
            self.ram_data.pop(0)
        self.ram_plot.plot(self.ram_data, clear=True)

        # Temp
        temp = get_cpu_temp()
        self.temp_label.setText(f"CPU Temp: {temp:.1f}°C")

        # Network
        net_io = psutil.net_io_counters()
        net_in = net_io.bytes_recv / (1024 * 1024)  # MB
        net_out = net_io.bytes_sent / (1024 * 1024)  # MB
        self.net_in_data.append(net_in)
        self.net_out_data.append(net_out)
        if len(self.net_in_data) > 60:
            self.net_in_data.pop(0)
            self.net_out_data.pop(0)
        self.net_plot.plot(self.net_in_data, pen='g', clear=True)
        self.net_plot.plot(self.net_out_data, pen='r')

    def video_test(self):
        cap = cv2.VideoCapture(0)  # Open webcam
        if not cap.isOpened():
            self.video_label.setText("Error: No camera found.")
            return

        frame_count = 0
        start_time = time.time()
        while time.time() - start_time < 10:  # Run for 10 seconds
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            # Optional: Display frame in cv2.imshow() (not needed here)

        cap.release()
        fps = frame_count / 10.0
        self.video_label.setText(f"Video FPS: {fps:.1f} fps")

# Main entry
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PiBenchmarkApp()
    window.show()
    sys.exit(app.exec_())
