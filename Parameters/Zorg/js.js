class Zorg extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.term = gid(`${this.pid}_term`);

    // set up tabs
    this.tab_buttons = {
      msg_sender: gid(`${this.pid}_msg_sender_tab_button`),
      push_subs: gid(`${this.pid}_push_subs_tab_button`),
      single_sub: gid(`${this.pid}_single_sub_tab_button`),
      devices: gid(`${this.pid}_devices_tab_button`),
      esp32: gid(`${this.pid}_esp32_tab_button`),
    }
    for (const [name, button] of Object.entries(this.tab_buttons)) {
      button.onclick = (event) => { this.change_tab(event, name) };
    }

    this.tabs = {
      msg_sender: gid(`${this.pid}_msg_sender`),
      push_subs: gid(`${this.pid}_push_subs`),
      single_sub: gid(`${this.pid}_single_sub`),
      devices: gid(`${this.pid}_devices`),
      esp32: gid(`${this.pid}_esp32`),
    }

    for (const button of Object.values(gid(`${this.pid}_esp32`).children)) {
      button.onclick = (event) => { this._call(button.innerHTML) }
    }
    
  }

  call(data) {
    const self = this;
    // console.log(data)
    const order = JSON.parse(data);
    const cmd = order.cmd;

    function post(order) {
      const msg = order.state.replaceAll('\n', '<br>')
      self.term.innerHTML = self.term.innerHTML + '<br>' + msg;
    }

    if (cmd == 'term') {post(order)}
    else if (cmd == 'devices') {this.create_device_table(order)}
    else if (cmd == 'cluster') {this.create_cluster_list(order)}
    else if (cmd == 'files') {this.create_file_table(order)}
    else if (cmd == 'myblobs') {this.populateblob(order)}
  }

  populateblob(order) {
    const blobmap = order.state;
    for (const [pid, blob] of Object.entries(blobmap)) {
      gid(`${this.pid}_blob_${pid}`).value = blob;
    }
  }

  _call(cmd, other) {
    console.log(cmd, other);
    let type;
    let msg;
    let load;
    if (cmd == 'send') {
      if (gid(`${this.pid}_radio_string`).checked) {
        type = 'string';
        msg = gid(`${this.pid}_string`).value;
      }
      else {
        type = 'bytes';
        msg = [
          gid(`${this.pid}_bytes_0`).value,
          gid(`${this.pid}_bytes_1`).value,
          gid(`${this.pid}_bytes_2`).value,
          gid(`${this.pid}_bytes_3`).value,
          gid(`${this.pid}_bytes_4`).value,
          gid(`${this.pid}_bytes_5`).value,
          gid(`${this.pid}_bytes_6`).value,
          gid(`${this.pid}_bytes_7`).value,
        ]
      }
      load = {
        cmd: cmd,
        adr: gid(`${this.pid}_adr`).value,
        pid: gid(`${this.pid}_pid`).value,
        type: type,
        msg: msg,
        write: gid(`${this.pid}_read`).checked
      }
    }
    else if (cmd == 'create_sub') {
      load = {
        cmd: cmd,
        sender: {
          adr: gid(`${this.pid}_sub_s_adr`).value,
          pid: gid(`${this.pid}_sub_s_pid`).value,
        },
        recvr: {
          adr: gid(`${this.pid}_sub_adr`).value,
          pid: gid(`${this.pid}_sub_pid`).value,
        },
        struct: gid(`${this.pid}_struct`).value,
      }
    }
    else if (cmd == 'ide_subs') {
      load = {
        cmd: cmd,
        subs: gid(`${this.pid}_ide_subs`).value,
      }
    }
    else if (cmd == 'save_subs') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'clear_subs') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'reset_self') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'ping') {
      load = { cmd: cmd }
      gid(`${this.pid}_device_table`).innerHTML = "pinging<br>please wait";
    }
    else if (cmd == 'show_files') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'reset') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'lightshow') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'send_file') {
      load = other
    }
    else if (cmd == 'cluster') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'get_file') {
      load = {
        cmd: cmd,
        filename: other
      }
    }
    else if (cmd == 'test') {
      load = {cmd: cmd}
    }
    console.log(load);
    hermes.send_json(this.pid, load)
  }

  post(line) {
    console.log(line);
    this.term.innerHTML = this.term.innerHTML + '<br>' + line;
  }

  create_cluster_list(order) {
    const cluster = gid(`${this.pid}_cluster`);
    let html = "Cluster Info<br>";
    for (const clust of order.state) {
      html = html + `${clust[0]}: ${clust[1]}<br>`
    }
    html = html + "---------<br><br><br>";
    console.log(html)
    cluster.innerHTML = html;
  }

  create_device_table(order) {
    // example order {'cmd': 'devices', 'state': adr: [machine.id, device_name]}
    let devices = order.state
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');

    // create headings
    const row = document.createElement('tr');
    const adr = document.createElement('td');
    adr.textContent = "adr";

    const dev_id = document.createElement('td');
    dev_id.textContent = "device id";

    const name = document.createElement('td');
    name.textContent = "name";

    const blob = document.createElement('td');
    blob.textContent = "blob";

    row.appendChild(adr);
    row.appendChild(dev_id);
    row.appendChild(name);
    row.appendChild(blob);
    tbody.appendChild(row);

    for (const [adr, device] of Object.entries(devices)) {
      const row = document.createElement('tr');
      const adrCell = document.createElement('td');
      adrCell.textContent = adr;
      row.appendChild(adrCell);

      const device_id = document.createElement('td');
      device_id.textContent = device[0];
      row.appendChild(device_id);

      const name = document.createElement('td');
      if (device[1] == 'unknown device') {
        name.innerHTML = '<button>feature coming soon</button>';
      }
      else {
        name.innerHTML = "<button>mate</button>";
      }
      name.id = `${device[0]}_name`
      row.appendChild(name);
      
      const blob = document.createElement('td');
      blob.innerHTML = '<button>getblob</button>'
      blob.id = `${this.pid}_blob_${adr}`
      row.appendChild(blob)
      // Append the row to the table body
      tbody.appendChild(row);
    }
    // Append the table body to the table
    table.appendChild(tbody);

    // Get the table_div element
    const tableDiv = document.getElementById(`${this.pid}_device_table`);
    tableDiv.innerHTML = '';
    // Append the table to the table_div element
    tableDiv.appendChild(table);
  }

  create_file_table(order) {
    const file_div = gid(`${this.pid}_files`)
    file_div.innerHTML = ""
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');

    // create headings
    const row = document.createElement('tr');
    const _filename = document.createElement('td');
    _filename.textContent = "filename";

    const actions = document.createElement('td');
    actions.textContent = "actions";

    row.appendChild(_filename);
    row.appendChild(actions);
    tbody.appendChild(row);

    for (const filename of order.state.sort()) {
      const row = document.createElement('tr');
      const name = document.createElement('td');
      name.textContent = filename;
      row.appendChild(name);
      const act = document.createElement('td');
      if (filename.charCodeAt(0) >= 65 && filename.charCodeAt(0) <= 90) {
        act.innerHTML = `
        <button onclick="hermes.p[${this.pid}].craft_file_message(this, '${filename}')">send to</button>
        <input style="width: 100px;" type="number">
        <button class="xsm_button blue" onclick="hermes.p[${this.pid}]._call('get_file', '${filename}')">update</button>
        `
      }
      else {
        act.innerHTML = `
      <button onclick="hermes.p[${this.pid}].craft_file_message(this, '${filename}')">send to</button>
      <input style="width: 100px;" type="number">
      `
      }

      row.appendChild(act);
      tbody.appendChild(row);
    }
    // Append the table body to the table
    table.appendChild(tbody);
    file_div.appendChild(table);
  }
  craft_file_message(button, filename) {
    let adr = parseInt(button.nextElementSibling.value)
    if (isNaN(adr)) {
      this.post('enter valid address')
      return
    }
    let load = {
      cmd: 'send_file',
      adr: adr,
      filename: filename,
    }
    hermes.send_json(this.pid, load)
  }

  change_tab(event, tab_name) {
    // handle tabs
    let buttons = document.getElementById(`${this.pid}_tabs`).children;
    for (var i = 0; i < buttons.length; i++) {
      let button = buttons[i];
      if (button.classList.contains('green')) {
        console.log(button)
        button.classList.remove('green');
        button.classList.add('grey');
      }
    }
    event.target.classList.remove('grey');
    event.target.classList.add('green');

    for (const [name, tab] of Object.entries(this.tabs)) {
      if (name == tab_name) {
        tab.style.display = "block";
      }
      else {
        tab.style.display = "none";
      }
    }
  }

  getHTML(param, self) {
    return `{{ html }}`;
  }
}