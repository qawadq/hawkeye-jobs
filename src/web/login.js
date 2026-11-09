(() => {
  const form = document.getElementById("login-form");
  const password = document.getElementById("password");
  const button = document.getElementById("submit");
  const message = document.getElementById("message");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.textContent = "";
    button.disabled = true;
    button.textContent = "جارٍ التحقق…";
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password.value }),
        cache: "no-store"
      });
      if (response.ok) {
        location.replace("/");
        return;
      }
      if (response.status === 429) {
        const seconds = Number(response.headers.get("Retry-After")) || 900;
        message.textContent = "محاولات كثيرة. حاول مرة أخرى بعد " + Math.ceil(seconds / 60) + " دقيقة.";
      } else if (response.status === 401) {
        message.textContent = "كلمة المرور غير صحيحة.";
        password.select();
      } else {
        message.textContent = "تعذر تسجيل الدخول. حاول مرة أخرى.";
      }
    } catch (_) {
      message.textContent = "تعذر الاتصال بالخادم.";
    } finally {
      button.disabled = false;
      button.textContent = "دخول";
    }
  });
})();
