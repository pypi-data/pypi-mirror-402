from django.http import HttpResponse

from ..settings import comment_settings

TEMPLATE = """
<html><body>
<div id="turnstile-container"></div>
<script>
let port = null;
window.addEventListener('message', function (e) {
  if (e.data === 'channel' && e.ports.length) {
    port = e.ports[0]
  }
})
window.onloadTurnstileCallback = function () {
  turnstile.render("#turnstile-container", {
    sitekey: "{{site_key}}",
    callback: function (token) {
      port.postMessage(JSON.stringify({ type: 'captcha.token', token }));
    },
  });
};
</script>
<script
  src="https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onloadTurnstileCallback"
  defer
>
</script></body></html>
"""


def turnstile_view(request):
    content = TEMPLATE.replace('{{site_key}}', comment_settings.TURNSTILE_SITE_KEY)
    return HttpResponse(content)
