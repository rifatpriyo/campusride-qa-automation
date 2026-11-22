"use strict";

async function postJSON(url, payload) {
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error("The app could not be reached. Try again.");
  }

  if (response.status === 204) return null;
  const result = await response.json().catch(() => null);
  if (response.ok) return result;

  const detail = result?.detail;
  if (Array.isArray(detail)) {
    const errors = detail.map(({ loc, msg }) => {
      const field = loc.length > 1 ? String(loc.at(-1)).replaceAll("_", " ") + " — " : "";
      return field + msg.replace(/^Value error, /, "");
    });
    throw new Error(errors.join(" "));
  }
  throw new Error(detail || `The action failed (HTTP ${response.status}). Try again.`);
}

function formData(form, submitter) {
  const values = Object.fromEntries(new FormData(form));
  if (submitter?.name) values[submitter.name] = submitter.value;
  for (const input of form.querySelectorAll('input[type="checkbox"][name]')) {
    values[input.name] = input.checked;
  }
  for (const input of form.querySelectorAll("[data-number]")) {
    values[input.name] = Number(input.value);
  }
  return values;
}

function errorFor(form) {
  return form.querySelector("[data-error]") || document.querySelector("#page-error");
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = !message;
}

function beginSubmission(form) {
  showError(errorFor(form), "");
  const buttons = [...form.querySelectorAll('button[type="submit"]:not(:disabled)')];
  buttons.forEach((button) => { button.disabled = true; });
  form.setAttribute("aria-busy", "true");
  return () => {
    form.removeAttribute("aria-busy");
    buttons.forEach((button) => { button.disabled = false; });
  };
}

function navigateAfterSubmit(next, data) {
  if (next === "account") {
    if (data.roles.includes("admin")) window.location.assign("/admin");
    else if (data.roles.includes("rider")) window.location.assign("/rider");
    else window.location.assign("/passenger");
  } else if (next === "ride") {
    window.location.assign(`/rides/${data.id}`);
  } else if (next) {
    window.location.assign(next);
  } else {
    window.location.reload();
  }
}

function configureBooking(quoteForm) {
  const booking = document.querySelector("[data-confirm-booking]");
  const details = document.querySelector("[data-quote-details]");
  const placeholder = document.querySelector("[data-quote-placeholder]");
  const confirm = booking.querySelector('button[type="submit"]');
  const quoteId = booking.elements.quote_id;
  let revision = 0;

  function resetQuote() {
    revision += 1;
    quoteId.value = "";
    confirm.disabled = true;
    details.hidden = true;
    placeholder.hidden = false;
    showError(errorFor(booking), "");
    showError(errorFor(quoteForm), "");
  }

  quoteForm.addEventListener("change", resetQuote);
  quoteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (quoteForm.hasAttribute("aria-busy") || booking.hasAttribute("aria-busy")) return;
    resetQuote();
    const version = revision;
    const finish = beginSubmission(quoteForm);
    try {
      const quote = await postJSON(quoteForm.action, formData(quoteForm));
      if (version !== revision) return;
      details.querySelector("[data-fare]").textContent = quote.fare_bdt;
      quoteId.value = quote.id;
      details.hidden = false;
      placeholder.hidden = true;
      confirm.disabled = false;
    } catch (error) {
      if (version === revision) showError(errorFor(quoteForm), error.message);
    } finally {
      finish();
    }
  });
}

for (const form of document.querySelectorAll("[data-api-form]")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (form.hasAttribute("aria-busy")) return;
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) return;
    const values = formData(form, event.submitter);
    const finish = beginSubmission(form);
    try {
      const result = await postJSON(form.action, values);
      navigateAfterSubmit(form.dataset.next, result);
    } catch (error) {
      showError(errorFor(form), error.message);
      finish();
    }
  });
}

const quoteForm = document.querySelector("[data-quote-form]");
if (quoteForm) configureBooking(quoteForm);

const demoPanel = document.querySelector("[data-demo-password]");
if (demoPanel) {
  const login = document.querySelector('[data-testid="login-form"]');
  for (const button of demoPanel.querySelectorAll("[data-demo-email]")) {
    button.addEventListener("click", () => {
      login.elements.email.value = button.dataset.demoEmail;
      login.elements.password.value = demoPanel.dataset.demoPassword;
      showError(errorFor(login), "");
      login.querySelector('button[type="submit"]').focus();
    });
  }
}
