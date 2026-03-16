document.querySelectorAll('[data-search-input]').forEach((input) => {
  const selector = input.dataset.searchTarget;
  if (!selector) return;
  const items = Array.from(document.querySelectorAll(selector));
  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    items.forEach((item) => {
      const haystack = (item.dataset.searchText || item.textContent || '').toLowerCase();
      const matched = !query || haystack.includes(query);
      item.classList.toggle('is-hidden', !matched);
    });
  });
});
