class GuiCmdAggregator extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;

    this.create_event_button = document.getElementById(`${param.pid}_create_event_button`);
    this.verify_button = document.getElementById(`${param.pid}_verify_button`);
    this.copy_button = document.getElementById(`${param.pid}_copy_button`);

    this.create_event_button.addEventListener('click', function () { self.send() });
    this.verify_button.addEventListener('click', function () { self.verify(false) });
    this.copy_button.addEventListener('click', function () { self.copy2clip() });


    this.editor = CodeMirror.fromTextArea(document.getElementById(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula", // Set theme (you can change it)
      autoCloseBrackets: true, // Enable auto close brackets
    });

    // Set initial and maximum height
    let initialHeight = 100; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    document.getElementById(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);

    this.resizeBar = document.getElementById(`${param.pid}_resize-bar`);
    this.resizeBar.addEventListener('mousedown', (event) => {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        document.getElementById(`${param.pid}_editor`).style.height = newHeight + 'px';
        self.editor.setSize(null, newHeight);
      }

      // Function to handle mouse up after dragging
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    this.editor.setValue(val)
  }

  send() {
    let list = this.verify(this.pid, false);
    if (list !== null) {
      hermes.send(this.pid, list)
    }
  }

  verify(json) {
    let raw = this.editor.getValue().split('\n')
    console.log(raw);
    for (const e in raw) {
      try {
        if (raw[e] == "") {
          continue
        }
        JSON.parse(raw[e])
      }
      catch {
        document.getElementById(`${this.pid}_editor_error`).innerHTML = `error on line ${parseInt(e) + 1} - no action was taken`
        return null
      }
    }
    document.getElementById(`${this.pid}_editor_error`).innerHTML = ""
    if (json == true) {
      return `[${raw}]`;
    }
    return this.editor.getValue()
  }

  copy2clip() {
    let clip = this.verify(true)
    if (clip != null) {
      navigator.clipboard.writeText(clip);
    }
  }
}