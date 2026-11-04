// Build week2/report/Week2_Report_Group40.docx from week2/report/report.md
// Usage: NODE_PATH=<dir with node_modules/docx> node week2/tools/build_report.js
const d = require('docx');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const mdPath = path.join(root, 'report', 'report.md');
const outPath = path.join(root, 'report', 'Week2_Report_Group40.docx');
const F = 'Calibri';
const SZ = 22;

// inline: **bold**, *italic*, `code`
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new d.TextRun({ text: text.slice(last, m.index), font: F, size: SZ, ...base }));
    const tok = m[0];
    if (tok.startsWith('**')) out.push(new d.TextRun({ text: tok.slice(2, -2), bold: true, font: F, size: SZ, ...base }));
    else if (tok.startsWith('`')) out.push(new d.TextRun({ text: tok.slice(1, -1), font: 'Consolas', size: SZ - 2, ...base }));
    else out.push(new d.TextRun({ text: tok.slice(1, -1), italics: true, font: F, size: SZ, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new d.TextRun({ text: text.slice(last), font: F, size: SZ, ...base }));
  return out;
}

const bd = { style: d.BorderStyle.SINGLE, size: 4, color: '999999' };
const BR = { top: bd, bottom: bd, left: bd, right: bd };

function table(lines) {
  const rows = lines.filter(l => !/^\|\s*-/.test(l)).map(l => l.trim().replace(/^\||\|$/g, '').split('|').map(s => s.trim()));
  const n = rows[0].length;
  const total = 9026;
  // weight columns by longest cell (bounded) so wide text columns get room
  const w = Array.from({ length: n }, (_, i) => Math.min(60, Math.max(8, ...rows.map(r => (r[i] || '').length))));
  const sum = w.reduce((a, b) => a + b, 0);
  let cols = w.map(x => Math.round(total * x / sum));
  cols[n - 1] += total - cols.reduce((a, b) => a + b, 0);
  return new d.Table({
    width: { size: total, type: d.WidthType.DXA },
    columnWidths: cols,
    rows: rows.map((r, k) => new d.TableRow({
      cantSplit: true,
      tableHeader: k === 0,
      children: r.map((t, i) => new d.TableCell({
        width: { size: cols[i], type: d.WidthType.DXA },
        borders: BR,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
        shading: k === 0 ? { type: d.ShadingType.CLEAR, fill: 'D9E2F3', color: 'auto' } : undefined,
        children: [new d.Paragraph({ children: runs(t, { size: 18, bold: k === 0 }) })],
      })),
    })),
  });
}

// PNG size from header
function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }

const lines = fs.readFileSync(mdPath, 'utf8').split(/\r?\n/);
const children = [];
let i = 0;
while (i < lines.length) {
  const l = lines[i];
  if (!l.trim()) { i++; continue; }
  if (l.startsWith('# ')) {
    children.push(new d.Paragraph({ spacing: { after: 100 }, children: [new d.TextRun({ text: l.slice(2), bold: true, size: 40, color: '1F3864', font: F })] }));
  } else if (l.startsWith('### ')) {
    children.push(new d.Paragraph({ keepNext: true, spacing: { before: 140, after: 60 }, children: [new d.TextRun({ text: l.slice(4), bold: true, size: 23, color: '2F5597', font: F })] }));
  } else if (l.startsWith('## ')) {
    children.push(new d.Paragraph({
      heading: d.HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 240, after: 90 },
      border: { bottom: { style: d.BorderStyle.SINGLE, size: 6, color: '1F3864', space: 1 } },
      children: [new d.TextRun({ text: l.slice(3), bold: true, size: 26, color: '1F3864', font: F })],
    }));
  } else if (l.startsWith('|')) {
    const blk = [];
    while (i < lines.length && lines[i].startsWith('|')) blk.push(lines[i++]);
    children.push(table(blk));
    children.push(new d.Paragraph({ spacing: { after: 80 }, children: [] }));
    continue;
  } else if (l.startsWith('![')) {
    const m = /!\[(.*?)\]\((.*?)\)/.exec(l);
    const p = path.resolve(path.dirname(mdPath), m[2]);
    const buf = fs.readFileSync(p);
    const { w, h } = pngSize(buf);
    const W = 560; // px, ~ 5.8in
    children.push(new d.Paragraph({
      alignment: d.AlignmentType.CENTER, spacing: { before: 80, after: 120 }, keepLines: true,
      children: [new d.ImageRun({ type: 'png', data: buf, transformation: { width: W, height: Math.round(W * h / w) },
        altText: { title: m[1], description: m[1], name: m[1] } })],
    }));
  } else if (/^- /.test(l)) {
    children.push(new d.Paragraph({ numbering: { reference: 'b', level: 0 }, spacing: { after: 50 }, children: runs(l.slice(2)) }));
  } else if (/^\d+\. /.test(l)) {
    const mm = /^(\d+)\. (.*)$/.exec(l);
    children.push(new d.Paragraph({ spacing: { after: 50 }, indent: { left: 360, hanging: 360 }, children: runs(`[${mm[1]}]\t${mm[2]}`, { size: 18 }) }));
  } else {
    children.push(new d.Paragraph({ spacing: { after: 100 }, alignment: d.AlignmentType.LEFT, children: runs(l) }));
  }
  i++;
}

const doc = new d.Document({
  styles: { default: { document: { run: { font: F, size: SZ } } } },
  numbering: { config: [{ reference: 'b', levels: [{ level: 0, format: d.LevelFormat.BULLET, text: '•', alignment: d.AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 240 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1440, right: 1440 } } },
    footers: { default: new d.Footer({ children: [new d.Paragraph({ alignment: d.AlignmentType.CENTER, children: [
      new d.TextRun({ text: 'IT457 Group 40 | IRCTC case study | Page ', size: 16, color: '666666', font: F }),
      new d.TextRun({ children: [d.PageNumber.CURRENT], size: 16, color: '666666', font: F }) ] })] }) },
    children,
  }],
});
d.Packer.toBuffer(doc).then(b => { fs.writeFileSync(outPath, b); console.log('wrote', outPath); });
