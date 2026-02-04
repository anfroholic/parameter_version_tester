class GuiFloat extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.input = document.getElementById(`${param.pid}_input`);
    this.input.value = param.initial_value;
    this.input.onchange = () => {this.send(this.pid)};
  }

  send() {
    const val = this.input.value
    hermes.send(this.pid, val)
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    this.input.value = val;
  }
}