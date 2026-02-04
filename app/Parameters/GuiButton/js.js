
class GuiButton extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.button = document.getElementById(`${param.pid}_button`);
    this.button.onclick = () => {hermes.send(this.pid, true)};
  }
  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    console.log(`button ${this.pid} clicked`, val);
  }
}