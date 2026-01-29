/*
 * Handle locale selection.
 */
document.addEventListener('DOMContentLoaded', function () {
  const LOCALE_COOKIE_NAME = 'locale';
  const ONE_YEAR = 60 * 60 * 24 * 365;

  function setLocaleCookie(locale) {
    document.cookie = `${LOCALE_COOKIE_NAME}=${locale}; path=/; max-age=${ONE_YEAR}; SameSite=Lax`;
  }

  function onLanguageClick(event) {
    const locale = event.target.dataset.locale;
    if (!locale) return;

    setLocaleCookie(locale);

    // Reload page so backend can use the new language
    window.location.reload();
  }

  document.querySelectorAll('.btn-locale').forEach(btn => {
    btn.addEventListener('click', onLanguageClick);
  });
  
});