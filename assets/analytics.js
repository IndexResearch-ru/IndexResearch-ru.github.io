// IndexResearch shared analytics bootstrap.
// Add future analytics providers (for example GA4) here so all pages inherit them.
(function () {
  "use strict";

  // Yandex Metrika
  (function(m,e,t,r,i,k,a){
      m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
      m[i].l=1*new Date();
      for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
      k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
  })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=112773213', 'ym');

  ym(112773213, 'init', {
    ssr:true,
    clickmap:true,
    ecommerce:"dataLayer",
    referrer:document.referrer,
    url:location.href,
    accurateTrackBounce:true,
    trackLinks:true
  });

  // GA4 and any future analytics providers belong below this line.
})();
