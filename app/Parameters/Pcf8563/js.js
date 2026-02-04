// var Pcf8563 = {
//   getHTML: function (param) {
//     return `{{ !html }}`
//   },
//   pid: 0,
//   init: function (param) {
//     this.pid = param.pid;

//     // Update current time every second
//     setInterval(this.updateCurrentTime, 1000);

//     Pcf8563.add_all_alarms(param.pid, param.alarms, param.current);

//     hermes.p[param.pid] = function (pid, data) {
//       const msg = JSON.parse(data);
//       if (msg.cmd == 'status') {
//         gid(`${pid}_ts`).innerHTML = msg.ts;
//         if (msg.alarm) {
//           gid(`${pid}_alarm`).innerHTML = 'on';
//         }
//         else {
//           gid(`${pid}_alarm`).innerHTML = 'off';
//         }
//         if (msg.state) {
//           gid(`${pid}_state`).innerHTML = 'on';
//         }
//         else {
//           gid(`${pid}_state`).innerHTML = 'off';
//         }
//       }
//       else if (msg.cmd == 'ts') {
//         gid(`${pid}_ts`).innerHTML = msg.ts;
//       }
//       else if (msg.cmd == 'alarms') {
//         Pcf8563.add_all_alarms(pid, msg.alarms, msg.current);
//       }
//     }
//   },
//   clear_alarms: function (pid) {
//     cmd = { cmd: 'clear_alarms' }
//     hermes.send_json(pid, cmd)
//   },
//   add_all_alarms: function (pid, alarms, current) {
//     console.log('adding alarms');
//     gid(`${pid}_current`).innerHTML = current;
//     gid(`${pid}_alarms`).innerHTML = "";
//     for (let alarm of alarms) {
//       Pcf8563.addAlarm(pid, alarm)
//     }
//   },
//   // Function to format datetime as required by the input
//   formatDatetimeForInput: function (datetime) {
//     var year = datetime.getFullYear();
//     var month = ('0' + (datetime.getMonth() + 1)).slice(-2); // Months are zero-based
//     var day = ('0' + datetime.getDate()).slice(-2);
//     var hours = ('0' + datetime.getHours()).slice(-2);
//     var minutes = ('0' + datetime.getMinutes()).slice(-2);
//     return year + month + day + hours + minutes;
//   },
//   // Function to update the current time continuously
//   updateCurrentTime: function () {
//     var currentTimeDiv = gid(`Pcf8563_currentTime`)
//     var now = new Date();
//     var month = ('0' + (now.getMonth() + 1)).slice(-2); // Months are zero-based
//     var day = ('0' + now.getDate()).slice(-2);
//     var year = now.getFullYear();
//     var hours = ('0' + now.getHours()).slice(-2);
//     var minutes = ('0' + now.getMinutes()).slice(-2);
//     var seconds = ('0' + now.getSeconds()).slice(-2);
//     var currentTimeString = 'Current Time: ' + month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
//     currentTimeDiv.textContent = currentTimeString;
//   },
//   please_wait: function (pid) {
//     document.getElementById(`${pid}_alarms`).innerHTML = "Getting alarms<br> please wait";
//   },
//   timestamp2date: function (timestamp) {
//     var year = parseInt(timestamp.slice(0, 4), 10);
//     var month = parseInt(timestamp.slice(4, 6), 10) - 1; // Months are zero-indexed
//     var day = parseInt(timestamp.slice(6, 8), 10);
//     var hour = parseInt(timestamp.slice(8, 10), 10);
//     var minute = parseInt(timestamp.slice(10, 12), 10);
//     return new Date(year, month, day, hour, minute);
//   },
//   date2timestamp: function (date) {
//     var year = date.getFullYear();
//     var month = ('0' + (date.getMonth() + 1)).slice(-2); // Months are zero-indexed
//     var day = ('0' + date.getDate()).slice(-2);
//     var hour = ('0' + date.getHours()).slice(-2);
//     var minute = ('0' + date.getMinutes()).slice(-2);
//     return year + month + day + hour + minute;
//   },
//   add_rel_alarm: function (pid) {
//     var days = parseInt(document.getElementById('days').value, 10);
//     var hours = parseInt(document.getElementById('hours').value, 10);
//     var minutes = parseInt(document.getElementById('minutes').value, 10);
//     var date = document.getElementById(`${pid}_ts`).innerText;
//     let now = this.timestamp2date(date)
//     now.setDate(now.getDate() + days);
//     now.setHours(now.getHours() + hours);
//     now.setMinutes(now.getMinutes() + minutes);
//     let timestamp = this.date2timestamp(now);
//     let callback = document.getElementById(`${pid}_callback`).value;
//     let alarm = timestamp + callback
//     hermes.send_json(pid, { cmd: "add_alarm", alarm: alarm })
//     return false;
//   },

//   add_abs_alarm: function (pid) {
//     var date = document.getElementById(`${pid}_datetimeInput`).value;
//     let callback = document.getElementById(`${pid}_callback`).value;
//     const charactersToRemove = /[-:T]/g;
//     let alarm = date.replace(charactersToRemove, "") + callback;
//     hermes.send_json(pid, { cmd: "add_alarm", alarm: alarm })
//   },
//   delete: function (pid, button) {
//     let alarm = button.previousSibling.data;
//     hermes.send_json(pid, { cmd: 'delete', alarm: alarm })
//     this.please_wait(pid)
//   },

//   eval_change: function (pid, input) {
//     let timestamp = input.previousSibling.previousSibling;
//     hermes.send_json(pid, { cmd: 'eval_change', timestamp: timestamp })
//     this.please_wait(pid)
//   },

//   addAlarm: function (pid, alarm) {
//     var alarmsDiv = document.getElementById(`${pid}_alarms`);
//     console.log(alarm);
//     // var alarmText = this.formatDatetimeForInput(date);


//     var alarmElement = document.createElement('div');
//     alarmElement.textContent = alarm;

//     // Create delete button for the alarm
//     var deleteButton = document.createElement('button');
//     deleteButton.textContent = 'Delete';
//     deleteButton.onclick = function () {
//       Pcf8563.delete(pid, this)
//     };
//     alarmElement.appendChild(deleteButton);

//     // var evalElement = document.createElement('input');
//     // evalElement.style.width = "200px";
//     // evalElement.value = alarm.slice(12);
//     // evalElement.onchange = function() {
//     //   Pcf8563.eval_change(pid, this)
//     // }

//     // alarmElement.appendChild(evalElement);

//     // Add the new alarm to alarms div
//     alarmsDiv.appendChild(alarmElement);


//     // cmd = {cmd: 'set_alarms', alarms: dates}
//     // hermes.send_json(pid, cmd)
//   }
// }


class Pcf8563 extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    // Update current time every second
    setInterval(this.updateCurrentTime, 1000);

    this.add_all_alarms(param.alarms, param.current);
    this.abs_alarm_button = gid(`${this.pid}_abs_alarm_button`);
    this.timeform = gid(`${this.pid}_timeform`);
    this.timeform.onsubmit = function () {
      return this.add_rel_alarm();
    }
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    const msg = JSON.parse(data);
    if (msg.cmd == 'status') {
      gid(`${pid}_ts`).innerHTML = msg.ts;
      if (msg.alarm) {
        gid(`${pid}_alarm`).innerHTML = 'on';
      }
      else {
        gid(`${pid}_alarm`).innerHTML = 'off';
      }
      if (msg.state) {
        gid(`${pid}_state`).innerHTML = 'on';
      }
      else {
        gid(`${pid}_state`).innerHTML = 'off';
      }
    }
    else if (msg.cmd == 'ts') {
      gid(`${pid}_ts`).innerHTML = msg.ts;
    }
    else if (msg.cmd == 'alarms') {
      Pcf8563.add_all_alarms(pid, msg.alarms, msg.current);
    }

  }

  clear_alarms() {
    cmd = { cmd: 'clear_alarms' }
    hermes.send_json(this.pid, cmd)
  }

  add_all_alarms(alarms, current) {
    console.log('adding alarms');
    gid(`${this.pid}_current`).innerHTML = current;
    gid(`${this.pid}_alarms`).innerHTML = "";
    for (let alarm of alarms) {
      this.addAlarm(alarm)
    }
  }

  // Function to format datetime as required by the input
  formatDatetimeForInput(datetime) {
    var year = datetime.getFullYear();
    var month = ('0' + (datetime.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + datetime.getDate()).slice(-2);
    var hours = ('0' + datetime.getHours()).slice(-2);
    var minutes = ('0' + datetime.getMinutes()).slice(-2);
    return year + month + day + hours + minutes;
  }

  // Function to update the current time continuously
  updateCurrentTime() {
    var currentTimeDiv = gid(`Pcf8563_currentTime`)
    var now = new Date();
    var month = ('0' + (now.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + now.getDate()).slice(-2);
    var year = now.getFullYear();
    var hours = ('0' + now.getHours()).slice(-2);
    var minutes = ('0' + now.getMinutes()).slice(-2);
    var seconds = ('0' + now.getSeconds()).slice(-2);
    var currentTimeString = 'Current Time: ' + month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
    currentTimeDiv.textContent = currentTimeString;
  }

  please_wait() {
    document.getElementById(`${this.pid}_alarms`).innerHTML = "Getting alarms<br> please wait";
  }

  timestamp2date(timestamp) {
    var year = parseInt(timestamp.slice(0, 4), 10);
    var month = parseInt(timestamp.slice(4, 6), 10) - 1; // Months are zero-indexed
    var day = parseInt(timestamp.slice(6, 8), 10);
    var hour = parseInt(timestamp.slice(8, 10), 10);
    var minute = parseInt(timestamp.slice(10, 12), 10);
    return new Date(year, month, day, hour, minute);
  }

  date2timestamp(date) {
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2); // Months are zero-indexed
    var day = ('0' + date.getDate()).slice(-2);
    var hour = ('0' + date.getHours()).slice(-2);
    var minute = ('0' + date.getMinutes()).slice(-2);
    return year + month + day + hour + minute;
  }

  add_rel_alarm() {
    var days = parseInt(document.getElementById('days').value, 10);
    var hours = parseInt(document.getElementById('hours').value, 10);
    var minutes = parseInt(document.getElementById('minutes').value, 10);
    var date = document.getElementById(`${this.pid}_ts`).innerText;
    let now = this.timestamp2date(date)
    now.setDate(now.getDate() + days);
    now.setHours(now.getHours() + hours);
    now.setMinutes(now.getMinutes() + minutes);
    let timestamp = this.date2timestamp(now);
    let callback = document.getElementById(`${this.pid}_callback`).value;
    let alarm = timestamp + callback
    hermes.send_json(this.pid, { cmd: "add_alarm", alarm: alarm })
    return false;
  }

  add_abs_alarm() {
    var date = document.getElementById(`${this.pid}_datetimeInput`).value;
    let callback = document.getElementById(`${this.pid}_callback`).value;
    const charactersToRemove = /[-:T]/g;
    let alarm = date.replace(charactersToRemove, "") + callback;
    hermes.send_json(this.pid, { cmd: "add_alarm", alarm: alarm })
  }

  delete(button) {
    let alarm = button.previousSibling.data;
    hermes.send_json(this.pid, { cmd: 'delete', alarm: alarm })
    this.please_wait()
  }

  eval_change(input) {
    let timestamp = input.previousSibling.previousSibling;
    hermes.send_json(this.pid, { cmd: 'eval_change', timestamp: timestamp })
    this.please_wait()
  }

  addAlarm(alarm) {
    var alarmsDiv = document.getElementById(`${this.pid}_alarms`);
    console.log(alarm);

    var alarmElement = document.createElement('div');
    alarmElement.textContent = alarm;

    // Create delete button for the alarm
    var deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function () {
      this.delete(pid, this)
    };
    alarmElement.appendChild(deleteButton);


    alarmsDiv.appendChild(alarmElement);
  }
}