
class GuiTextbox extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.textbox = document.getElementById(`${param.pid}_textbox`);
    this.textbox.value = param.initial_value;
    this.textbox.oninput = () => {
      hermes.send(this.param.pid, this.textbox.value);
    }
  }

  getHTML(param) {
    return `{{ html }}`;
  }

  call(val) {
    if (this.textbox.value != val) {
      this.textbox.value = val;
    }
  }
}