class GuiCheckbox extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.checkbox = document.getElementById(`${param.pid}_checkbox`);
    this.checkbox.onclick = () => {hermes.send(this.pid,this.checkbox.checked)};
    
    if (param.initial_value) {
      this.checkbox.checked = true;
    }
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    let bool;
    // console.log(val)
    if (val == 'True') { bool = true; }
    else { bool = false; }
    this.checkbox.checked = bool;
  }
}
