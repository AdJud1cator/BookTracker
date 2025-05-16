// Save the native fetch function
const originalFetch = window.fetch;

async function getCsrfToken() {
    const response = await originalFetch('/csrf-token'); // Use original fetch
    const data = await response.json();
    return data.csrf_token;
}

async function customFetch(url, options = {}) {
    // Bypass CSRF for external APIs
    if (url.startsWith('https://www.googleapis.com')) {
        return originalFetch(url, options);
    }

    const csrfToken = await getCsrfToken();
    options.headers = options.headers || {};
    options.headers['X-CSRF-Token'] = csrfToken;

    return originalFetch(url, options);
}

// Override global fetch function
window.fetch = customFetch;