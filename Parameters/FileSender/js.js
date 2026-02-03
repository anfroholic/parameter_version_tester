class FileSender extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    print('FileSender constructor');
    this.progress_bar = document.getElementById(`${param.pid}_file`);
    this.send_button = document.getElementById(`${param.pid}_send`);
    this.send_button.onclick = () => {this.send()};
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(val) {
    this.progress_bar.value = val;
  }

  send() {
    let remote_adr = gid(`${this.pid}_adr`).value;
    let remote_pid = gid(`${this.pid}_pid`).value;
    let remote_filename = gid(`${this.pid}_remote_filename`).value;
    let local_filename = gid(`${this.pid}_local_filename`).value;
    hermes.send_json(this.pid, {'remote_adr': remote_adr, 'remote_pid': remote_pid, 'remote_filename': remote_filename, 'local_filename': local_filename});
  }
}