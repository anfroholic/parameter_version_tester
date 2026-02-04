class GuiPnpFeeder extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;
    // this.rack = param.rack
    this.table = gid(`${param.pid}_table`)
    this.save_button = gid(`${param.pid}_save_button`)
    this.save_button.addEventListener('click', function () { self.send('save_rack', null); })
    this.copy_button = gid(`${param.pid}_copy_button`)
    this.copy_button.addEventListener('click', function () { self.copy_rack(); })
    this.create_feeder_table(param);
    this.set_all(param.rack);
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'set_feeder') {
      console.log(msg)
      this.set_feeder(msg)
    }
    if (msg.cmd == 'saved') {
      this.saved()
    }
    else {
      console.log('unknown command GuiPnpFeeder', msg)
    }
  }

  saved() {
    this.save_button.style.backgroundColor = "#6c6c6c";
    const color = "#304050"
    let first = true;
    for (const row of this.table.rows) {
      if (!first) {
        row.cells[1].querySelector('input').style.backgroundColor = color
        row.cells[2].querySelector('input').style.backgroundColor = color
        row.cells[3].querySelector('input').style.backgroundColor = color
        row.cells[4].querySelector('input').style.backgroundColor = color
        row.cells[5].querySelector('input').style.backgroundColor = color
        row.cells[6].querySelector('input').style.backgroundColor = color
      }
      first = false
    }
  }

  set_all(data) {
    console.log('set all', data);
    for (const component in data) {
      const comp = data[component]
      const row = this.table.rows[comp.id + 1]
      row.cells[1].querySelector('input').value = component
      row.cells[2].querySelector('input').value = comp.x
      row.cells[3].querySelector('input').value = comp.y
      row.cells[4].querySelector('input').value = comp.z
      row.cells[5].querySelector('input').value = comp.a
      row.cells[6].querySelector('input').value = comp.t
    }
  }

  set_feeder(data) {
    // return from when the set button was hit
    const color = "#ff8b8b" // lit color
    for (const component in data) {
      const row = this.table.rows[data.feeder + 1]
      row.cells[1].querySelector('input').style.backgroundColor = color
      row.cells[2].querySelector('input').value = data.x
      row.cells[2].querySelector('input').style.backgroundColor = color
      row.cells[3].querySelector('input').value = data.y
      row.cells[3].querySelector('input').style.backgroundColor = color
      row.cells[4].querySelector('input').value = data.z
      row.cells[4].querySelector('input').style.backgroundColor = color
      row.cells[5].querySelector('input').value = data.a
      row.cells[5].querySelector('input').style.backgroundColor = color
      row.cells[6].querySelector('input').value = data.t
      row.cells[6].querySelector('input').style.backgroundColor = color
    }
    this.save_button.style.backgroundColor = color;
  }

  get_data() {
    let data = {};
    for (let i = 0; i < this.table.rows.length; i++) {
      if (i == 0) { continue };
      const row = this.table.rows[i];
      const val = row.cells[1].querySelector('input').value;
      data[val] = {
        "id": i - 1,
        "x": parseFloat(row.cells[2].querySelector('input').value),
        "y": parseFloat(row.cells[3].querySelector('input').value),
        "z": parseFloat(row.cells[4].querySelector('input').value),
        "a": parseFloat(row.cells[5].querySelector('input').value),
        "t": parseFloat(row.cells[6].querySelector('input').value),
      }
    }
    console.log(data);
    return data
  }

  change(element) {
    // will make background red to note changes that have not been saved
    element.style.backgroundColor = "#ff8b8b";
    this.save_button.style.backgroundColor = "#068770"
  }

  send(action, payload) {
    let data = {};
    console.log('send', action, payload);
    if (action == 'feed') {
      data['feed'] = payload;
    }
    else if (action == 'save_rack') {
      data['save_rack'] = this.get_data();
    }
    else if (action == 'set') {
      data['set'] = payload;
    }
    else if (action == 'set_pos') {
      data['set_pos'] = payload;
    }
    else if (action == 'move_to') {
      const locations = Object.values(this.get_data());
      const location = locations[payload]
      console.log('move to', location);
      data['move_to'] = location;
    }
    else {
      alert(`unknown action from GuiPnpFeeder: ${action}, ${payload}`);
    }
    hermes.send_json(this.pid, data);
  }

  create_feeder_table(param) {
    let self = this;
    console.log('create_feeder_table', this.table);
    for (let i = 0; i < param.num_feeders; i++) {
      let row = document.createElement('tr'); // Create a new row

      // Create the first cell for feeder label
      let feederCell = document.createElement('td');
      feederCell.textContent = `feeder: ${i}`;
      row.appendChild(feederCell);

      // Create the input cells
      let inputs = ['val', 'xpos', 'ypos', 'zpos', 'apos', 'thickness'];
      inputs.forEach(inputType => {
        let cell = document.createElement('td');
        let input = document.createElement('input');

        input.type = inputType === 'val' ? 'text' : 'number';
        input.style.width = '100%';
        input.id = `${param.pid}_${inputType}_${i}`;
        input.value = inputType === 'val' ? `${i}_bbb` : '';
        input.onchange = () => self.change(input);
        input.step = '0.01';
        cell.appendChild(input);
        row.appendChild(cell);
      });

      // Create the button cells
      let actions = [
        { class: 'xsm_button blue', text: 'set', action: 'set' },
        { class: 'xsm_button green', text: 'feed', action: 'feed' },
        { class: 'xsm_button grey', text: 'move_to', action: 'move_to' },
      ];

      actions.forEach(action => {
        let cell = document.createElement('td');
        let button = document.createElement('button');

        button.className = action.class;
        button.textContent = action.text;
        button.onclick = () => self.send(action.action, i);

        cell.appendChild(button);
        row.appendChild(cell);
      });

      this.table.appendChild(row); // Append the row to the table
    }
  }

  copy_rack() {
    // copy rack to the clipboard
    const prettyString = JSON.stringify(this.get_data(), null, 2);
    navigator.clipboard.writeText(prettyString)

    return prettyString;
  }
}