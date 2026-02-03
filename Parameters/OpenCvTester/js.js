class OpenCvTester extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.pid = param.pid;
    this.currentMode = 'qrcode';
    this.currentImageData = null;
    this.lastResults = [];
    this.webcamStream = null;
    this.webcamActive = false;

    // Get DOM elements
    this.canvas = gid(`${this.pid}_canvas`);
    this.video = gid(`${this.pid}_video`);
    this.tempCanvas = gid(`${this.pid}_temp_canvas`);
    this.status = gid(`${this.pid}_status`);
    this.resultsBody = gid(`${this.pid}_results_body`);
    this.modeList = gid(`${this.pid}_mode_list`);
    this.fileInput = gid(`${this.pid}_file_input`);
    this.cameraUrl = gid(`${this.pid}_camera_url`);

    // Buttons
    this.browseBtn = gid(`${this.pid}_browse_btn`);
    this.processBtn = gid(`${this.pid}_process_btn`);
    this.captureBtn = gid(`${this.pid}_capture_btn`);
    this.exportBtn = gid(`${this.pid}_export_btn`);
    this.sendBtn = gid(`${this.pid}_send_btn`);
    this.clearBtn = gid(`${this.pid}_clear_btn`);
    this.startWebcamBtn = gid(`${this.pid}_start_webcam_btn`);
    this.stopWebcamBtn = gid(`${this.pid}_stop_webcam_btn`);

    // Source radios
    this.sourceUpload = gid(`${this.pid}_source_upload`);
    this.sourceWebcam = gid(`${this.pid}_source_webcam`);
    this.sourceUrl = gid(`${this.pid}_source_url`);

    // Settings panels
    this.settingsPanels = {
      qrcode: gid(`${this.pid}_qrcode_settings`),
      contour: gid(`${this.pid}_contour_settings`),
      color: gid(`${this.pid}_color_settings`),
      shape: gid(`${this.pid}_shape_settings`)
    };

    // Help panels
    this.helpToggle = gid(`${this.pid}_help_toggle`);
    this.helpPanels = {
      qrcode: gid(`${this.pid}_help_qrcode`),
      contour: gid(`${this.pid}_help_contour`),
      color: gid(`${this.pid}_help_color`),
      shape: gid(`${this.pid}_help_shape`)
    };
    this.helpVisible = false;

    // Processing overlay
    this.processingOverlay = gid(`${this.pid}_processing_overlay`);
    this.isProcessing = false;

    this.setupEventListeners();
    this.setupSliderListeners();
  }

  getHTML(param) {
    return `{{ html }}`
  }

  setupEventListeners() {
    // File browse button
    this.browseBtn.addEventListener('click', () => {
      this.fileInput.click();
    });

    // File input change
    this.fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        this.loadImageFile(e.target.files[0]);
      }
    });

    // Process button
    this.processBtn.addEventListener('click', () => {
      this.processCurrentImage();
    });

    // Capture button - works for both webcam and URL
    this.captureBtn.addEventListener('click', () => {
      this.captureFrame();
    });

    // Start webcam
    this.startWebcamBtn.addEventListener('click', () => {
      this.startWebcam();
    });

    // Stop webcam
    this.stopWebcamBtn.addEventListener('click', () => {
      this.stopWebcam();
    });

    // Mode selection
    this.modeList.querySelectorAll('.opencv-mode-item').forEach(item => {
      item.addEventListener('click', () => {
        const mode = item.dataset.mode;
        this.setMode(mode);
        item.querySelector('input[type="radio"]').checked = true;
      });
    });

    // Export JSON
    this.exportBtn.addEventListener('click', () => {
      this.exportResults();
    });

    // Send to output
    this.sendBtn.addEventListener('click', () => {
      this.sendToOutput();
    });

    // Clear results
    this.clearBtn.addEventListener('click', () => {
      this.clearResults();
    });

    // Settings change listeners for contour
    ['canny_low', 'canny_high', 'min_area', 'max_area'].forEach(setting => {
      const el = gid(`${this.pid}_${setting}`);
      if (el) {
        el.addEventListener('change', () => this.updateContourSettings());
      }
    });

    // Settings change listeners for shape
    ['min_radius', 'max_radius', 'min_dist', 'param2'].forEach(setting => {
      const el = gid(`${this.pid}_${setting}`);
      if (el) {
        el.addEventListener('change', () => this.updateShapeSettings());
      }
    });

    // Help toggle
    this.helpToggle.addEventListener('click', () => {
      this.toggleHelp();
    });
  }

  setupSliderListeners() {
    // HSV sliders with live value display
    ['h_low', 'h_high', 's_low', 's_high', 'v_low', 'v_high'].forEach(setting => {
      const slider = gid(`${this.pid}_${setting}`);
      const valDisplay = gid(`${this.pid}_${setting}_val`);
      if (slider && valDisplay) {
        slider.addEventListener('input', () => {
          valDisplay.textContent = slider.value;
        });
        slider.addEventListener('change', () => {
          this.updateColorSettings();
        });
      }
    });
  }

  setMode(mode) {
    this.currentMode = mode;

    // Update UI
    this.modeList.querySelectorAll('.opencv-mode-item').forEach(item => {
      item.classList.remove('active');
      if (item.dataset.mode === mode) {
        item.classList.add('active');
      }
    });

    // Show/hide settings panels
    Object.keys(this.settingsPanels).forEach(key => {
      if (this.settingsPanels[key]) {
        this.settingsPanels[key].style.display = (key === mode) ? 'flex' : 'none';
      }
    });

    // Show/hide help panels (only if help is visible)
    Object.keys(this.helpPanels).forEach(key => {
      if (this.helpPanels[key]) {
        const shouldShow = this.helpVisible && (key === mode);
        this.helpPanels[key].classList.toggle('visible', shouldShow);
      }
    });

    // Send mode change to backend
    this.sendCommand({ cmd: 'set_mode', mode: mode });

    this.setStatus(`Mode changed to: ${mode}`);
  }

  toggleHelp() {
    this.helpVisible = !this.helpVisible;
    this.helpToggle.classList.toggle('active', this.helpVisible);

    // Show/hide current mode's help panel
    Object.keys(this.helpPanels).forEach(key => {
      if (this.helpPanels[key]) {
        const shouldShow = this.helpVisible && (key === this.currentMode);
        this.helpPanels[key].classList.toggle('visible', shouldShow);
      }
    });
  }

  loadImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      this.currentImageData = e.target.result;
      this.showImage();
      this.canvas.src = this.currentImageData;
      this.setStatus(`Loaded: ${file.name}`);
    };
    reader.readAsDataURL(file);
  }

  async startWebcam() {
    try {
      this.setStatus('Starting webcam...');

      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'environment' // Prefer back camera on mobile
        }
      };

      this.webcamStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.webcamStream;
      this.webcamActive = true;

      // Show video, hide image
      this.video.style.display = 'block';
      this.canvas.style.display = 'none';

      // Update buttons
      this.startWebcamBtn.style.display = 'none';
      this.stopWebcamBtn.style.display = 'inline-block';

      this.setStatus('Webcam started - Click Capture to take a frame');
    } catch (err) {
      console.error('Webcam error:', err);
      this.setStatus(`Webcam error: ${err.message}`);
    }
  }

  stopWebcam() {
    if (this.webcamStream) {
      this.webcamStream.getTracks().forEach(track => track.stop());
      this.webcamStream = null;
    }
    this.webcamActive = false;
    this.video.srcObject = null;

    // Hide video, show image
    this.video.style.display = 'none';
    this.canvas.style.display = 'block';

    // Update buttons
    this.startWebcamBtn.style.display = 'inline-block';
    this.stopWebcamBtn.style.display = 'none';

    this.setStatus('Webcam stopped');
  }

  captureFrame() {
    // Check which source is selected
    const source = document.querySelector(`input[name="${this.pid}_source"]:checked`).value;

    if (source === 'webcam') {
      this.captureFromWebcam();
    } else if (source === 'url') {
      this.captureFromUrl();
    } else {
      this.setStatus('Select webcam or URL source to capture');
    }
  }

  captureFromWebcam() {
    if (!this.webcamActive || !this.video.srcObject) {
      this.setStatus('Error: Webcam not started');
      return;
    }

    // Draw video frame to temporary canvas
    this.tempCanvas.width = this.video.videoWidth;
    this.tempCanvas.height = this.video.videoHeight;
    const ctx = this.tempCanvas.getContext('2d');
    ctx.drawImage(this.video, 0, 0);

    // Get image data
    this.currentImageData = this.tempCanvas.toDataURL('image/jpeg', 0.9);

    // Show captured frame in image element
    this.showImage();
    this.canvas.src = this.currentImageData;

    this.setStatus('Frame captured from webcam');
  }

  captureFromUrl() {
    const url = this.cameraUrl.value;
    if (!url) {
      this.setStatus('Error: No camera URL specified');
      return;
    }

    this.setStatus('Capturing from URL...');

    const tempImg = new Image();
    tempImg.crossOrigin = 'anonymous';
    tempImg.onload = () => {
      this.tempCanvas.width = tempImg.width;
      this.tempCanvas.height = tempImg.height;
      const ctx = this.tempCanvas.getContext('2d');
      ctx.drawImage(tempImg, 0, 0);
      this.currentImageData = this.tempCanvas.toDataURL('image/jpeg');
      this.showImage();
      this.canvas.src = this.currentImageData;
      this.setStatus('Frame captured from URL');
    };
    tempImg.onerror = () => {
      this.setStatus('Error: Could not capture from URL (CORS or network issue)');
    };
    tempImg.src = url + '?' + Date.now(); // Cache bust
  }

  showImage() {
    // Ensure image element is visible
    this.video.style.display = 'none';
    this.canvas.style.display = 'block';
  }

  processCurrentImage() {
    if (!this.currentImageData) {
      this.setStatus('Error: No image loaded - Upload, capture from webcam, or capture from URL first');
      return;
    }

    this.setProcessing(true);
    this.sendCommand({
      cmd: 'process_image',
      image_data: this.currentImageData
    });
  }

  setProcessing(processing) {
    // This currently does not work since pyscript is blocking the main thread

    this.isProcessing = processing;

    // Overlay
    this.processingOverlay.classList.toggle('visible', processing);

    // Button state
    this.processBtn.disabled = processing;
    this.processBtn.classList.toggle('processing', processing);
    this.processBtn.textContent = processing ? 'Processing...' : 'Process';

    // Status animation
    this.status.classList.toggle('processing', processing);
    if (processing) {
      this.setStatus('Processing image...');
    }
  }

  updateContourSettings() {
    const settings = {
      canny_low: parseInt(gid(`${this.pid}_canny_low`).value) || 50,
      canny_high: parseInt(gid(`${this.pid}_canny_high`).value) || 150,
      min_area: parseInt(gid(`${this.pid}_min_area`).value) || 100,
      max_area: parseInt(gid(`${this.pid}_max_area`).value) || 50000
    };
    this.sendCommand({ cmd: 'update_contour_settings', settings: settings });
  }

  updateColorSettings() {
    const settings = {
      h_low: parseInt(gid(`${this.pid}_h_low`).value) || 0,
      h_high: parseInt(gid(`${this.pid}_h_high`).value) || 180,
      s_low: parseInt(gid(`${this.pid}_s_low`).value) || 50,
      s_high: parseInt(gid(`${this.pid}_s_high`).value) || 255,
      v_low: parseInt(gid(`${this.pid}_v_low`).value) || 50,
      v_high: parseInt(gid(`${this.pid}_v_high`).value) || 255
    };
    this.sendCommand({ cmd: 'update_color_settings', settings: settings });
  }

  updateShapeSettings() {
    const settings = {
      min_radius: parseInt(gid(`${this.pid}_min_radius`).value) || 10,
      max_radius: parseInt(gid(`${this.pid}_max_radius`).value) || 100,
      min_dist: parseInt(gid(`${this.pid}_min_dist`).value) || 30,
      param2: parseInt(gid(`${this.pid}_param2`).value) || 30
    };
    this.sendCommand({ cmd: 'update_shape_settings', settings: settings });
  }

  sendCommand(data) {
    hermes.send_json(this.pid, data);
  }

  call(data) {
    try {
      if (typeof data === 'string') {
        data = JSON.parse(data);
      }

      if (data.cmd === 'detection_results') {
        this.handleDetectionResults(data.results);
      } else if (data.cmd === 'settings') {
        this.handleSettingsUpdate(data);
      }
    } catch (e) {
      console.error('OpenCvTester call error:', e);
      this.setProcessing(false);
      this.setStatus('Error processing response');
    }
  }

  handleDetectionResults(results) {
    // Stop processing state
    this.setProcessing(false);

    if (results.error) {
      this.setStatus(`Error: ${results.error}`);
      return;
    }

    // Update canvas with annotated image
    if (results.annotated_image) {
      this.showImage();
      this.canvas.src = results.annotated_image;
    }

    // Store and display results
    this.lastResults = results.detections || [];
    this.displayResults(this.lastResults, results.mode);

    const count = this.lastResults.length;
    this.setStatus(`Found ${count} detection${count !== 1 ? 's' : ''} (${results.mode})`);
  }

  handleSettingsUpdate(data) {
    this.currentMode = data.mode;
  }

  displayResults(detections, mode) {
    if (!detections || detections.length === 0) {
      this.resultsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666;">No detections</td></tr>';
      return;
    }

    let html = '';
    detections.forEach(det => {
      const details = this.getDetailsString(det);
      html += `<tr>
        <td>${det.id}</td>
        <td>${det.type}</td>
        <td>${det.center ? det.center.x : '-'}</td>
        <td>${det.center ? det.center.y : '-'}</td>
        <td>${details}</td>
      </tr>`;
    });

    this.resultsBody.innerHTML = html;
  }

  getDetailsString(det) {
    switch (det.type) {
      case 'qrcode':
        return det.data ? `"${det.data.substring(0, 30)}${det.data.length > 30 ? '...' : ''}"` : '(no data)';
      case 'contour':
        return `Area: ${det.area}, AR: ${det.aspect_ratio}`;
      case 'color':
        return `Area: ${det.area}`;
      case 'circle':
        return `Radius: ${det.radius}`;
      case 'rectangle':
        return `${det.bbox.w}x${det.bbox.h}, AR: ${det.aspect_ratio}`;
      default:
        return JSON.stringify(det).substring(0, 50);
    }
  }

  exportResults() {
    if (this.lastResults.length === 0) {
      this.setStatus('No results to export');
      return;
    }

    const json = JSON.stringify(this.lastResults, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `opencv_results_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    this.setStatus('Results exported to JSON');
  }

  sendToOutput() {
    if (this.lastResults.length === 0) {
      this.setStatus('No results to send');
      return;
    }

    this.sendCommand({
      cmd: 'send_output',
      results: this.lastResults
    });

    this.setStatus('Results sent to output');
  }

  clearResults() {
    this.lastResults = [];
    this.resultsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666;">No detections yet</td></tr>';
    this.setStatus('Results cleared');
  }

  setStatus(message) {
    this.status.textContent = message;
  }
}
