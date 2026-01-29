/**
 * aiterm Theme Toggle
 * Handles localStorage persistence and high-contrast mode
 * localStorage key: aiterm-theme (as per spec)
 */

(function() {
  const STORAGE_KEY = 'aiterm-theme';
  const THEMES = ['auto', 'light', 'dark', 'high-contrast'];

  // Get current theme index from Material's palette
  function getCurrentThemeIndex() {
    const palette = document.querySelector('[data-md-color-switching]');
    if (!palette) return 0;

    const scheme = document.body.getAttribute('data-md-color-scheme');
    const icon = document.querySelector('.md-header [data-md-component="palette"] button svg use');

    if (!icon) return 0;

    const iconHref = icon.getAttribute('href') || '';

    if (iconHref.includes('brightness-auto')) return 0;  // auto
    if (iconHref.includes('weather-sunny')) return 1;    // light
    if (iconHref.includes('weather-night')) return 2;    // dark
    if (iconHref.includes('contrast-circle')) return 3;  // high-contrast

    return 0;
  }

  // Apply high-contrast class when needed
  function applyHighContrast(enabled) {
    if (enabled) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  }

  // Save theme preference
  function saveTheme(themeIndex) {
    const themeName = THEMES[themeIndex] || 'auto';
    localStorage.setItem(STORAGE_KEY, themeName);

    // Apply high-contrast if selected
    applyHighContrast(themeName === 'high-contrast');
  }

  // Load saved theme preference
  function loadSavedTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'high-contrast') {
      applyHighContrast(true);
    }
  }

  // Initialize on DOM ready
  function init() {
    loadSavedTheme();

    // Watch for palette toggle clicks
    const paletteButton = document.querySelector('[data-md-component="palette"]');
    if (paletteButton) {
      paletteButton.addEventListener('click', function() {
        // Small delay to let Material update the theme
        setTimeout(function() {
          const index = getCurrentThemeIndex();
          saveTheme(index);
        }, 100);
      });
    }

    // Also observe body attribute changes for theme switches
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'data-md-color-scheme') {
          const index = getCurrentThemeIndex();
          saveTheme(index);
        }
      });
    });

    observer.observe(document.body, { attributes: true });
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
