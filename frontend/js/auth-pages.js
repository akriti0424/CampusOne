
  import { Auth, Api, escapeHtml } from './api.js';
  if (Auth.getToken()) window.location.href = "app.html";

  function showAlert(message, type = "error") {
    document.getElementById("alert-box").innerHTML =
      `<div class="alert alert-${type}">${escapeHtml(message)}</div>`;
  }

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    try {
      const data = await Api.login({ email, password });
      Auth.setSession(data.token.access_token, data.user);
      window.location.href = "app.html";
    } catch (err) {
      showAlert(err.message);
    }
  });

  document.getElementById("signup-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      full_name: document.getElementById("signup-name").value,
      scholar_id: document.getElementById("signup-scholar").value,
      branch: document.getElementById("signup-branch").value,
      email: document.getElementById("signup-email").value,
      password: document.getElementById("signup-password").value,
    };
    try {
      await Api.register(payload);
      document.getElementById("verify-email").value = payload.email;
      document.getElementById("login-form").classList.add("hidden");
      document.getElementById("signup-form").classList.add("hidden");
      document.getElementById("verify-form").classList.remove("hidden");
      document.getElementById("tab-login").classList.remove("active");
      document.getElementById("tab-signup").classList.remove("active");
      showAlert("We sent a verification code. Enter it below to finish creating your account.", "success");
    } catch (err) {
      showAlert(err.message);
    }
  });

  document.getElementById("verify-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await Api.verifyEmail({
        email: document.getElementById("verify-email").value,
        otp: document.getElementById("verify-otp").value.trim(),
      });
      Auth.setSession(data.token.access_token, data.user);
      window.location.href = "app.html";
    } catch (err) {
      showAlert(err.message);
    }
  });

  document.getElementById("resend-code").addEventListener("click", async () => {
    try {
      await Api.resendVerification(document.getElementById("verify-email").value);
      showAlert("A new verification code was sent.", "success");
    } catch (err) {
      showAlert(err.message);
    }
  });


const dialog = document.getElementById('auth-dialog');
let previousOverflow = '';
function switchTab(which) {
  for (const name of ['login', 'signup']) {
    document.getElementById(`${name}-form`).classList.toggle('hidden', name !== which);
    document.getElementById(`tab-${name}`).classList.toggle('active', name === which);
  }
  document.getElementById('forgot-form').classList.add('hidden');
  document.getElementById('reset-form').classList.add('hidden');
  document.getElementById('verify-form').classList.add('hidden');
  document.getElementById('alert-box').textContent = '';
  document.querySelector('.auth-page-title').textContent = which === 'login' ? 'Welcome back.' : 'Join your campus.';
}
function openForgotPassword() {
  document.getElementById('login-form').classList.add('hidden');
  document.getElementById('signup-form').classList.add('hidden');
  document.getElementById('verify-form').classList.add('hidden');
  document.getElementById('forgot-form').classList.remove('hidden');
  document.querySelector('.auth-page-title').textContent = 'Reset your password.';
  document.getElementById('forgot-email').focus();
}
function openAuth(which) {
  switchTab(which);
  if (!dialog.open) {
    previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }
  history.replaceState(null, '', `#${which}`);
  document.getElementById(which === 'login' ? 'login-email' : 'signup-name').focus();
}
for (const which of ['login','signup']) document.getElementById(`tab-${which}`).addEventListener('click', () => switchTab(which));
document.querySelectorAll('[data-auth]').forEach(link => link.addEventListener('click', event => {
  event.preventDefault();
  openAuth(link.dataset.auth);
}));
document.getElementById('forgot-password').addEventListener('click', openForgotPassword);
document.getElementById('back-to-login').addEventListener('click', () => switchTab('login'));
document.getElementById('forgot-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const email = document.getElementById('forgot-email').value.trim();
  try {
    await Api.forgotPassword(email);
    document.getElementById('reset-email').value = email;
    document.getElementById('forgot-form').classList.add('hidden');
    document.getElementById('reset-form').classList.remove('hidden');
    showAlert('If the account exists, a reset code was sent.', 'success');
  } catch (error) { showAlert(error.message); }
});
document.getElementById('reset-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await Api.resetPassword({
      email: document.getElementById('reset-email').value,
      otp: document.getElementById('reset-otp').value.trim(),
      new_password: document.getElementById('reset-password').value,
    });
    showAlert('Password reset successfully. You can log in now.', 'success');
    document.getElementById('reset-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
    document.querySelector('.auth-page-title').textContent = 'Welcome back.';
  } catch (error) { showAlert(error.message); }
});
document.querySelector('.auth-home').addEventListener('click', (event) => {
  event.preventDefault();
  if (typeof dialog.close === 'function') dialog.close();
  else dialog.removeAttribute('open');
  history.replaceState(null, '', '#home');
});
dialog.addEventListener('close', () => {
  document.body.style.overflow = previousOverflow;
  if (location.hash === '#login' || location.hash === '#signup') history.replaceState(null, '', location.pathname + location.search);
});
if (location.hash === '#login' || location.hash === '#signup') openAuth(location.hash.slice(1));
