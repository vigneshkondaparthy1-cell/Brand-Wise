
document.addEventListener('contextmenu', event => event.preventDefault());

try {
  if (localStorage.getItem('brandwise-theme') === 'dark') {
    document.documentElement.dataset.theme = 'dark';
  }
} catch {}
