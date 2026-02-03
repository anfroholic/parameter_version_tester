class WsHelper extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.pid = param.pid;
    this.svg = document.getElementById(`${param.pid}_die`);
    this.heatmapSvg = document.getElementById(`${param.pid}_heatmap`);
    this.button = document.getElementById(`${param.pid}_button`);
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    // console.log("WsHelper call", data);
    data = JSON.parse(data);
    const type = data.cmd;
    const svgContent = data.data;
    console.log("WsHelper call type:", type);
    if (type === "die") {   
      this.updateDieSVG(svgContent);
    } else if (type === "heatmap") {
       this.updateHeatmapSVG(svgContent);
    }
  }

  plotWafer() {
    console.log("Plotting wafer for pid:", this.pid);
    this.button.innerText = "Plotting...\nPlease wait\n";
    this.button.disabled = true;
    hermes.send(
      this.pid,
      JSON.stringify({ cmd: "plot_wafer" })
    );
  }
  
  updateDieSVG(svgContent) {
    console.log("Updating Die SVG");
    this.svg.innerHTML = svgContent;
    

    this.die_svg = this.svg.querySelector('svg');
    // Add zoom functionality 

    this.die_svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      console.log("Wheel event", e);
      // Get the current viewBox values
      let [x, y, width, height] = this.die_svg.getAttribute('viewBox').split(' ').map(Number);
      const scaleFactor = 1.1; // Zoom in/out factor

      // Determine zoom direction
      const zoomIn = e.deltaY < 0;
      const scale = zoomIn ? 1 / scaleFactor : scaleFactor;

      // Calculate new width and height
      const width2 = width * scale;
      const height2 = height * scale;

      // Update the viewBox
      this.die_svg.setAttribute('viewBox', `${x} ${y} ${width2} ${height2}`);
    });
    // Add pan functionality
    this.die_isDragging = false;
    this.die_lastX, this.die_lastY;

    this.die_svg.addEventListener("mousedown", (e) => {
      this.die_isDragging = true;
      this.die_lastX = e.clientX;
      this.die_lastY = e.clientY;
    });

    this.die_svg.addEventListener("mousemove", (e) => {
      if (!this.die_isDragging) return;

      const dx = e.clientX - this.die_lastX;
      const dy = e.clientY - this.die_lastY;

      // Update the viewBox
      let [x, y, width, height] = this.die_svg.getAttribute('viewBox').split(' ').map(Number);
      this.die_svg.setAttribute('viewBox', `${x - dx} ${y - dy} ${width} ${height}`);

      this.die_lastX = e.clientX;
      this.die_lastY = e.clientY;
    });

    this.die_svg.addEventListener("mouseup", () => {
      this.die_isDragging = false;
    });
  }

  updateHeatmapSVG(svgContent) {
    this.heatmapSvg.innerHTML = svgContent; 
    this.hm_svg = this.heatmapSvg.querySelector('svg');
    // Add zoom functionality
    this.hm_svg.addEventListener("wheel", (e) => {
      e.preventDefault();
      console.log("Wheel event", e);
      // Get the current viewBox values
      let [x, y, width, height] = this.hm_svg.getAttribute('viewBox').split(' ').map(Number);
      const scaleFactor = 1.1; // Zoom in/out factor

      // Determine zoom direction
      const zoomIn = e.deltaY < 0;
      const scale = zoomIn ? 1 / scaleFactor : scaleFactor;

      // Calculate new width and height
      const width2 = width * scale;
      const height2 = height * scale;

      // Update the viewBox
      this.hm_svg.setAttribute('viewBox', `${x} ${y} ${width2} ${height2}`);
    });
    // Add pan functionality
    this.hm_isDragging = false;
    this.hm_lastX, this.hm_lastY;

    this.hm_svg.addEventListener("mousedown", (e) => {
      this.hm_isDragging = true;
      this.hm_lastX = e.clientX;
      this.hm_lastY = e.clientY;
    });

    this.hm_svg.addEventListener("mousemove", (e) => {
      if (!this.hm_isDragging) return;

      const dx = e.clientX - this.hm_lastX;
      const dy = e.clientY - this.hm_lastY;

      // Update the viewBox
      let [x, y, width, height] = this.hm_svg.getAttribute('viewBox').split(' ').map(Number);
      this.hm_svg.setAttribute('viewBox', `${x - dx} ${y - dy} ${width} ${height}`);

      this.hm_lastX = e.clientX;
      this.hm_lastY = e.clientY;
    });

    this.hm_svg.addEventListener("mouseup", () => {
      this.hm_isDragging = false;
    }); 
  }
}