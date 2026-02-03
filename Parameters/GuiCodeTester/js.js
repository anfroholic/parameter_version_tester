
class GuiCodeTester extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    // Initialize CodeMirror
    this.editor = CodeMirror.fromTextArea(gid(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula" // Set theme
    });

    gid(`${param.pid}_description`).innerHTML = marked.parse(param.description)

    // Set initial and maximum height
    let initialHeight = 50; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    gid(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);

    this.editor.setValue(param.code);

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
  
    this.terminal = Terminal.init(param, true)
    gid(`${param.pid}_toggler`).click();
  
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'term') {
      Terminal.write(gid(`${this.pid}_terminal`), msg.msg)
    }
  }

  button(button) {
    // console.log(button.innerText);
    const pid = button.dataset.pid
    const msg = `{"cmd": "button", "msg": "${button.innerText}"}`;
    hermes.send(pid, msg);
  }

  make_buttons(param) {
    let buttons_html = ""
    for (const button in param.buttons) {
      const but = `<button data-pid=${param.pid} onclick="hermes.p[${param.pid}].button(this)">${button}</button>`;
      buttons_html = buttons_html + but;
    }
    return buttons_html
  }
  
  send() {
    const text = this.editor.getValue();
    hermes.send(this.pid, text);
  }
}