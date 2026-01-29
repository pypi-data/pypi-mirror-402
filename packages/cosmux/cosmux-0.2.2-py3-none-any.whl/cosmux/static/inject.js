(function() {
  // Prevent double-loading
  if (window.__COSMUX_LOADED__) return;
  window.__COSMUX_LOADED__ = true;

  // Configuration
  var config = window.__COSMUX_CONFIG__ || {};
  var serverUrl = config.serverUrl || 'http://localhost:3333';

  // Load the widget bundle
  var script = document.createElement('script');
  script.src = serverUrl + '/static/cosmux-widget.iife.js';
  script.async = true;

  script.onload = function() {
    console.log('[Cosmux] Widget loaded successfully');
  };

  script.onerror = function() {
    console.error('[Cosmux] Failed to load widget from ' + serverUrl);
    console.error('[Cosmux] Make sure the Cosmux server is running: cosmux serve');
  };

  // Inject when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      document.head.appendChild(script);
    });
  } else {
    document.head.appendChild(script);
  }
})();
