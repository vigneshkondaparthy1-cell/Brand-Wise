// Turn a component's trusted, static HTML into nodes before app behavior binds.
function component(markup) {
  const template = document.createElement('template');
  template.innerHTML = markup.trim();
  return template.content;
}
