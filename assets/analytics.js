// IndexResearch shared analytics bootstrap.
(function () {
  "use strict";

  var COUNTER_ID = 112773213;
  var TRACKING_KEY = "indexresearch_tracking_v1";
  var TRACKING_KEYS = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "utm_id",
    "gclid",
    "yclid",
    "ysclid"
  ];

  function safeSessionStorage() {
    try {
      var probe = "__indexresearch_probe__";
      sessionStorage.setItem(probe, "1");
      sessionStorage.removeItem(probe);
      return sessionStorage;
    } catch (e) {
      return null;
    }
  }

  var session = safeSessionStorage();

  function queryTracking() {
    var result = {};
    var params = new URLSearchParams(window.location.search);
    TRACKING_KEYS.forEach(function (key) {
      var value = params.get(key);
      if (value) result[key] = value.slice(0, 500);
    });
    return result;
  }

  function storedTracking() {
    if (!session) return {};
    try {
      var parsed = JSON.parse(session.getItem(TRACKING_KEY) || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (e) {
      return {};
    }
  }

  function persistTracking() {
    var merged = Object.assign({}, storedTracking(), queryTracking());
    if (session && Object.keys(merged).length) {
      try {
        session.setItem(TRACKING_KEY, JSON.stringify(merged));
      } catch (e) {}
    }
    return merged;
  }

  persistTracking();

  // Yandex Metrika
  (function(m,e,t,r,i,k,a){
      m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
      m[i].l=1*new Date();
      for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
      k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
  })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=112773213', 'ym');

  ym(COUNTER_ID, 'init', {
    ssr:true,
    clickmap:true,
    ecommerce:"dataLayer",
    referrer:document.referrer,
    url:location.href,
    accurateTrackBounce:true,
    trackLinks:true
  });

  function goal(name, params) {
    if (!name || typeof window.ym !== "function") return false;
    window.ym(COUNTER_ID, "reachGoal", name, params || {});
    return true;
  }

  document.addEventListener("indexresearch:lead-success", function (event) {
    var detail = event && event.detail ? event.detail : {};
    goal("lead_submit_success", {
      form_mode: detail.mode || "unknown",
      lang: detail.lang || document.documentElement.lang || "unknown",
      page_path: window.location.pathname
    });
  });

  window.IndexResearchAnalytics = {
    counterId: COUNTER_ID,
    getTracking: function () {
      return Object.assign({}, storedTracking(), queryTracking());
    },
    goal: goal
  };
})();
