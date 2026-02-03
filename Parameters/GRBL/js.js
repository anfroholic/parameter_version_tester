
class GRBL extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;

    this.tabs = {
      machine: {button: gid(`${param.pid}_machine_button`), tab: gid(`${param.pid}_machine_tab`)},
      work_offsets: {button: gid(`${param.pid}_work_offsets_button`), tab: gid(`${param.pid}_work_offsets_tab`)},
      tool_offsets: {button: gid(`${param.pid}_tool_offsets_button`), tab: gid(`${param.pid}_tool_offsets_tab`)},
      term: {button: gid(`${param.pid}_term_button`), tab: gid(`${param.pid}_term_tab`)}
    }

    for (const [key, value] of Object.entries(this.tabs)) {
      value.button.addEventListener('click', function () { self.set_tabs(key) });
    }
    
    this.create_machine_table();
    this.create_grbl_coms_table();
    Terminal.init(param, true);  // initialize the terminal
  }

  create_machine_table() {
    const machine_table = gid(`${this.pid}_machine_table`);
    console.log(machine_table);
    // First row: Move Machine headers
    const headerRow = document.createElement('tr');
    const headers = [
        { text: 'Move Machine:', colspan: 2 },
        'Position',
        'Offset',
        'Absolute Pos',
        { text: 'Encoders', colspan: 2 }
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

    // Axes rows: t, p, z, a, b, c
    const axes = ['x', 'y', 'z', 'a', 'b', 'c'];
    axes.forEach(axis => {
        const row = document.createElement('tr');

        // Label cell
        const labelCell = document.createElement('td');
        labelCell.innerHTML = `<strong>${axis}: </strong>`;
        labelCell.style.width = '5px';
        row.appendChild(labelCell);

        // Input cell
        const inputCell = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.width = '100%';
        input.id = `${this.pid}move_${axis}`;
        inputCell.appendChild(input);
        row.appendChild(inputCell);

        // Position, Offset, Absolute Pos cells
        ['pos', 'offset', 'abs', 'enc'].forEach(suffix => {
            const cell = document.createElement('td');
            const div = document.createElement('div');
            div.id = `${this.pid}_${axis}${suffix}`;
            div.textContent = 'None';
            cell.appendChild(div);
            row.appendChild(cell);
        });

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
    const msg = JSON.parse(data);
    if (msg.cmd == 'post') {
      Terminal.write(gid(`${pid}_terminal`), msg.data);
      let command = msg.data;
      if (command[0] === '$') {
        // we have a command frame
        if (command.includes('=')) {
          pieces = command.split('=')
          let table = document.getElementById('machine_table');
          for (const row of table.rows) {
            if (row.cells[0].innerHTML.includes(pieces[0])) {
              row.cells[1].querySelector('input').value = pieces[1]
            }
          }
        }
      }
    }
    else if (msg.cmd == 'status') {
      gid(`${pid}_xpos`).innerHTML = msg.x;
      gid(`${pid}_ypos`).innerHTML = msg.y;
      gid(`${pid}_zpos`).innerHTML = msg.z;
      gid(`${pid}_apos`).innerHTML = msg.a;
      gid(`${pid}_bpos`).innerHTML = msg.b;
      gid(`${pid}_cpos`).innerHTML = msg.c;
      gid(`${pid}_theta_enc`).innerHTML = msg.theta_enc;
      gid(`${pid}_phi_enc`).innerHTML = msg.phi_enc;
      gid(`${pid}_state`).innerHTML = `Status: ${msg.state}`;
      if (gid(`${pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
        gid(`${pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
      }
      else { gid(`${pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)"; }
      if (gid(`${pid}_show_status`).checked == true) {
        Terminal.write(gid(`${pid}_terminal`), JSON.stringify(msg));
      }
      // const pos = GRBLScara.fk(param.pid, msg.x, msg.y);
      const pos = GRBLScara.fk(pid, msg.theta_enc, msg.phi_enc);
      gid(`${pid}_cart_x`).innerHTML = pos[0];
      gid(`${pid}_cart_y`).innerHTML = pos[1];
      gid(`${pid}_cart_z`).innerHTML = msg.z;

    }
    // else if (msg.cmd == 'set_offset') {
    //   gid(`${param.pid}_xoffset`).innerHTML = msg.x;
    //   gid(`${param.pid}_yoffset`).innerHTML = msg.y;
    //   gid(`${param.pid}_zoffset`).innerHTML = msg.z;
    //   gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
    // }
    else if (msg.cmd == 'set_work_offset') {
      let table = gid(`${pid}_machine_table`);
      axes = ['x', 'y', 'z', 'a', 'b', 'c'];
      for (let i = 1; i < 7; i++) {
        table.rows[i].cells[3].innerHTML = msg.data[axes[i - 1]];
      }
      table.rows[7].cells[3].innerHTML = "Name: " + msg.data.name;
    }
  }
  
  send(cmd, payload) {
    if (cmd == 'req_w_offset') {
      // this function will send a request to main to get machine position 
      // and return another value to actually 
      let table = gid(`${pid}_work_offsets_table`)
      let name = table.rows[payload + 1].cells[1].querySelector('input').value
      let data = {
        cmd: 'req_w_offset',
        off_id: payload,
        name: name
      }
      hermes.send_json(pid, data);
    }
  }

  change_work_offset(id, from_machine) {
    function get_val(cell) {
      return cell.querySelector('input').value
    }
    function set_val(cell, val) {
      cell.querySelector('input').value = val
    }
    cells = gid(`${this.pid}_work_offsets_table`).rows[id + 1].cells
    if (from_machine === true) { // we're putting the submition and reply in the same function
      console.log('apply')
      return
    }
    console.log('submit');
    let offset = {
      cmd: 'set_work_offset',
      name: get_val(cells[1]),
      x: parseFloat(get_val(cells[2])),
      y: parseFloat(get_val(cells[3])),
      z: parseFloat(get_val(cells[4])),
      a: parseFloat(get_val(cells[5])),
    }
    hermes.send_json(pid, offset)
    console.log(offset)
  }

  set_tabs(tab) {
    for (const [key, value] of Object.entries(this.tabs)) {
      const button = value.button;
      if (key == tab) {
        value.tab.style.display = "block";
        if (button.classList.contains('green')) {
          console.log(button)
          button.classList.remove('green');
          button.classList.add('blue');
        }
      }
      else {
        value.tab.style.display = "none";
        if (button.classList.contains('blue')) {
          console.log(button)
          button.classList.remove('blue');
          button.classList.add('green');
        }
      }
    }
  }

  fk(theta_deg, phi_deg, a_deg = null) {
    // forward kinematics
    const theta = theta_deg * Math.PI / 180;
    const phi = phi_deg * Math.PI / 180;
    const c2 = (this.theta_2 + this.phi_2) - (2 * this.theta_len * this.phi_len * Math.cos(Math.PI - phi));
    const c = Math.sqrt(c2);
    const B = Math.acos((c2 + this.theta_2 - this.phi_2) / (2 * c * this.theta_len));
    const new_theta = theta + B;
    // we implicitly to the coordinate tranform here
    let y = -Math.cos(new_theta) * c;
    let x = Math.sin(new_theta) * c;
    return [x.toFixed(3), y.toFixed(3)];
  }

  create_grbl_coms_table() {
    const self = this;
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