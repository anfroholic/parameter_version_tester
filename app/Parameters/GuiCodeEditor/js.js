class GuiCodeEditor extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    this.editor = CodeMirror.fromTextArea(gid(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula" // Set theme (you can change it)
    });
    
    this.save_button = gid(`${param.pid}_save_button`);
    this.submit_button = gid(`${param.pid}_submit_button`);

    this.save_button.addEventListener('click', function () { self.save_file() });
    this.submit_button.addEventListener('click', function () { self.send() });

    // Set initial and maximum height
    let initialHeight = 50; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    gid(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);
    
    // Get the resize bar element
    this.resizeBar = gid(`${param.pid}_resize-bar`);
    // Function to handle mouse down on the resize bar
    this.resizeBar.addEventListener('mousedown', function (event) {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        gid(`${param.pid}_editor`).style.height = newHeight + 'px';
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
    gid(`${param.pid}_file_input`).addEventListener('change', function (event) {
      const fileInput = event.target;

      if (fileInput.files.length > 0) {
        const selectedFile = fileInput.files[0];
        // Read the file content
        const reader = new FileReader();
        reader.onload = function (e) {
          const fileContent = e.target.result;
          self.editor.setValue(fileContent);
        };
        reader.readAsText(selectedFile);
      }
    });
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    this.editor.setValue(data);
  }

  send() {
    const text = this.editor.getValue();
    hermes.send(this.pid, text);
  }

  save_file() {
    // Prompt for a filename
    const fileName = prompt('Enter a filename: ', "filename.evzr");

    if (fileName) {
      const fileContent = this.editor.getValue();

      const blob = new Blob([fileContent], { type: 'text/plain' });
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = blobUrl;

      a.download = fileName;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(blobUrl);
    }
  }
}