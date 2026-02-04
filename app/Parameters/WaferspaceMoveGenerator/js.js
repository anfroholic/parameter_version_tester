class WaferspaceMoveGenerator extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.pid = param.pid;
    this.alert_box = gid(`${param.pid}_alert_box`);
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(order) {
    console.log("mover call", order);
    order = JSON.parse(order);
    if (order.cmd === 'alert') {
      this.alert_box.innerHTML = order.alert;
    }
  }
}