class GuiUsbCamera extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.recording = false;

    this.videoElement = document.getElementById('webcam');
    this.stopButton = document.getElementById('stopWebcamButton');
    this.startButton = document.getElementById('startWebcamButton');
    this.startRecordingButton = document.getElementById('startRecordingButton');
    this.stopRecordingButton = document.getElementById('stopRecordingButton');
    this.saveRecordingButton = document.getElementById('saveRecordingButton');
    this.videoSourceSelect = document.getElementById('videoSource');
    this.testMicButton = document.getElementById('testMicButton');
    
    this.stopButton.onclick = (event) => { this.stopWebcam() };
    this.startButton.onclick = (event) => { console.log('start_button'); this.startWebcam() };
    this.startRecordingButton.onclick = (event) => { this.startRecording() };
    this.stopRecordingButton.onclick = (event) => { this.stopRecording() };
    this.saveRecordingButton.onclick = (event) => { this.saveRecording() };
    this.videoSourceSelect.onchange = (event) => { this.startWebcam() };
    this.testMicButton.onclick = (event) => { this.testMicrophone() };

    this.mediaRecorder;
    this.recordedChunks = [];
    this.currentStream;
    this.audioStream;

    // TODO: add something to prevent autostart if desired
    this.getVideoSources();
    this.startWebcam();
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log('GuiUsbCamera call', msg);
    if (msg.cmd == 'set_record') {
      if (!this.recording && msg.state) {
        this.startRecording();
      }
      else if (this.recording && !msg.state) {
        this.stopRecording();
      }
      else {
        console.log('recorder parameter out of sync somehow');
      }
    }
    else if (msg.cmd == 'save_file') {
      console.log(msg)
      if (this.saveRecordingButton.disabled) {
        return
      }
      if ('filename' in msg) {
        this.saveRecording(msg.filename);
      }
      else {
        this.saveRecording();
      }
    }
    else {
      console.log('unknown command to GuiUsbCamera', msg);
    }
  }

  // Function to start the webcam with selected video source and default to 1080p
  async startWebcam() {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(track => track.stop());
    }
    this.videoSource = this.videoSourceSelect.value;
    this.constraints = {
      video: {
        deviceId: this.videoSource ? { exact: this.videoSource } : undefined,
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: true
    };
    try {
      const stream = await navigator.mediaDevices.getUserMedia(this.constraints);
      const videoTracks = stream.getVideoTracks();
      const audioTracks = stream.getAudioTracks();
      this.videoElement.srcObject = new MediaStream(videoTracks); // Only attach video to the video element;

      this.currentStream = stream;
      this.audioStream = new MediaStream(stream.getAudioTracks());

      this.startButton.disabled = true;
      this.stopButton.disabled = false;
    } catch (error) {
      console.error('Error accessing webcam:', error);
      alert('Unable to access webcam. Please allow camera access.');
    }
  }

  // Function to test the microphone
  async testMicrophone() {
    const micStream = new MediaStream(this.audioStream.getAudioTracks());
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const micSource = audioContext.createMediaStreamSource(micStream);
    const analyser = audioContext.createAnalyser();

    micSource.connect(analyser);
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function visualizeMic() {
      analyser.getByteFrequencyData(dataArray);
      const volume = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
      console.log(`Microphone volume: ${volume}`);
      requestAnimationFrame(visualizeMic);
    }

    visualizeMic();
  }

  // Function to stop the webcam
  stopWebcam () {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(track => track.stop());
      this.videoElement.srcObject = null;
      console.log('Webcam stopped');
    }
    this.startButton.disabled = false;
    this.stopButton.disabled = true;
  }

  // Function to populate video source options
  async getVideoSources() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');

      this.videoSourceSelect.innerHTML = '';
      videoDevices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.deviceId;
        option.text = device.label || `Camera ${this.videoSourceSelect.length + 1}`;
        this.videoSourceSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Error getting video sources:', error);
    }
  }

  // Function to start recording
  startRecording() {
    if (this.currentStream) {
      this.mediaRecorder = new MediaRecorder(this.currentStream);
      this.recordedChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };

      this.mediaRecorder.start();
      console.log('Recording started');

      this.recording = true;
      this.startRecordingButton.disabled = true;
      this.stopRecordingButton.disabled = false;
      this.saveRecordingButton.disabled = true;
    }

  }

  // Function to stop recording
  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
      console.log('Recording stopped');

      this.recording = false;
      this.startRecordingButton.disabled = false;
      this.stopRecordingButton.disabled = true;
      this.saveRecordingButton.disabled = false;
    }
  }

  // Function to save the recording
  saveRecording(_filename) {
    let filename
    if (typeof _filename === 'string') {
      filename = _filename + '.webm'
    }
    else {
      filename = 'recording.webm'
    }
    const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    console.log('Recording saved');
  }
}






