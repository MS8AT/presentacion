(() => {
  const supported = ['ru', 'zh', 'en'];
  const saved = localStorage.getItem('future-flow-language');
  const browser = (navigator.language || 'ru').toLowerCase();
  const initial = supported.includes(saved) ? saved : (browser.startsWith('zh') ? 'zh' : browser.startsWith('en') ? 'en' : 'ru');

  function selectLanguage(lang) {
    if (!supported.includes(lang)) return;
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang;
    document.querySelectorAll('[data-lang]').forEach(node => node.classList.toggle('active', node.dataset.lang === lang));
    document.querySelectorAll('[data-lang-image]').forEach(node => node.classList.toggle('active', node.dataset.langImage === lang));
    document.querySelectorAll('[data-select-lang]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.selectLang === lang)));
    document.querySelectorAll('video').forEach(video => { if (!video.closest('[data-lang]')?.classList.contains('active')) video.pause(); });
    localStorage.setItem('future-flow-language', lang);
  }

  document.querySelectorAll('[data-select-lang]').forEach(button => button.addEventListener('click', () => selectLanguage(button.dataset.selectLang)));
  selectLanguage(initial);
})();
