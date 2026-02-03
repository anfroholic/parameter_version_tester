class WaferSpaceViewer extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const svg = document.getElementById('wafer');
    const descriptionBox = document.getElementById('description');

    const waferDiameterMM = 300;
    const chipWidthMM = 8;
    const chipHeightMM = 10;
    const pxPerMM = 2;

    const waferRadiusPx = (waferDiameterMM / 2) * pxPerMM;
    const centerX = waferRadiusPx;
    const centerY = waferRadiusPx;

    // Define chip type colors
    const chipColors = {
      1: '#FF6666',
      2: '#FFCC66',
      3: '#99CC66',
      4: '#66CCCC',
      5: '#6699FF',
      6: '#9966CC',
      7: '#CC6699',
      8: '#CCCCCC',
      9: '#666666'
    };

    const getChipType = (col, row) => {
      const localCol = col % 3;
      const localRow = row % 3;
      return localRow * 3 + localCol + 1;
    };

    // Draw wafer circle
    const wafer = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    wafer.setAttribute("cx", centerX);
    wafer.setAttribute("cy", centerY);
    wafer.setAttribute("r", waferRadiusPx);
    wafer.setAttribute("fill", "#eee");
    wafer.setAttribute("stroke", "#333");
    svg.appendChild(wafer);

    const chipW = chipWidthMM * pxPerMM;
    const chipH = chipHeightMM * pxPerMM;

    const cols = Math.floor(waferDiameterMM / chipWidthMM);
    const rows = Math.floor(waferDiameterMM / chipHeightMM);

    const offsetX = centerX - (cols * chipW) / 2;
    const offsetY = centerY - (rows * chipH) / 2;

    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const x = offsetX + col * chipW;
        const y = offsetY + row * chipH;

        // Check if chip center is inside the wafer
        const chipCenterX = x + chipW / 2;
        const chipCenterY = y + chipH / 2;
        const dx = chipCenterX - centerX;
        const dy = chipCenterY - centerY;

        if (Math.sqrt(dx * dx + dy * dy) <= waferRadiusPx) {
          const chipType = getChipType(col, row);
          const fillColor = chipColors[chipType] || '#bbb';

          const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", chipW);
          rect.setAttribute("height", chipH);
          rect.setAttribute("class", "chip");
          rect.setAttribute("fill", fillColor);
          rect.addEventListener("click", () => {
            descriptionBox.innerHTML = `<strong>Chip at col ${col}, row ${row}</strong><br>Type: ${chipType}<br>X: ${(col * chipWidthMM).toFixed(1)} mm<br>Y: ${(row * chipHeightMM).toFixed(1)} mm`;
          });
          svg.appendChild(rect);
        }
      }
    }

  }

  getHTML(param) {
    return `{{ html }}`
  }

  call(data) {
    
  }
}
