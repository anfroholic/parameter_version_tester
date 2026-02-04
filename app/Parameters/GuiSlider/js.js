class GuiSlider extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.slider = document.getElementById(`${param.pid}_slider`);
    console.log(this.slider);
    this.slider.value = param.initial_value;
    this.slider.oninput = () => {
      hermes.send(this.param.pid, parseInt(this.slider.value));
    }
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    if (this.slider.value != val) {
      this.slider.value = val;
    }
  }
}