// Minimal Markdown line model: fenced code blocks, ignore markers and inline code spans.
import { CREATE_MARKERS, MARKERS } from "../config.mjs";

/**
 * @typedef {object} Line
 * @property {number} no          1-based line number
 * @property {string} text
 * @property {boolean} ignored    inside an ignore block / marked line / ignore-file
 * @property {boolean} create     the line documents a file to create (CREATE_MARKERS)
 * @property {CodeBlock|null} block  the fenced block this line belongs to (null = prose)
 *
 * @typedef {object} CodeBlock
 * @property {string} lang
 * @property {number} start       line number of the first content line
 * @property {Line[]} lines       content lines (fences excluded)
 */

const FENCE = /^\s*(`{3,}|~{3,})\s*([^`\s]*)/;

/** Parse a Markdown document into lines and code blocks. */
export function parseMarkdown(source) {
  const raw = source.split(/\r?\n/);
  const ignoreFile = raw.some((l) => l.includes(MARKERS.file));
  /** @type {Line[]} */
  const lines = [];
  /** @type {CodeBlock[]} */
  const blocks = [];
  let fence = null; // { char, len, block }
  let ignoring = false;
  let ignoreNext = false;

  raw.forEach((text, i) => {
    const no = i + 1;
    let ignored = ignoreFile || ignoring || ignoreNext || text.includes(MARKERS.line);
    ignoreNext = false;
    if (text.includes(MARKERS.start)) {
      ignoring = true;
      ignored = true;
    }
    if (text.includes(MARKERS.end)) {
      ignoring = false;
      ignored = true;
    }
    if (text.includes(MARKERS.nextLine)) ignoreNext = true;
    const create = CREATE_MARKERS.some((re) => re.test(text));

    const m = text.match(FENCE);
    if (fence) {
      if (m && m[1][0] === fence.char && m[1].length >= fence.len && !m[2]) {
        fence = null; // closing fence
        lines.push({ no, text, ignored: true, create, block: null });
        return;
      }
      const line = { no, text, ignored, create, block: fence.block };
      fence.block.lines.push(line);
      lines.push(line);
      return;
    }
    if (m) {
      const block = { lang: (m[2] || "").toLowerCase(), start: no + 1, lines: [] };
      blocks.push(block);
      fence = { char: m[1][0], len: m[1].length, block };
      lines.push({ no, text, ignored: true, create, block: null });
      return;
    }
    lines.push({ no, text, ignored, create, block: null });
  });

  return { lines, blocks };
}

/** Inline code spans of a prose line: [{ code, index }]. Handles `` double `` backticks. */
export function inlineCodeSpans(text) {
  const spans = [];
  const re = /(`+)([\s\S]*?[^`])\1(?!`)/g;
  let m;
  while ((m = re.exec(text))) spans.push({ code: m[2].trim(), index: m.index, end: m.index + m[0].length });
  return spans;
}

/** The line with inline code spans blanked out (keeps offsets). */
export function stripInlineCode(text) {
  return text.replace(/(`+)([\s\S]*?[^`])\1(?!`)/g, (s) => " ".repeat(s.length));
}
