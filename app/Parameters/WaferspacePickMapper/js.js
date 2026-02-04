class WaferspacePickMapper extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.pid = param.pid;
    this.projects = gid(`${param.pid}_projects`);
    this.generate_button = gid(`${param.pid}_generate`);
    this.send_all_button = gid(`${param.pid}_send_all`);

    this.generate_button.onclick = () => {
      const cmd = {cmd: 'generate_projects'};
      hermes.send_json(this.pid, cmd);
    };

    this.send_all_button.onclick = () => {
      const cmd = {cmd: 'send_all'};
      hermes.send_json(this.pid, cmd);
    };
  }

  getHTML(param) {
    return `{{ html }}`
  }

  generateProjects(projects) {
    console.log("Generating projects", projects);
    this.projects.innerHTML = "";
    for (const [size, projectList] of Object.entries(projects)) {
      const sizeGroup = document.createElement("div");
      const sizeLabel = document.createElement("text");
      sizeLabel.innerText = size;
      sizeGroup.appendChild(sizeLabel);
      
      for (const project of projectList.sort()) {
        const button = document.createElement("button");
        button.innerText = project;
        button.onclick = () => this.project_buttons(project);
        sizeGroup.appendChild(button);
      }
      this.projects.appendChild(sizeGroup);
    }
  }

  generateReticles(reticles) {
    console.log("Generating reticles", reticles);
    const reticleDiv = gid(`${this.pid}_reticles`);
    reticleDiv.innerHTML = "";
    for (const reticle of reticles.sort()) {
      const button = document.createElement("button");
      button.innerText = reticle;
      button.onclick = () => this.reticle_buttons(reticle);
      reticleDiv.appendChild(button);
    }
  }

  project_buttons(project) {
    const cmd = {cmd: 'do_project', project: project};
    hermes.send_json(this.pid, cmd);
  }

  reticle_buttons(reticle) {
    const cmd = {cmd: 'do_reticle', reticle: reticle};
    hermes.send_json(this.pid, cmd);
  }

  call(data) {
    console.log("Mapper call", data);
    data = JSON.parse(data);
    if (data.cmd === 'wafermap') {
      this.generateProjects(data.projects);
      this.generateReticles(data.reticles);
      this.generate_button.disabled = true;
    }
  }
}