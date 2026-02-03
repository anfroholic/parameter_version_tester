class WaferspaceManifestDigester extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.pid = param.pid;
    this.svg = document.getElementById(`${param.pid}_map`);
    this.button = document.getElementById(`${param.pid}_button`);
    this.SVG_NS = "http://www.w3.org/2000/svg";
  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    // console.log("Manifester call", data);
    data = JSON.parse(data);

    this.renderSvgFromSlots(data.layout);
  }

  createSvgEl(tag, attrs = {}) {
    const el = document.createElementNS(this.SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      el.setAttribute(k, v);
    }
    return el;
  }

  renderSvgFromSlots(data) {
  

  const SLOT_DIMENSIONS = {
    "1x1":   { w: 4, h: 5 },
    "0p5x1": { w: 2, h: 5 },
    "1x0p5": { w: 4, h: 2.5 },
    "0p5x0p5": { w: 2, h: 2.5 },
  };

  const TILE_GAP = 0.25; // spacing between tiles
  const ROW_GAP  = 0.5;

  

  function wrapText(text, maxCharsPerLine = 18) {
    const words = text.split(" ");
    const lines = [];
    let line = "";

    for (const word of words) {
      if ((line + " " + word).trim().length > maxCharsPerLine) {
        lines.push(line.trim());
        line = word;
      } else {
        line += " " + word;
      }
    }
    if (line.trim()) lines.push(line.trim());
    return lines.slice(0, 2); // cap at two lines
  }

  let cursorY = 0;
  let totalWidth = 0;

  const svg = this.createSvgEl("svg", {
    xmlns: this.SVG_NS,
    style: "width: 100%; height: auto; font-family: sans-serif;"
  });

  const rootGroup = this.createSvgEl("g");
  svg.appendChild(rootGroup);

  data.forEach(row => {
    let cursorX = 0;
    let rowHeight = 0;

    // Precompute row height
    row.forEach(tile => {
      const dim = SLOT_DIMENSIONS[tile.slot_size];
      if (!dim) {
        throw new Error(`Unknown slot_size: ${tile.slot_size}`);
      }
      rowHeight = Math.max(rowHeight, dim.h);
    });

    row.forEach(tile => {
      const { w, h } = SLOT_DIMENSIONS[tile.slot_size];

      const g = this.createSvgEl("g", {
        class: "tile",
        transform: `translate(${cursorX}, ${cursorY})`,
        "data-code": tile.code,
        "data-project": tile.project,
        "data-slot-size": tile.slot_size,
        style: "cursor: pointer;"
      });

      const rect = this.createSvgEl("rect", {
        x: 0,
        y: 0,
        width: w,
        height: h,
        rx: 0.25,
        ry: 0.25,
        fill: "#f2f2f2",
        stroke: "#333",
        "stroke-width": 0.05
      });

      g.appendChild(rect);

      // Code text (centered)
      const codeText = this.createSvgEl("text", {
        x: w / 2,
        y: h / 2 - 0.3,
        "text-anchor": "middle",
        "dominant-baseline": "middle",
        "font-size": 0.9,
        "font-weight": "bold",
        fill: "#000"
      });
      codeText.textContent = tile.code;
      g.appendChild(codeText);

      // Project text (wrapped)
      const projectLines = wrapText(tile.project);
      projectLines.forEach((line, i) => {
        const t = this.createSvgEl("text", {
          x: w / 2,
          y: h / 2 + 0.7 + i * 0.6,
          "text-anchor": "middle",
          "font-size": 0.45,
          fill: "#333"
        });
        t.textContent = line;
        g.appendChild(t);
      });

      rootGroup.appendChild(g);

      cursorX += w + TILE_GAP;
      totalWidth = Math.max(totalWidth, cursorX);
    });

    cursorY += rowHeight + ROW_GAP;
  });

  svg.setAttribute("viewBox", `0 0 ${totalWidth} ${cursorY}`);
  console.log(svg);
  this.svg.innerHTML = '';
  this.svg.appendChild(svg);
}
  generate() {
    console.log("Generating wafer manifest...");
    hermes.send(this.pid, JSON.stringify({cmd: "generate"}));
  }
}