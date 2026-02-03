class GuiTeleprompter extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this
    this.textContainer = document.getElementById("scrollingText");
    console.log('stating', param)
    this.textContainer.innerHTML = param.state;

    // Add mirror checkbox
    this.mirrorCheckbox = document.getElementById('teleprompterMirrorCheckbox');

    this.isMirrored = this.mirrorCheckbox.checked;
    this.mirrorCheckbox.addEventListener('change', function() { self.mirror() });

    this.speed = param.speed; // Default scrolling speed (pixels per frame)
    this.isScrolling = false;
    this.animationFrame = null;
    this.popupWindow = null;
    this.pid = 123;
    this.startButton = document.getElementById('teleprompterStartButton')
    this.stopButton = document.getElementById('teleprompterStopButton')
    this.resetButton = document.getElementById('teleprompterResetButton')
    
    this.startButton.addEventListener('click', function () { self.start() });
    this.stopButton.addEventListener('click', function () { self.stop() });
    this.resetButton.addEventListener('click', function () { self.reset() });

  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'set_state') {
      let state = msg.state;
      state = state.replaceAll('\n', '<br>'); // Convert newlines to <br> for HTML
      console.log(state);
      this.textContainer.innerHTML = state;
      this.reset(); // Reset the teleprompter to the new state
    }
    else if (msg.cmd == 'set_speed') {
      console.log(msg.state);
      this.setSpeed(msg.state);
    }
    else if (msg.cmd == 'start') {
      this.start();
    }
    else if (msg.cmd == 'stop') {
      this.stop();
    }
    else if (msg.cmd == 'reset') {
      this.reset();
    }
    else {
      console.log('unknown command GuiTeleprompter', msg)
    }
  }

  setSpeed(speed) {
    this.speed = speed; // Set the scrolling speed
  }

  mirror() {
    this.isMirrored = this.mirrorCheckbox.checked;
    
    if (this.isMirrored) {
      this.textContainer.style.transform = 'scaleX(-1)';
    } else {
      this.textContainer.style.transform = 'scaleX(1)';
    }
  }

  start() {
    if (this.isScrolling) return; // Prevent multiple instances of scrolling

    this.isScrolling = true;
    const step = () => {
      const currentTransform = getComputedStyle(this.textContainer).transform;
      // Extract translateY from the matrix
      let translateY = 0;
      if (currentTransform !== 'none') {
        const matrix = currentTransform.match(/matrix.*\((.+)\)/);
        if (matrix) {
          const values = matrix[1].split(', ');
          translateY = parseFloat(values[5]);
        }
      }
      const newTranslateY = translateY - this.speed;

      // Set transform with mirroring if needed
      if (this.isMirrored) {
        this.textContainer.style.transform = `scaleX(-1) translateY(${newTranslateY}px)`;
      } else {
        this.textContainer.style.transform = `scaleX(1) translateY(${newTranslateY}px)`;
      }

      if (this.isScrolling) {
        this.animationFrame = requestAnimationFrame(step);
      }
    };

    this.animationFrame = requestAnimationFrame(step);
  }

  stop() {
    this.isScrolling = false;
    cancelAnimationFrame(this.animationFrame);
  }

  reset() {
    this.stop();
    // Calculate how much the text is above the visible area
    const containerRect = this.textContainer.getBoundingClientRect();
    const parentRect = this.textContainer.parentElement.getBoundingClientRect();
    let offset = 0;
    if (containerRect.top < parentRect.top) {
      offset = parentRect.top - containerRect.top;
    }
    
    if (this.isMirrored) {
      this.textContainer.style.transform = `scaleX(-1) translateY(${offset}px)`;
    } else {
      this.textContainer.style.transform = `scaleX(1) translateY(${offset}px)`;
    }
    
  }
}
