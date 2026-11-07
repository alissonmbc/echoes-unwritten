// Keyboard and mouse menus. The router sends actions here, so the buttons never take DOM focus:
// a focused button would also fire on Enter or Space and run its item twice.
export function moveFocus(items, index, delta) {
  const n = items.length;
  for (let i = 1; i <= n; i++) {
    const j = ((index + delta * i) % n + n) % n;
    if (!items[j].disabled) return j;
  }
  return index;
}

export function createMenu(root) {
  let current = null, focus = 0, buttons = [];

  const paint = () => buttons.forEach((b, i) => b.classList.toggle('focus', i === focus));
  const run = item => { if (!item.disabled) item.run(); };

  function show(def) {
    current = def;
    focus = def.items.findIndex(i => !i.disabled);
    root.className = def.variant;
    root.replaceChildren();
    const h = document.createElement('h2'); h.textContent = def.heading; root.append(h);
    if (def.subtitle) { const p = document.createElement('p'); p.textContent = def.subtitle; root.append(p); }
    buttons = def.items.map((item, i) => {
      const b = document.createElement('button');
      b.type = 'button'; b.tabIndex = -1; b.disabled = !!item.disabled; b.textContent = item.label; b.dataset.item = item.id;
      if (item.reason) { const s = document.createElement('small'); s.textContent = item.reason; b.append(s); }
      // Real movement only: a menu opening under a resting mouse must not steal focus, or Esc then Enter would hit Quit.
      b.onpointermove = e => { if (!item.disabled && (e.movementX || e.movementY)) { focus = i; paint(); } };
      b.onmousedown = e => e.preventDefault();
      b.onclick = () => run(item);
      root.append(b);
      return b;
    });
    paint();
  }
  function hide() { current = null; buttons = []; root.className = ''; root.replaceChildren(); }

  function handle(action) {
    if (!current) return;
    if (action === 'MenuUp') focus = moveFocus(current.items, focus, -1);
    else if (action === 'MenuDown') focus = moveFocus(current.items, focus, 1);
    else if (action === 'MenuConfirm') return run(current.items[focus]);
    else if (action === 'MenuBack') return current.onBack?.();
    paint();
  }
  return { show, hide, handle };
}
