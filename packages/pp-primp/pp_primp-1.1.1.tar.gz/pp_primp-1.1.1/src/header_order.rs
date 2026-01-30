use std::sync::LazyLock;
use rquest::header::{HeaderMap, HeaderName};

/// Browser-specific header order definitions
/// Based on real browser behavior analysis
pub struct HeaderOrder;

// Static header order arrays for different browsers
// Using LazyLock for delayed initialization

pub static CHROME_HEADER_ORDER: LazyLock<Vec<HeaderName>> = LazyLock::new(|| vec![
    HeaderName::from_static("sec-ch-ua"),
    HeaderName::from_static("sec-ch-ua-mobile"),
    HeaderName::from_static("sec-ch-ua-platform"),
    HeaderName::from_static("upgrade-insecure-requests"),
    rquest::header::USER_AGENT,
    rquest::header::ACCEPT,
    HeaderName::from_static("sec-fetch-site"),
    HeaderName::from_static("sec-fetch-mode"),
    HeaderName::from_static("sec-fetch-user"),
    HeaderName::from_static("sec-fetch-dest"),
    rquest::header::ACCEPT_ENCODING,      // accept-encoding在accept-language之前
    rquest::header::ACCEPT_LANGUAGE,
    rquest::header::CACHE_CONTROL,        // cache-control在cookie之前
    rquest::header::PRAGMA,               // pragma在cookie之前
    rquest::header::COOKIE,               // cookie在priority之前
    HeaderName::from_static("priority"),
    rquest::header::AUTHORIZATION,        // authorization在referer之前
    rquest::header::REFERER,
    HeaderName::from_static("origin"),
    rquest::header::CONTENT_TYPE,
    rquest::header::CONTENT_LENGTH,
]);

pub static FIREFOX_HEADER_ORDER: LazyLock<Vec<HeaderName>> = LazyLock::new(|| vec![
    rquest::header::USER_AGENT,
    rquest::header::ACCEPT,
    rquest::header::ACCEPT_LANGUAGE,
    rquest::header::ACCEPT_ENCODING,
    rquest::header::CACHE_CONTROL,               // cache-control在cookie之前
    rquest::header::PRAGMA,                      // pragma在cookie之前
    rquest::header::COOKIE,                      // Cookie在accept-encoding之后
    HeaderName::from_static("upgrade-insecure-requests"),
    HeaderName::from_static("sec-fetch-dest"),
    HeaderName::from_static("sec-fetch-mode"),
    HeaderName::from_static("sec-fetch-site"),
    HeaderName::from_static("sec-fetch-user"),
    HeaderName::from_static("priority"),         // Priority在sec-fetch之后
    HeaderName::from_static("te"),               // TE在最后（Firefox特有）
    rquest::header::AUTHORIZATION,               // authorization在referer之前
    rquest::header::CONNECTION,                  // 可选headers
    rquest::header::REFERER,
    HeaderName::from_static("origin"),
    rquest::header::CONTENT_TYPE,
    rquest::header::CONTENT_LENGTH,
]);

pub static SAFARI_HEADER_ORDER: LazyLock<Vec<HeaderName>> = LazyLock::new(|| vec![
    HeaderName::from_static("sec-fetch-dest"),   // Safari特色：sec-fetch-dest在最前
    rquest::header::USER_AGENT,
    rquest::header::ACCEPT,
    HeaderName::from_static("sec-fetch-site"),
    HeaderName::from_static("sec-fetch-mode"),
    rquest::header::ACCEPT_LANGUAGE,
    HeaderName::from_static("priority"),         // Priority在accept-language之后
    rquest::header::ACCEPT_ENCODING,             // Accept-encoding在priority之后
    rquest::header::CACHE_CONTROL,               // cache-control在cookie之前
    rquest::header::PRAGMA,                      // pragma在cookie之前
    rquest::header::COOKIE,                      // Cookie在最后
    HeaderName::from_static("upgrade-insecure-requests"),
    rquest::header::AUTHORIZATION,               // authorization在referer之前
    rquest::header::CONNECTION,                  // 可选headers
    rquest::header::REFERER,
    HeaderName::from_static("origin"),
    rquest::header::CONTENT_TYPE,
    rquest::header::CONTENT_LENGTH,
]);

pub static OKHTTP_HEADER_ORDER: LazyLock<Vec<HeaderName>> = LazyLock::new(|| vec![
    rquest::header::USER_AGENT,
    rquest::header::ACCEPT,
    rquest::header::ACCEPT_ENCODING,
    rquest::header::CONNECTION,
    rquest::header::COOKIE,
    rquest::header::CONTENT_TYPE,
    rquest::header::CONTENT_LENGTH,
]);

impl HeaderOrder {
    /// Detect browser type from impersonate string and return the appropriate header order
    pub fn get_order_for_browser(impersonate: &str) -> &'static [HeaderName] {
        let impersonate_lower = impersonate.to_lowercase();

        if impersonate_lower.starts_with("chrome") ||
           impersonate_lower.starts_with("edge") ||
           impersonate_lower.starts_with("opera") {
            &CHROME_HEADER_ORDER
        } else if impersonate_lower.starts_with("firefox") {
            &FIREFOX_HEADER_ORDER
        } else if impersonate_lower.starts_with("safari") {
            &SAFARI_HEADER_ORDER
        } else if impersonate_lower.starts_with("okhttp") {
            &OKHTTP_HEADER_ORDER
        } else {
            // Default to Chrome
            &CHROME_HEADER_ORDER
        }
    }

    /// Get the header name after which cookie should be inserted for the given browser
    /// Returns the header name that should come immediately before cookie
    pub fn get_cookie_anchor(impersonate: &str) -> &'static str {
        let impersonate_lower = impersonate.to_lowercase();

        if impersonate_lower.starts_with("chrome") ||
           impersonate_lower.starts_with("edge") ||
           impersonate_lower.starts_with("opera") {
            // Chrome: cookie after accept-language
            "accept-language"
        } else if impersonate_lower.starts_with("firefox") {
            // Firefox: cookie after accept-encoding
            "accept-encoding"
        } else if impersonate_lower.starts_with("safari") {
            // Safari: cookie after accept-encoding
            "accept-encoding"
        } else {
            // Default to Chrome
            "accept-language"
        }
    }
}
