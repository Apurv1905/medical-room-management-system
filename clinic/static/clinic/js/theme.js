(function () {
    var themes = ['light', 'dark'];
    var accents = ['blue', 'violet', 'teal', 'emerald', 'rose'];
    var root = document.documentElement;
    var theme;
    var accent;

    try {
        theme = localStorage.getItem('medi-theme');
        accent = localStorage.getItem('medi-accent');
    } catch (error) {
        theme = null;
        accent = null;
    }

    if (themes.indexOf(theme) === -1) {
        theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    if (accents.indexOf(accent) === -1) {
        accent = 'teal';
    }

    root.setAttribute('data-theme', theme);
    root.setAttribute('data-accent', accent);

    function savePreference(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (error) {
            // The current page still responds when browser storage is unavailable.
        }
    }

    function syncControls() {
        var toggle = document.getElementById('themeToggle');
        var icon = document.getElementById('themeIcon');
        var isDark = root.getAttribute('data-theme') === 'dark';

        if (toggle && icon) {
            icon.textContent = isDark ? '☀️' : '🌙';
            toggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
            toggle.setAttribute('aria-pressed', String(isDark));
            toggle.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
        }

        document.querySelectorAll('[data-accent-choice]').forEach(function (swatch) {
            var isActive = swatch.getAttribute('data-accent-choice') === root.getAttribute('data-accent');
            swatch.classList.toggle('active', isActive);
            swatch.setAttribute('aria-pressed', String(isActive));
        });
    }

    function bindControls() {
        var toggle = document.getElementById('themeToggle');

        if (toggle) {
            toggle.addEventListener('click', function () {
                var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
                root.setAttribute('data-theme', next);
                savePreference('medi-theme', next);
                syncControls();
            });
        }

        document.querySelectorAll('[data-accent-choice]').forEach(function (swatch) {
            swatch.addEventListener('click', function () {
                var next = swatch.getAttribute('data-accent-choice');
                if (accents.indexOf(next) === -1) {
                    return;
                }
                root.setAttribute('data-accent', next);
                savePreference('medi-accent', next);
                syncControls();
            });
        });

        syncControls();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindControls);
    } else {
        bindControls();
    }
})();