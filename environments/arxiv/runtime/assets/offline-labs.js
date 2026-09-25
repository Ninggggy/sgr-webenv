document.addEventListener('change', event => {
  if (event.target.matches('#labstabs input.lab-toggle')) {
    event.target.checked = false;
    window.location.assign('/offline/unavailable');
  }
});
