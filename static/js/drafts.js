/* Автосохранение черновиков для форм создания/редактирования дел и комментариев.
   Данные сохраняются только в браузере. Подтверждение успешного сохранения
   приходит в параметре draft_saved после серверного редиректа (HTTP 303). */
(() => {
  "use strict";

  const prefix = `promise-diary:drafts:v1:${window.location.pathname}:`;
  const pendingKey = "promise-diary:drafts:v1:pending";

  const getDraftKey = (form) => prefix + form.dataset.draftKey;
  const fields = (form) => Array.from(form.querySelectorAll("input[name], textarea[name], select[name]"))
    .filter((field) => field.type !== "hidden" && field.type !== "submit" && field.type !== "button");

  const getStored = (key) => {
    try {
      const raw = window.localStorage.getItem(key);
      return raw === null ? null : JSON.parse(raw);
    } catch (_error) {
      return null;
    }
  };

  function processSuccessfulSave() {
    const url = new URL(window.location.href);
    const token = url.searchParams.get("draft_saved");
    if (!token) return;

    try {
      const pending = JSON.parse(window.sessionStorage.getItem(pendingKey) || "null");
      if (pending && pending.token === token && typeof pending.key === "string") {
        window.localStorage.removeItem(pending.key);
        window.sessionStorage.removeItem(pendingKey);
      }
    } catch (_error) {
      // Если storage недоступен, не трогаем остальные черновики.
    }

    url.searchParams.delete("draft_saved");
    window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
  }

  function initForm(form) {
    const key = getDraftKey(form);
    const editableFields = fields(form);
    const note = document.createElement("small");
    note.className = "d-block text-muted mt-2";
    note.setAttribute("aria-live", "polite");

    const discardButton = document.createElement("button");
    discardButton.type = "button";
    discardButton.className = "btn btn-sm btn-link p-0 mt-1";
    discardButton.textContent = "Удалить черновик";
    discardButton.hidden = true;
    form.append(note, discardButton);

    const draft = getStored(key);
    if (draft && draft.values && typeof draft.values === "object") {
      for (const field of editableFields) {
        if (Object.prototype.hasOwnProperty.call(draft.values, field.name)) {
          field.value = String(draft.values[field.name]);
        }
      }
      const container = form.closest("details");
      if (container) container.open = true;
      discardButton.hidden = false;
      note.textContent = "Черновик восстановлен из этого браузера.";
    }

    function saveDraft() {
      const values = {};
      for (const field of editableFields) values[field.name] = field.value;
      try {
        window.localStorage.setItem(key, JSON.stringify({ values, savedAt: Date.now() }));
        discardButton.hidden = false;
        note.textContent = "Черновик сохранён в этом браузере.";
        return true;
      } catch (_error) {
        note.textContent = "Не удалось сохранить черновик: хранилище браузера недоступно или заполнено.";
        return false;
      }
    }

    form.addEventListener("input", saveDraft);
    form.addEventListener("change", saveDraft);

    discardButton.addEventListener("click", () => {
      try {
        window.localStorage.removeItem(key);
        form.reset();
        discardButton.hidden = true;
        note.textContent = "Черновик удалён. Восстановлены исходные значения формы.";
      } catch (_error) {
        note.textContent = "Не удалось удалить черновик из хранилища браузера.";
      }
    });

    form.addEventListener("submit", () => {
      // Черновик остаётся в localStorage до подтверждения успеха от сервера.
      if (!saveDraft()) return;
      const token = (window.crypto && typeof window.crypto.randomUUID === "function")
        ? window.crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

      let hiddenToken = form.querySelector('input[name="_draft"]');
      if (!hiddenToken) {
        hiddenToken = document.createElement("input");
        hiddenToken.type = "hidden";
        hiddenToken.name = "_draft";
        form.appendChild(hiddenToken);
      }
      hiddenToken.value = token;
      try {
        window.sessionStorage.setItem(pendingKey, JSON.stringify({ key, token }));
      } catch (_error) {
        // Без sessionStorage не очищаем автоматически: сохраняем черновик.
      }
    });
  }

  processSuccessfulSave();
  document.querySelectorAll("form[data-draft-key]").forEach(initForm);
})();
