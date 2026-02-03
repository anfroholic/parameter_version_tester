
class GRBLScara extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;

    this.tabs = {
      machine: { button: gid(`${param.pid}_machine_button`), tab: gid(`${param.pid}_machine_tab`) },
      work_offsets: { button: gid(`${param.pid}_work_offsets_button`), tab: gid(`${param.pid}_work_offsets_tab`) },
      tool_offsets: { button: gid(`${param.pid}_tool_offsets_button`), tab: gid(`${param.pid}_tool_offsets_tab`) },
      term: { button: gid(`${param.pid}_term_button`), tab: gid(`${param.pid}_term_tab`) },
      files: { button: gid(`${param.pid}_files_button`), tab: gid(`${param.pid}_files_tab`) },
    }

    for (const [key, value] of Object.entries(this.tabs)) {
      value.button.addEventListener('click', function () { self.set_tabs(key) });
    }

    this.work_offsets = param.work_offsets;
    this.work_offset = param.work_offset;

    this.tool_offsets = param.tool_offsets;
    this.tool_offset = param.tool_offset;

    this.theta_len = param.theta_len;
    this.theta_2 = this.theta_len ** 2;

    this.phi_len = param.tool_offsets[this.tool_offset]['l']
    this.phi_2 = this.phi_len ** 2;
    this.axes = param.axes;
    this.axes_map = param.axes_map;

    this.create_machine_table();
    this.create_grbl_coms_table();
    this.create_work_offsets_table();
    this.create_tool_offset_table();
    Terminal.init(param, true);  // initialize the terminal
  }

  create_tool_offset_table() {
    const table = document.getElementById(`${this.pid}_tool_offsets_table`);
    table.innerHTML = '';
    table.style.width = '100%';

    // Create header row
    const headerRow = document.createElement('tr');
    const headers = ['Offset:', 'Name', 'p', 'l', 'z', ''];
    headers.forEach(text => {
      const th = document.createElement('td');
      th.textContent = text;
      headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Create offset rows
    Object.entries(this.tool_offsets).forEach(([name, values], index) => {
      const row = document.createElement('tr');

      // Offset radio button
      const radioTd = document.createElement('td');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.id = `${this.pid}_radio_tool_offset_${index}`;
      radio.name = `${this.pid}_radio_tool_offset`;
      if (this.tool_offset === name) {
        radio.checked = true;
      }

      radio.onchange = () => this.send('change_tool_offset', name);
      radioTd.appendChild(radio);
      radioTd.appendChild(document.createTextNode(index));
      row.appendChild(radioTd);

      // Offset name
      const nameTd = document.createElement('td');
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = name;
      nameTd.appendChild(nameInput);
      row.appendChild(nameTd);

      // X, Y, Z, A input fields
      ['p', 'l', 'z'].forEach(axis => {
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.minWidth = '55px';
        input.value = values[axis] || 0;
        td.appendChild(input);
        row.appendChild(td);
      });

      // Set button
      const buttonTd = document.createElement('td');
      const button = document.createElement('button');
      button.className = 'xsm_button blue';
      button.textContent = 'set';
      button.onclick = () => this.send('set_tool_offset', name);
      buttonTd.appendChild(button);
      row.appendChild(buttonTd);

      table.appendChild(row);
    });

    this.phi_len = this.tool_offsets[this.tool_offset]['l']
    console.log(this.phi_len);
    this.phi_2 = this.phi_len ** 2;
  }

  create_machine_table() {
    // main tab for machine movement
    const self = this;

    // add function to move button
    const move_button = gid(`${this.pid}move_submit`);
    move_button.onclick = function () {

      let move = { cmd: 'move' };

      for (const axis of Object.values(self.axes_map)) {
        let pos = gid(`${self.pid}move_${axis}`).value;
        if (pos != "") {
          pos = parseFloat(pos);
        }
        move[axis] = pos;
      }
      console.log(move);
      move['f'] = gid(`${self.pid}move_f`).value;

      hermes.send_json(self.pid, move);
    }

    // create the table
    const machine_table = gid(`${this.pid}_machine_table`);
    console.log(machine_table);
    // First row: Move Machine headers
    const headerRow = document.createElement('tr');
    const headers = [
      { text: 'Move Machine:', colspan: 2 },
      'Position',
      'Offset',
      'MPos',
      'Encoders',
      'Jog',
    ];

    headers.forEach(header => {
      const th = document.createElement('td');
      if (typeof header === 'object') {
        th.textContent = header.text;
        th.colSpan = header.colspan;
      } else {
        th.textContent = header;
      }
      headerRow.appendChild(th);
    });
    machine_table.appendChild(headerRow);


    this.axes.forEach(axis => {
      const _axis = this.axes_map[axis]
      const row = document.createElement('tr');

      // Label cell
      const labelCell = document.createElement('td');
      labelCell.innerHTML = `<strong>${_axis}: </strong>`;
      labelCell.style.width = '5px';
      row.appendChild(labelCell);

      // Input cell
      const inputCell = document.createElement('td');
      const input = document.createElement('input');
      input.type = 'number';
      input.style.width = '100%';
      input.id = `${this.pid}move_${_axis}`;
      inputCell.appendChild(input);
      row.appendChild(inputCell);

      // Position, Offset, Absolute Pos cells
      ['pos', 'offset', 'mpos', 'enc'].forEach(suffix => {
        const cell = document.createElement('td');
        const div = document.createElement('div');
        div.id = `${this.pid}_${_axis}${suffix}`;
        div.textContent = 'None';
        cell.appendChild(div);
        row.appendChild(cell);
      });

      // create jog elements
      const cell = document.createElement('td');
      const div = document.createElement('div');
      div.id = `${this.pid}_${_axis}${'jog'}`;

      const jog_minus = document.createElement('button');
      jog_minus.textContent = '←';
      jog_minus.onclick = function () { 
        let val = parseFloat(gid(`${self.pid}_${_axis}pos`).innerHTML) - .1;
        let order = { cmd: 'move', 
          feed: 500,
        }
        order[_axis] = val
        hermes.send_json(self.pid, order);
      };


      const jog_plus = document.createElement('button');
      jog_plus.textContent = '→';
      jog_plus.onclick = function () { 
        let val = parseFloat(gid(`${self.pid}_${_axis}pos`).innerHTML) + .1;
        let order = { cmd: 'move', 
          feed: 500,
        }
        order[_axis] = val
        hermes.send_json(self.pid, order);
      };
      div.appendChild(jog_minus);
      div.appendChild(jog_plus);
      cell.appendChild(div);
      row.appendChild(cell);
      // /create jog elements

      machine_table.appendChild(row);
    });

    // Feed row
    const feedRow = document.createElement('tr');

    // Feed label and input
    const feedLabelCell = document.createElement('td');
    feedLabelCell.innerHTML = '<strong>feed: </strong>';
    feedRow.appendChild(feedLabelCell);

    const feedInputCell = document.createElement('td');
    const feedInput = document.createElement('input');
    feedInput.type = 'number';
    feedInput.style.width = '100%';
    feedInput.id = `${this.pid}move_f`;
    feedInput.value = '500';
    feedInputCell.appendChild(feedInput);
    feedRow.appendChild(feedInputCell);

    // Status and Offset Name cells
    const statusCell = document.createElement('td');
    const statusDiv = document.createElement('div');
    statusDiv.id = `${this.pid}_state`;
    statusDiv.textContent = 'Status: None';
    statusCell.appendChild(statusDiv);
    feedRow.appendChild(statusCell);

    const offsetNameCell = document.createElement('td');
    const offsetNameDiv = document.createElement('div');
    offsetNameDiv.id = `${this.pid}_offset_name`;
    // offsetNameDiv.textContent = 'Name: None';
    offsetNameCell.appendChild(offsetNameDiv);
    feedRow.appendChild(offsetNameCell);

    // Blinker cell
    const blinkerCell = document.createElement('td');
    blinkerCell.colSpan = 2;
    const blinkerDiv = document.createElement('div');
    blinkerDiv.id = `${this.pid}_blinker`;
    blinkerDiv.style.cssText = 'height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;';
    blinkerCell.appendChild(blinkerDiv);
    feedRow.appendChild(blinkerCell);

    machine_table.appendChild(feedRow);

  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    const self = this;
    const msg = JSON.parse(data);
    if (msg.cmd != 'status') {
      console.log(msg);
    }
    if (msg.cmd == 'post') {
      Terminal.write(gid(`${self.pid}_terminal`), msg.data);
      let command = msg.data;
      if (command[0] === '$') {
        // we have a command frame
        if (command.includes('=')) {
          const pieces = command.split('=');
          let table = gid(`${self.pid}_grbl_coms_table`);
          for (const row of table.rows) {
            if (row.cells[0].innerHTML.includes(pieces[0])) {
              row.cells[1].querySelector('input').value = pieces[1]
            }
          }
        }
      }
    }
    else if (msg.cmd == 'status') {
      this._status(msg);
    }
    else if (msg.cmd == 'set_work_offset') {
      console.log('set_work_offset', msg.data);
      this.work_offsets = msg.data;
      this.create_work_offsets_table();
    }
    else if (msg.cmd == 'change_work_offset') {
      this.work_offset = msg.data;
      this.create_work_offsets_table();
    }
    else if (msg.cmd == 'change_tool_offset') {
      this.tool_offset = msg.data;
      this.create_tool_offset_table();
    }
    else if (msg.cmd == 'set_tool_offset') {
      console.log('set_tool_offset', msg.data);
      this.tool_offsets = msg.data;
      this.create_tool_offset_table();
    }
    else if (msg.cmd == 'populate_files') {
      let table = gid(`${this.pid}_files_table`);
      console.log(table);
      table.innerHTML = '';
      for (let i = 0; i < msg.data.length; i++) {
        let row = table.insertRow();
        let cell = row.insertCell();
        cell.innerHTML = msg.data[i];
        let cell2 = row.insertCell();
        let button = document.createElement('button');
        button.innerHTML = 'load';
        button.onclick = function () {
          hermes.send_json(self.pid, { cmd: 'run', script: msg.data[i] });
        }
        cell2.appendChild(button);
      }
    }
    else {
      console.log('unknown message', msg)
    }
  }

  _status(msg) {

    if (this.axes.includes('x')) {
      gid(`${this.pid}_tpos`).innerHTML = msg.x;
      gid(`${this.pid}_tmpos`).innerHTML = msg.x;
    }
    if (this.axes.includes('y')) {
      const p = msg.y - this.tool_offsets[this.tool_offset]['p'];
      gid(`${this.pid}_ppos`).innerHTML = p.toFixed(3);
      gid(`${this.pid}_pmpos`).innerHTML = msg.y;
    }
    if (this.axes.includes('z')) {
      const z = msg.z - this.work_offsets[this.work_offset]['z'] - - this.tool_offsets[this.tool_offset]['z'];
      gid(`${this.pid}_zmpos`).innerHTML = msg.z;
      gid(`${this.pid}_zpos`).innerHTML = z.toFixed(3);
    }
    if (this.axes.includes('a')) {
      gid(`${this.pid}_apos`).innerHTML = msg.a;
      gid(`${this.pid}_ampos`).innerHTML = msg.a;
    }
    if (this.axes.includes('b')) {
      gid(`${this.pid}_bpos`).innerHTML = msg.b;
      gid(`${this.pid}_bmpos`).innerHTML = msg.b;
    }
    if (this.axes.includes('c')) {
      gid(`${this.pid}_cpos`).innerHTML = msg.c;
      gid(`${this.pid}_cmpos`).innerHTML = msg.c;
    }
    
    // TODO: create error state if no encoders
    if (msg.theta_enc == null) {msg.theta_enc = 0;}
    if (msg.phi_enc == null) {msg.phi_enc = 0;}
    gid(`${this.pid}_tenc`).innerHTML = msg.theta_enc.toFixed(3);
    gid(`${this.pid}_penc`).innerHTML = msg.phi_enc.toFixed(3);
    
    gid(`${this.pid}_state`).innerHTML = `Status: ${msg.state}`;
    if (gid(`${this.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
      gid(`${this.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
    }
    else { gid(`${this.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)"; }
    if (gid(`${this.pid}_show_status`).checked == true) {
      Terminal.write(gid(`${this.pid}_terminal`), JSON.stringify(msg));
    }

    gid(`${this.pid}_work_offset`).innerHTML = this.work_offset;
    gid(`${this.pid}_tool_offset`).innerHTML = this.tool_offset;

    // const pos = GRBLScara.fk(param.pid, msg.x, msg.y);
    let pos = this.translatexy(this.fk(msg.theta_enc, msg.phi_enc));
    gid(`${this.pid}_cart_x`).innerHTML = pos[0].toFixed(3);
    gid(`${this.pid}_cart_y`).innerHTML = pos[1].toFixed(3);
    gid(`${this.pid}_cart_z`).innerHTML = gid(`${this.pid}_zpos`).innerHTML;

    let grbl_pos = this.translatexy(this.fk(msg.x, msg.y - this.tool_offsets[this.tool_offset]['p']));
    let pos_dict = {x: grbl_pos[0].toFixed(3), y:grbl_pos[1].toFixed(3), z:gid(`${this.pid}_zpos`).innerHTML}
    gid(`${this.pid}_cart_x_grbl`).innerHTML = grbl_pos[0].toFixed(3);
    gid(`${this.pid}_cart_y_grbl`).innerHTML = grbl_pos[1].toFixed(3);
    gid(`${this.pid}_cart_z_grbl`).innerHTML = gid(`${this.pid}_zpos`).innerHTML;
    let a = (msg.a - msg.x - msg.y).toFixed(3)

    gid(`${this.pid}_cart_dict`).innerHTML = `{"x": ${pos_dict.x}, "y": ${pos_dict.y}, "z": ${pos_dict.z}, "a": ${a}}`
  }

  send(cmd, payload) {
    let msg = {};
    console.log(cmd, payload);
    if (cmd == 'change_work_offset' || cmd == 'change_tool_offset') {
      msg = { cmd: cmd, data: payload }
    }

    else if (cmd == 'set_work_offset') {
      const table = document.getElementById(`${this.pid}_work_offsets_table`);
      let row;
      
      for (let i = 1; i < table.rows.length; i++) {
        if (table.rows[i].cells[1].querySelector('input').value == payload) {
          row = table.rows[i];
        }
      }
      msg.cmd = cmd;
      msg.name = row.cells[1].querySelector('input').value;

      for (let i = 0; i < this.axes.length; i++) {
        msg[this.axes[i]] = parseFloat(row.cells[i + 2].querySelector('input').value);
      }
      console.log(msg);
    }

    else if (cmd == 'set_tool_offset') {
      const table = document.getElementById(`${this.pid}_tool_offsets_table`);
      let row;
      for (let i = 1; i < table.rows.length; i++) {
        // console.log(table.rows[i].cells[1].querySelector('input').value);
        if (table.rows[i].cells[1].querySelector('input').value == payload) {
          row = table.rows[i];
        }
      }
      msg.cmd = cmd;
      msg.name = row.cells[1].querySelector('input').value;
      msg.p = parseFloat(row.cells[2].querySelector('input').value);
      msg.l = parseFloat(row.cells[3].querySelector('input').value);
      msg.z = parseFloat(row.cells[4].querySelector('input').value);

      console.log(msg);
    }
    else {
      console.log('error')
      return
    }
    hermes.send_json(this.pid, msg)
  }

  create_work_offsets_table() {
    const table = document.getElementById(`${this.pid}_work_offsets_table`);
    table.innerHTML = '';
    table.style.width = '100%';

    // Create header row
    const headerRow = document.createElement('tr');
    const headers = ['Offset:', 'Name', 'X', 'Y', 'Z', 'A', ''];
    headers.forEach(text => {
      const th = document.createElement('td');
      th.textContent = text;
      headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Create offset rows
    Object.entries(this.work_offsets).forEach(([name, values], index) => {
      const row = document.createElement('tr');

      // Offset radio button
      const radioTd = document.createElement('td');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.id = `${this.pid}_radio_work_offset_${index}`;
      radio.name = `${this.pid}_radio_work_offset`;
      if (this.work_offset === name) {
        radio.checked = true;
      }

      radio.onchange = () => this.send('change_work_offset', name);
      radioTd.appendChild(radio);
      radioTd.appendChild(document.createTextNode(index));
      row.appendChild(radioTd);

      // Offset name
      const nameTd = document.createElement('td');
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = name;
      nameTd.appendChild(nameInput);
      row.appendChild(nameTd);

      // X, Y, Z, A input fields
      ['x', 'y', 'z', 'a'].forEach(axis => {
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.minWidth = '55px';
        input.value = values[axis] || 0;
        td.appendChild(input);
        row.appendChild(td);
      });

      // Set button
      const buttonTd = document.createElement('td');
      const button = document.createElement('button');
      button.className = 'xsm_button blue';
      button.textContent = 'set';
      button.onclick = () => this.send('set_work_offset', name);
      buttonTd.appendChild(button);
      row.appendChild(buttonTd);

      table.appendChild(row);
    });
  }

  set_tabs(tab) {
    for (const [key, value] of Object.entries(this.tabs)) {
      const button = value.button;
      if (key == tab) {
        value.tab.style.display = "block";
        if (button.classList.contains('grey')) {
          // console.log(button)
          button.classList.remove('grey');
          button.classList.add('green');
        }
      }
      else {
        value.tab.style.display = "none";
        if (button.classList.contains('green')) {
          console.log(button)
          button.classList.remove('green');
          button.classList.add('grey');
        }
      }
    }
  }

  fk(theta_deg, phi_deg) {
    // forward kinematics
    const theta = theta_deg * Math.PI / 180;
    const phi = phi_deg * Math.PI / 180;
    const c2 = (this.theta_2 + this.phi_2) - (2 * this.theta_len * this.phi_len * Math.cos(Math.PI - phi));
    const c = Math.sqrt(c2);
    const B = Math.acos((c2 + this.theta_2 - this.phi_2) / (2 * c * this.theta_len));
    const new_theta = theta + B;
    // we implicitly do the coordinate tranform here
    let y = -Math.cos(new_theta) * c;
    let x = Math.sin(new_theta) * c;
    return [x, y];
  }

  translatexy(pos) {
    const work_offset = this.work_offsets[this.work_offset]
    // Rotate
    let hyp = Math.hypot(pos[0], pos[1]);
    let hypAngle = Math.atan2(pos[1], pos[0]);
    let newHypAngle = hypAngle + work_offset.a;

    pos[0] = Math.cos(newHypAngle) * hyp;
    pos[1] = Math.sin(newHypAngle) * hyp;

    // Translate
    pos[0] -= work_offset['x']
    pos[1] -= work_offset['y']

    return pos;
  }

  create_grbl_coms_table() {
    const self = this;

    this.coms_list_offsets = gid(`${this.pid}_list_offsets`);
    this.coms_reset = gid(`${this.pid}_reset`);
    this.coms_list_errors = gid(`${this.pid}_list_errors`);
    this.coms_list_modes = gid(`${this.pid}_list_modes`);
    this.coms_list_files = gid(`${this.pid}_list_files`);

    this.coms_list_offsets.onclick = () => hermes.send_json(this.pid, {cmd: 'machine', action: 'get', command: "$GCode/Offsets"})
    this.coms_reset.onclick = () => hermes.send_json(this.pid, {cmd: 'machine', action: 'get', command: "$Bye"})
    this.coms_list_errors.onclick = () => hermes.send_json(this.pid, {cmd: 'machine', action: 'get', command: "$Errors/List"})
    this.coms_list_modes.onclick = () => hermes.send_json(this.pid, {cmd: 'machine', action: 'get', command: "$GCode/Modes"})
    this.coms_list_files.onclick = () => hermes.send_json(this.pid, {cmd: 'machine', action: 'get', command: "$LocalFS/List"})

    const coms_table = gid(`${this.pid}_grbl_coms_table`);
    const axes = ['x', 'y', 'z', 'a', 'b', 'c'];
    const properties = [
      'steps_per_mm',
      'max_rate_mm_per_min',
      'acceleration_mm_per_sec2',
      'max_travel_mm'
    ];

    axes.forEach(axis => {
      properties.forEach(property => {
        const row = document.createElement('tr');

        // Create and append the first cell (label)
        const labelCell = document.createElement('td');
        labelCell.textContent = `$/axes/${axis}/${property}`;
        row.appendChild(labelCell);

        // Create and append the second cell (input)
        const inputCell = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        inputCell.appendChild(input);
        row.appendChild(inputCell);

        // Create and append the third cell (buttons)
        const buttonCell = document.createElement('td');
        const setButton = document.createElement('button');
        setButton.textContent = 'set';
        // setButton.onclick = () => self.grbl_coms(self.pid, labelCell.textContent, 'set');
        setButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'set');

        const getButton = document.createElement('button');
        getButton.textContent = 'get';
        getButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'get');

        buttonCell.appendChild(setButton);
        buttonCell.appendChild(getButton);
        row.appendChild(buttonCell);

        // Append the row to the table
        coms_table.appendChild(row);
      });
    });
  }

  grbl_coms(command, input_cell, action) {
    // this is stuff that should be sent directly to the grbl machine itself
    let data = {
      cmd: 'machine',
      action: action,
      command: command,
    }
    if (action == 'set') {
      let value = parseFloat(input_cell.value)
      data.value = value
      console.log(value)
      if (isNaN(value)) {
        Terminal.write(gid(`${this.pid}_terminal`), `invalid data: ${value}`);
        return
      }
    }
    console.log(data)
    hermes.send_json(this.pid, data);
  }
}