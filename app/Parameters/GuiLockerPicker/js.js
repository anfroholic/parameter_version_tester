
class GuiLockerPicker extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.websocket = param.websocket;  // pid: Websocket
    this.current_user = null;
    this.state = param.pod
    this.name = param.name
    if (param.websocket != "") {
      let gl_ws = new WebSocket(param.websocket);
      this.websocket = gl_ws;
      let self = this;
      gl_ws.onmessage = function (event) {
        let order = JSON.parse(event.data)
        self.process(order);
      }
    }
    else {
      // We must just be running locally and have a pod
      this.renderTable(param.pod)
    }
    setInterval(this.updateTimeRemaining, 1000, this);
  }

  process(order) {
    console.log('order', order);
    const cmd = order.cmd;
    if (cmd === 'connected') {
      // { cmd: "connected", name: "pallet_racks" }
      console.log('connected', cmd);
      let resp = JSON.stringify({ cmd: 'get', 'name': order.name })
      this.websocket.send(resp)
      console.log('sent', resp)
    }
    if (cmd === 'update_locker') {
      this.updateLockerInfo(order.name, order.address, order.status, order.days)
    }
    if (cmd === 'choose_locker') {
      console.log(this);
      this.current_user = order.user
      this.setClaimButtons('show');
      setTimeout(() => this.setClaimButtons('hide'), 30000);
    }
    if (cmd === 'render_table') {
      // {cmd: renderTable, name: name, pod: dict}: websocket
      // {cmd: renderTable, pod: dict}: hermes
      // console.log(order);
      this.renderTable(order.pod)
    }
  }
  
  call(order) {
    order = JSON.parse(order);
    // console.log(order)
    this.process(order);
  }

  getHTML(param) {
    return `{{ html }}`
  }

  renderTable(pod) {
    const table = document.getElementById(`${this.pid}_lockersTable`);
    this.state = pod;
    // Clear existing rows
    while (table.rows.length > 0) {
      table.deleteRow(0);
    }
    const columnCount = this.state[0].length;
    const columnWidth = 100 / columnCount;
    this.state.forEach(row => {
      const tr = document.createElement('tr');

      row.forEach(locker => {
        const timeRemaining = Math.round((new Date(locker.date) - new Date()) / 1000);
        locker.timeRemaining = timeRemaining;
        const td = document.createElement('td');
        const timeRemainingText = locker.status === 'full' ? `<br>time remaining: <span class="time-remaining" data-address="${locker.address}">${this.formatTime(timeRemaining)}</span>` : '';
        const dateText = locker.status === 'full' ? `<br>date: ${new Date(locker.date).toLocaleString()}` : '';
        const claimButton = locker.status === 'empty' ? `<br><button class="claim_button" onclick="hermes.p[${this.pid}].claimLocker(${locker.address})">Claim</button>` : '';
        td.innerHTML = `name: ${locker.name || 'N/A'}<br>address: <span class="large-text">${locker.address}</span><br>status: ${locker.status}${dateText}${timeRemainingText}${claimButton}`;
        td.className = this.getLockerClass(locker);
        td.style.width = `${columnWidth}%`;
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
  }
  
  formatTime(seconds) {
    // helper function
    const days = Math.floor(seconds / (24 * 3600));
    seconds %= 24 * 3600;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${days}d ${hours}h ${minutes}m ${secs}s`;
  }

  getLockerClass(locker) {
    // helper function
    if (locker.status === 'full') {
      return locker.timeRemaining < 86400 ? 'full-warning' : 'full'; // 86400 seconds = 1 day
    }
    return locker.status;
  }

  updateTimeRemaining(self) {
    // helper function    
    const timeElements = document.querySelectorAll('.time-remaining');
    timeElements.forEach(el => {
      const address = parseInt(el.getAttribute('data-address'));
      for (const lockers of Object.values(self.lockers)) {
        const locker = lockers.flat().find(locker => locker.address === address);
        if (locker && locker.timeRemaining > 0) {
          locker.timeRemaining--;
          el.textContent = self.formatTime(locker.timeRemaining);
          el.closest('td').className = self.getLockerClass(locker);
        }
      }
    });
  }

  updateLockerInfo(name, address, status, days = 0) {
    this.state.forEach(row => {
      row.forEach(locker => {
        if (locker.address === address) {
          locker.name = name;
          locker.status = status;
          if (status === 'full') {
            locker.date = new Date();
            locker.date.setSeconds(locker.date.getSeconds() + days * 24 * 3600);
            locker.timeRemaining = days * 24 * 3600; // Convert days to seconds
          } else {
            delete locker.date;
            delete locker.timeRemaining;
          }
        }
      });
    });
    this.renderTable(this.state);
  }

  claimLocker(address) {
    this.setClaimButtons('hide');

    if (confirm(`Claim locker ${address} for: ${this.current_user}`)) {
      console.log(`${this.current_user} wants locker ${address}`);
      // this is a hack. Fix once you understand better what should happen
      if (this.websocket) {
        let msg = JSON.stringify({
          cmd: 'claim',
          name: this.current_user,
          address: address,
          pod: this.state,
        });
        console.log(msg);
        this.websocket.send(msg)
      }
      hermes.send_json(this.pid, {
        cmd: 'get_locker',
        user: this.current_user,
        pid: this.pid,
        address: address,
      })
    }
  }

  setClaimButtons(display) {
    const buttons = document.getElementsByClassName('claim_button');
    for (const button of buttons) {
      if (display === 'hide') {
        button.style.display = 'none';
      }
      else {
        button.style.display = 'inline-block';
      }
    }
  }
}