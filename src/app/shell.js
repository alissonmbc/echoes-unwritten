// Connects the mode machine, input router and menus to the page. The scene only reads from this and gets callbacks.
import { Mode, ModeMachine } from '../core/modes.js';
import { InputRouter, MODE_CONTEXT } from '../core/input.js';
import { createMenu } from '../ui/menu.js';

export function createShell({ menuRoot, onNewGame, onQuitToTitle, onAction, onModeChange }) {
  const modes = new ModeMachine(), input = new InputRouter(), menu = createMenu(menuRoot);
  const html = document.documentElement;

  const titleMenu = {
    variant: 'title', heading: 'Echoes of the Unwritten', subtitle: 'Lumina',
    items: [
      { id: 'new', label: 'New Game', run() { onNewGame(); modes.to(Mode.Exploration); } },
      { id: 'continue', label: 'Continue', disabled: true, reason: 'No save yet' },
      { id: 'settings', label: 'Settings', disabled: true, reason: 'Not built yet' },
    ],
  };
  const pauseMenu = {
    variant: 'pause', heading: 'Paused', onBack: () => modes.resume(),
    items: [
      { id: 'resume', label: 'Resume', run: () => modes.resume() },
      { id: 'quit', label: 'Quit to Title', run() { onQuitToTitle(); modes.quitToMenu(); } },
    ],
  };

  html.dataset.mode = modes.mode;
  input.setContext(MODE_CONTEXT[modes.mode]);
  modes.onChange(event => {
    input.setContext(MODE_CONTEXT[event.to]);
    html.dataset.mode = event.to;
    if (event.to === Mode.MainMenu) menu.show(titleMenu);
    else if (event.to === Mode.Paused) menu.show(pauseMenu);
    else menu.hide();
    onModeChange(event);
  });

  addEventListener('keydown', e => {
    if (e.ctrlKey || e.altKey || e.metaKey) return;   // leave browser shortcuts alone
    const action = input.keyDown(e.code);
    if (!action) return;
    e.preventDefault();
    if (input.context === 'menu') menu.handle(action);
    else if (action === 'Pause') modes.pause();
    else onAction(action);
  });
  addEventListener('keyup', e => input.keyUp(e.code));
  addEventListener('blur', () => input.releaseAll());

  return {
    modes, input,
    start({ skipTitle }) { modes.to(Mode.MainMenu); if (skipTitle) modes.to(Mode.Exploration); },
  };
}
