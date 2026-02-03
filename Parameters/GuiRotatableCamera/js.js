class GuiRotatableCamera extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    this.src = param.src;

    this.show_crosshair_button = gid(`${param.pid}_show_crosshair_button`);
    this.hide_crosshair_button = gid(`${param.pid}_hide_crosshair_button`);
    this.reloadButton = gid(`${param.pid}_reload_button`);
    this.crosshair = gid(`${param.pid}_crosshair`);
    this.deg_label = gid(`${param.pid}_deg`);
    this.slider = gid(`${param.pid}_slider`);
    this.view = gid(`${param.pid}_view`);

    this.slider.addEventListener('input', function () { self.rotate_cam() });
    this.reloadButton.addEventListener('click', function () { self.view.src = self.src; });
    this.show_crosshair_button.addEventListener('click', function () { self.show_crosshair('visible') });
    this.hide_crosshair_button.addEventListener('click', function () { self.show_crosshair('hidden') });
    
    this.rotate_cam();
  }
  call(data) {
    console.log('guicamera not impemented', data)
  }

  getHTML(param) {
    return `{{ html }}`
  }

  rotate_cam() {
    this.deg_label.innerText = parseInt(this.slider.value) - 180;
    this.view.style.transform = `rotate(${this.slider.value}deg)`;
  }

  show_crosshair(show) {
    this.crosshair.style.visibility = show;
  }
}