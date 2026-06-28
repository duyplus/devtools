let javascriptRequestSequence = 0;
let qrSubmitTimer = 0;

const DEVTOOLS_MESSAGE_KEYS = {
  conversionFailed: "js.conversion_failed",
  copyImageFailed: "js.copy_image_failed",
  copyImageUnsupported: "js.copy_image_unsupported",
  copyTextDone: "js.copy_text_done",
  copyTextFailed: "js.copy_text_failed",
  fileReadDone: "js.file_read_done",
  customDelimiterEmpty: "js.custom_delimiter_empty",
  fileReadFailed: "js.file_read_failed",
  frameTextDefault: "qr.placeholder.frame_text",
  intervalInvalid: "js.interval_invalid",
  requestFailed: "js.request_failed",
  requestFailedStatus: "js.request_failed_status",
  unsupportedDelimiter: "js.unsupported_delimiter",
  unsupportedQuote: "js.unsupported_quote",
};

function loadDevtoolsMessages() {
  const raw = $("#devtools-i18n").text() || "{}";
  const source = JSON.parse(raw);
  return Object.fromEntries(Object.entries(DEVTOOLS_MESSAGE_KEYS).map(([name, key]) => [name, source[key] || key]));
}

function i18n(key, params) {
  window.devtoolsMessages ||= loadDevtoolsMessages();
  const template = window.devtoolsMessages[key] || key;
  return String(template).replace(/\{(\w+)\}/g, (_, name) => params?.[name] ?? "");
}

function toast(message, type) {
  if (!message) {
    return;
  }
  const $stack = $(".toast-stack").length ? $(".toast-stack") : $("<div>", { class: "toast-stack", role: "status", "aria-live": "polite" }).appendTo("body");
  const toastClass = `toast-${type || "success"}`;
  const duplicate = $stack.find(`.${toastClass}`).toArray().some((item) => $(item).text() === message);
  if (duplicate) {
    return;
  }
  const $toast = $("<div>", { class: `toast ${toastClass}` }).text(message).appendTo($stack);
  window.setTimeout(() => $toast.addClass("is-visible"), 10);
  window.setTimeout(() => {
    $toast.removeClass("is-visible");
    window.setTimeout(() => $toast.remove(), 220);
  }, 3200);
}

function notifySuccess(message) {
  toast(message, "success");
}

function notifyError(message) {
  toast(message, "error");
}

window.notifySuccess = notifySuccess;
window.notifyError = notifyError;

function currentTheme() {
  return $("html").attr("data-theme") || "light";
}

function setTheme(theme) {
  $("html").attr("data-theme", theme);
  localStorage.setItem("theme", theme);
  $("[data-theme-toggle]").each(function () {
    const $button = $(this);
    const label = theme === "dark" ? $button.data("labelDark") : $button.data("labelLight");
    $button.find("[data-theme-label]").text(label);
  });
}

function refreshUi() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
  setTheme(currentTheme());
  syncIconOptions();
  syncFileInputs();
  syncDelimiterOptions();
  syncLineNumbers();
  syncResponsiveTextareas();
  syncBase64Tools();
  syncJavascriptOptions();
  syncJavascriptTools();
  syncPercentageCalculators();
  syncPasswordTools();
  syncQrTools();
  syncTextDiffTools();
  syncNavToggle();
  syncServerToasts();
}

function syncNavToggle() {
  const $sidebar = $(".sidebar");
  const $navToggle = $("[data-nav-toggle]");
  if ($sidebar.length && $navToggle.length) {
    $navToggle.attr("aria-expanded", $sidebar.hasClass("nav-open") ? "true" : "false");
  }
}

function syncServerToasts(root) {
  $(root || document).find("[data-toast-error], [data-toast-success]").each(function () {
    const $node = $(this);
    const message = $node.text().trim();
    if (!message || $node.data("toastShown")) {
      return;
    }
    $node.data("toastShown", true);
    ($node.is("[data-toast-error]") ? notifyError : notifySuccess)(message);
  });
}

function setToolError($node, message) {
  const text = String(message || "");
  $node.text(text).prop("hidden", true);
  if (!text) {
    $node.removeData("lastToast");
    return;
  }
  if ($node.data("lastToast") !== text) {
    $node.data("lastToast", text);
    $node.data("toastShown", true);
    notifyError(text);
  }
}

function syncIconOptions() {
  const $packOptions = $("#pack-options");
  const $icoSizes = $("#ico-sizes");
  const $icoBitdepth = $("#ico-bitdepth");
  if (!$packOptions.length || !$icoSizes.length || !$icoBitdepth.length) {
    return;
  }
  const mode = $('input[name="mode"]:checked').val() || "pack";
  const bitDepth = $('input[name="bit_depth"]:checked').val() || "32";
  const isIco = mode === "ico";
  const $size256 = $("input[data-size-256]");
  $packOptions.prop("hidden", isIco);
  $icoSizes.prop("hidden", !isIco);
  $icoBitdepth.prop("hidden", !isIco);
  if ($size256.length) {
    $size256.prop("disabled", bitDepth === "8");
    if ($size256.prop("disabled")) {
      $size256.prop("checked", false);
    }
  }
}

function syncFileInputs(root) {
  $(root || document).find("[data-file-input]").each(function () {
    updateFileLabel(this);
  });
}

function updateFileLabel(input) {
  const $input = $(input);
  const $label = $input.closest("[data-file-dropzone]").find("[data-file-label]");
  if (!$label.length) {
    return;
  }
  const names = $.map(input.files || [], (file) => file.name);
  $label.text(names.length ? names.join(", ") : $label.data("defaultText"));
}

function syncDelimiterOptions() {
  $("[data-custom-for]").each(function () {
    const $input = $(this);
    const $select = $(`[name="${$input.data("customFor")}"]`);
    $input.prop("disabled", $select.val() !== "custom");
  });
}

function lineCount(value) {
  return value ? String(value).split(/\r\n|\r|\n/).length : 0;
}

function renderLineNumbersFor($textarea) {
  const key = $textarea.data("lineNumbersTarget");
  const $gutter = $(`[data-line-numbers-for="${key}"]`);
  const count = Math.max(1, lineCount($textarea.val()));
  $gutter.html(`<span class="line-number-list">${Array.from({ length: count }, (_, index) => `<span>${index + 1}</span>`).join("")}</span>`);
  if (!$textarea.data("lineScrollBound")) {
    $textarea.on("scroll", function () {
      syncLineNumberScroll($(this));
    });
    $textarea.data("lineScrollBound", true);
  }
  syncLineNumberScroll($textarea);
}

function syncLineNumbers(root) {
  $(root || document).find("[data-line-numbers-target]").each(function () {
    renderLineNumbersFor($(this));
  });
}

function syncLineNumberScroll($textarea) {
  const key = $textarea.data("lineNumbersTarget");
  $(`[data-line-numbers-for="${key}"] .line-number-list`).css("transform", `translateY(-${$textarea.scrollTop()}px)`);
}

function delimiterValue(name, custom) {
  const delimiters = {
    newline: "\n",
    comma: ",",
    semicolon: ";",
    pipe: "|",
    spaces: " ",
  };
  if (name === "custom") {
    if (custom === "") {
      throw new Error(i18n("customDelimiterEmpty"));
    }
    return custom;
  }
  if (!(name in delimiters)) {
    throw new Error(i18n("unsupportedDelimiter"));
  }
  return delimiters[name];
}

function splitDelimiterText(text, delimiterName, custom) {
  const delimiter = delimiterValue(delimiterName, custom);
  if (delimiterName === "newline") {
    if (text === "") {
      return [];
    }
    return text.split(/\r?\n/);
  }
  if (delimiterName === "spaces") {
    return text.split(/\s+/);
  }
  return text.split(delimiter);
}

function delimiterQuote(name) {
  if (name === "none") {
    return "";
  }
  if (name === "single") {
    return "'";
  }
  if (name === "double") {
    return "\"";
  }
  throw new Error(i18n("unsupportedQuote"));
}

function dedupeItems(items) {
  const seen = new Set();
  return items.filter((item) => {
    if (seen.has(item)) {
      return false;
    }
    seen.add(item);
    return true;
  });
}

function joinDelimiterItems(items, delimiter, interval) {
  if (interval < 0) {
    throw new Error(i18n("intervalInvalid"));
  }
  if (interval === 0) {
    return items.join(delimiter);
  }
  const chunks = [];
  for (let index = 0; index < items.length; index += interval) {
    chunks.push(items.slice(index, index + interval).join(delimiter));
  }
  return chunks.join("\n");
}

function calculateDelimiterTool(form, direction) {
  const $form = $(form);
  const field = (name) => $form.find(`[name="${name}"]`).val() || "";
  const checked = (name) => $form.find(`[name="${name}"]`).prop("checked");
  const $result = $form.find("[data-delimiter-result]");
  const $error = $("[data-delimiter-error]");
  let inputDelimiter = field("input_delimiter");
  let outputDelimiter = field("output_delimiter");
  let inputCustom = field("input_custom");
  let outputCustom = field("output_custom");
  if (direction === "reverse") {
    [inputDelimiter, outputDelimiter] = [outputDelimiter, inputDelimiter];
    [inputCustom, outputCustom] = [outputCustom, inputCustom];
  }
  try {
    let items = splitDelimiterText($form.find("[data-delimiter-source]").val(), inputDelimiter, inputCustom);
    if (checked("trim")) {
      items = items.map((item) => item.trim());
    }
    if (checked("remove_blank")) {
      items = items.filter((item) => item !== "");
    }
    if (checked("dedupe")) {
      items = dedupeItems(items);
    }
    const quote = delimiterQuote(field("quote") || "none");
    items = items.map((item) => `${field("prefix")}${quote}${item}${quote}${field("suffix")}`);
    const intervalRaw = field("interval").trim();
    if (intervalRaw && !/^-?\d+$/.test(intervalRaw)) {
      throw new Error(i18n("intervalInvalid"));
    }
    const interval = intervalRaw ? Number.parseInt(intervalRaw, 10) : 0;
    if (!Number.isFinite(interval)) {
      throw new Error(i18n("intervalInvalid"));
    }
    $result.val(joinDelimiterItems(items, delimiterValue(outputDelimiter, outputCustom), interval));
    setToolError($error, "");
  } catch (error) {
    $result.val("");
    setToolError($error, error.message || i18n("conversionFailed"));
  }
  syncLineNumbers(form);
}

function syncResponsiveTextareas() {
  const mobile = window.matchMedia("(max-width: 860px)").matches;
  $("[data-desktop-rows][data-mobile-rows]").each(function () {
    const $textarea = $(this);
    $textarea.prop("rows", mobile ? $textarea.data("mobileRows") : $textarea.data("desktopRows"));
  });
}

function numberFromInput(input) {
  const raw = String($(input).val() || "").trim().replace(",", ".");
  if (!raw) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function formatPercentResult(value) {
  if (!Number.isFinite(value)) {
    return "";
  }
  return value.toFixed(10).replace(/\.?0+$/, "");
}

function calculatePercentageRow(row) {
  const $row = $(row);
  const field = (name) => $row.find(`[data-percent-field="${name}"]`).get(0);
  const $result = $row.find("[data-percent-result]");
  let value = null;
  if (!$result.length) {
    return;
  }
  if ($row.data("percentageRow") === "of") {
    const percent = numberFromInput(field("percent"));
    const base = numberFromInput(field("value"));
    value = percent === null || base === null ? null : (base * percent) / 100;
  }
  if ($row.data("percentageRow") === "ratio") {
    const part = numberFromInput(field("value"));
    const base = numberFromInput(field("base"));
    value = part === null || base === null || base === 0 ? null : (part / base) * 100;
  }
  if ($row.data("percentageRow") === "change") {
    const percent = numberFromInput(field("percent"));
    const base = numberFromInput(field("value"));
    const direction = $(field("direction")).val() || "increase";
    const factor = direction === "decrease" ? 1 - percent / 100 : 1 + percent / 100;
    value = percent === null || base === null ? null : base * factor;
  }
  if ($row.data("percentageRow") === "total") {
    const part = numberFromInput(field("value"));
    const percent = numberFromInput(field("percent"));
    value = part === null || percent === null || percent === 0 ? null : (part * 100) / percent;
  }
  $result.val(value === null ? "" : formatPercentResult(value));
}

function syncPercentageCalculators(root) {
  $(root || document).find("[data-percentage-row]").each(function () {
    calculatePercentageRow(this);
  });
}

function bytesToBinary(bytes) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  return binary;
}

function binaryToBytes(binary) {
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function encodeBase64Text(text) {
  return btoa(bytesToBinary(new TextEncoder().encode(text)));
}

function decodeBase64Text(text) {
  if (text !== "" && !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(text)) {
    throw new Error("invalid-base64");
  }
  return new TextDecoder("utf-8", { fatal: true }).decode(binaryToBytes(atob(text)));
}

function calculateBase64Tool(form) {
  const $form = $(form);
  const $source = $form.find("[data-base64-source]");
  const $result = $form.find("[data-base64-result]");
  const $error = $("[data-base64-error]");
  const mode = $form.find('input[name="mode"]:checked').val() || "encode";
  if (!$source.length || !$result.length) {
    return;
  }
  try {
    $result.val(mode === "decode" ? decodeBase64Text($source.val()) : encodeBase64Text($source.val()));
    setToolError($error, "");
  } catch (decodeError) {
    $result.val("");
    setToolError($error, decodeError.message === "invalid-base64" ? $form.data("invalidBase64") : $form.data("invalidUtf8"));
  }
  syncLineNumbers(form);
}

function syncBase64Tools(root) {
  $(root || document).find("[data-base64-tool]").each(function () {
    calculateBase64Tool(this);
  });
}

function syncJavascriptOptions() {
  const $options = $("[data-javascript-options]");
  const mode = $('input[name="mode"]:checked').val() || "obfuscate";
  $options.prop("hidden", mode === "deobfuscate");
}

function calculateJavascriptTool(form) {
  const $form = $(form);
  const $source = $form.find("[data-javascript-source]");
  const $result = $form.find("[data-javascript-result]");
  const $error = $("[data-javascript-error]");
  const liveUrl = $form.data("liveUrl");
  if (!$source.length || !$result.length || !liveUrl) {
    return;
  }
  if (!$source.val()) {
    $result.val("");
    setToolError($error, "");
    syncLineNumbers(form);
    return;
  }
  javascriptRequestSequence += 1;
  const requestId = String(javascriptRequestSequence);
  $form.data("requestId", requestId);
  $.ajax({
    url: liveUrl,
    method: "POST",
    data: new FormData(form),
    processData: false,
    contentType: false,
    headers: { "X-Requested-With": "fetch" },
  }).done((payload) => {
    if ($form.data("requestId") !== requestId) {
      return;
    }
    $result.val(payload.result || "");
    setToolError($error, payload.error || "");
    syncLineNumbers(form);
  }).fail((xhr, status, error) => {
    if ($form.data("requestId") === requestId) {
      setToolError($error, error || status || i18n("requestFailed"));
    }
  });
}

function queueJavascriptTool(form) {
  const timer = $(form).data("javascriptTimer");
  clearTimeout(timer);
  $(form).data("javascriptTimer", setTimeout(() => calculateJavascriptTool(form), 180));
}

function syncJavascriptTools(root) {
  $(root || document).find("[data-javascript-tool]").each(function () {
    if ($(this).find("[data-javascript-source]").val()) {
      queueJavascriptTool(this);
    }
  });
}

function syncPasswordTool(form, source) {
  const $form = $(form);
  const $range = $form.find("[data-password-length-range]");
  const $input = $form.find("[data-password-length-input]");
  const $label = $form.find("[data-password-length]");
  const $source = $(source);
  const value = String(
    $source.is("[data-password-length-range], [data-password-length-input]")
      ? $source.val()
      : $input.val() || $range.val() || 16
  );
  $range.val(value);
  $input.val(value);
  $label.text(value);
}

function syncPasswordTools(root) {
  $(root || document).find("[data-password-tool]").each(function () {
    syncPasswordTool(this);
  });
}

function syncQrTools(root) {
  $(root || document).find("[data-qr-tool]").each(function () {
    const $form = $(this);
    const type = $form.find('input[name="type"]:checked').val() || "url";
    $form.find("[data-qr-fields]").each(function () {
      const active = $(this).data("qrFields") === type;
      $(this).prop("hidden", !active).toggleClass("is-active", active);
    });
    syncQrStyleControls($form);
  });
}

function syncQrStyleControls($form) {
  $form.find("[data-qr-range]").each(function () {
    $form.find(`[data-qr-range-output="${$(this).data("qrRange")}"]`).text($(this).val());
  });
  $form.find("[data-qr-color-value]").each(function () {
    const key = $(this).data("qrColorValue");
    const color = normalizeQrColor($(this).val());
    $(this).val(color);
    $form.find(`[data-qr-color-picker="${key}"]`).val(color.slice(0, 7));
  });
  const frameEnabled = $form.find("[data-qr-frame-toggle]").prop("checked");
  $form.find("[data-qr-frame-text] input").prop("disabled", !frameEnabled);
}

function normalizeQrColor(value) {
  const raw = String(value || "").trim();
  if (/^#[0-9a-f]{6}$/i.test(raw)) {
    return `${raw.toUpperCase()}FF`;
  }
  if (/^#[0-9a-f]{8}$/i.test(raw)) {
    return raw.toUpperCase();
  }
  return "#000000FF";
}

function queueQrSubmit(form) {
  window.clearTimeout(qrSubmitTimer);
  qrSubmitTimer = window.setTimeout(() => {
    if (document.contains(form)) {
      submitQrTool(form);
    }
  }, 500);
}

function submitQrTool(form) {
  const $form = $(form);
  const url = new URL(form.action || window.location.href, window.location.href);
  $.ajax({
    url: url.toString(),
    method: "POST",
    data: formData(form),
    processData: false,
    contentType: false,
    headers: { "X-Requested-With": "fetch" },
  }).done((html) => {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const $nextPreview = $(doc).find(".qr-preview");
    const $nextError = $(doc).find("[data-qr-error]");
    const hadError = Boolean($form.data("qrHadError"));
    if ($nextPreview.length) {
      $form.find(".qr-preview").replaceWith($nextPreview);
    }
    if ($nextError.length) {
      const message = $nextError.text().trim();
      const hasError = Boolean(message);
      const $currentError = $("[data-qr-error]");
      $currentError.text(message).prop("hidden", true);
      if (hasError) {
        $form.data("qrHadError", true);
        setToolError($currentError, message);
      } else if (hadError && $nextPreview.find("[data-copy-image]").length) {
        $form.data("qrHadError", false);
        notifySuccess($form.data("qrSuccess"));
      }
    }
    refreshUi();
  }).fail((xhr, status, error) => {
    setToolError($("[data-qr-error]"), error || status || i18n("requestFailed"));
  });
}

function syncTextDiffTools(root) {
  $(root || document).find("[data-text-diff-tool]").each(function () {
    bindTextDiffControls(this);
  });
}

function bindTextDiffControls(form) {
  const $form = $(form);
  $form.find("[data-copy-text-area]").off("click.textdiff").on("click.textdiff", function (event) {
    event.preventDefault();
    event.stopPropagation();
    copyText(form.elements?.[$(this).data("copyTextArea")]?.value || "");
  });
  $form.find("[data-textdiff-swap]").off("click.textdiff").on("click.textdiff", function (event) {
    event.preventDefault();
    event.stopPropagation();
    const left = form.elements?.left_text;
    const right = form.elements?.right_text;
    if (!left || !right) {
      return;
    }
    const leftValue = left.value;
    left.value = right.value;
    right.value = leftValue;
    syncLineNumbers(form);
  });
  $form.find("[data-text-file-target]").off("change.textdiff").on("change.textdiff", function (event) {
    event.stopPropagation();
    readTextDiffFile(this);
  });
}

function readTextDiffFile(input) {
  const file = input.files?.[0];
  const targetName = $(input).data("textFileTarget");
  const form = $(input).closest("[data-text-diff-tool]").get(0);
  const target = form?.elements?.[targetName];
  if (!file || !target) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    $(target).val(String(reader.result || ""));
    syncLineNumbers(form);
    notifySuccess(i18n("fileReadDone"));
  };
  reader.onerror = () => notifyError(i18n("fileReadFailed"));
  reader.readAsText(file);
}

function copyText(value) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(value)
      .then(() => notifySuccess(i18n("copyTextDone")))
      .catch((error) => notifyError(error.message || i18n("copyTextFailed")));
  }
  try {
    const textarea = $("<textarea>").val(value).appendTo(document.body).get(0);
    textarea.select();
    document.execCommand("copy");
    $(textarea).remove();
    notifySuccess(i18n("copyTextDone"));
  } catch {
    notifyError(i18n("copyTextFailed"));
  }
}

function copyQrImage(button) {
  const image = $(button).closest("[data-qr-tool]").find("[data-copy-image]").get(0);
  if (!image?.src || !navigator.clipboard || !window.ClipboardItem) {
    notifyError(i18n("copyImageUnsupported"));
    return;
  }
  fetch(image.src)
    .then((response) => response.blob())
    .then((blob) => navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]))
    .then(() => {
      const message = $(button).data("copySuccess");
      if (message) {
        notifySuccess(message);
      }
    })
    .catch((error) => notifyError(error.message || i18n("copyImageFailed")));
}

function secureRandomIndex(max) {
  const limit = Math.floor(0x100000000 / max) * max;
  const buffer = new Uint32Array(1);
  do {
    crypto.getRandomValues(buffer);
  } while (buffer[0] >= limit);
  return buffer[0] % max;
}

function randomFrom(chars) {
  return chars[secureRandomIndex(chars.length)];
}

function generatePasswordTool(form) {
  const $form = $(form);
  const $error = $("[data-password-error]");
  const length = Math.min(128, Math.max(4, Number($form.find("[data-password-length-input]").val()) || 16));
  const count = Math.min(50, Math.max(1, Number($form.find('input[name="count"]').val()) || 1));
  const groups = [];
  if ($form.find('input[name="lowercase"]').prop("checked")) {
    groups.push("abcdefghijklmnopqrstuvwxyz");
  }
  if ($form.find('input[name="uppercase"]').prop("checked")) {
    groups.push("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
  }
  if ($form.find('input[name="digits"]').prop("checked")) {
    groups.push("0123456789");
  }
  if ($form.find('input[name="symbols"]').prop("checked")) {
    groups.push("!@#$%^&*");
  }
  if (!groups.length) {
    setToolError($error, $form.data("passwordNoTypes"));
    return;
  }
  setToolError($error, "");
  const pool = groups.join("");
  const passwords = [];
  for (let item = 0; item < count; item += 1) {
    const chars = groups.map(randomFrom);
    while (chars.length < length) {
      chars.push(randomFrom(pool));
    }
    for (let index = chars.length - 1; index > 0; index -= 1) {
      const swap = secureRandomIndex(index + 1);
      [chars[index], chars[swap]] = [chars[swap], chars[index]];
    }
    passwords.push(chars.join(""));
  }
  const $result = $form.find("[data-password-result]");
  $result.val(passwords.join("\n"));
  renderLineNumbersFor($result);
  notifySuccess($form.data("passwordSuccess"));
}

function parseFilename(disposition) {
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    return decodeURIComponent(utf8Match[1].replaceAll("\"", ""));
  }
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : "download";
}

function responseHeader(response, name) {
  if (typeof response.getResponseHeader === "function") {
    return response.getResponseHeader(name);
  }
  return response.headers?.get(name) || "";
}

function responseToText(data) {
  if (typeof data === "string") {
    return data;
  }
  return new TextDecoder().decode(data);
}

function downloadBlob(response, data) {
  const disposition = responseHeader(response, "content-disposition");
  const contentType = responseHeader(response, "content-type") || "application/octet-stream";
  const blob = data instanceof Blob ? data : new Blob([data], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = $("<a>", {
    href: url,
    download: parseFilename(disposition),
  }).appendTo("body");
  link.get(0).click();
  link.remove();
  URL.revokeObjectURL(url);
}

function replaceShell(html, url, addHistory) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const $nextSidebar = $(doc).find(".sidebar");
  const $nextMain = $(doc).find(".main");
  if (!$nextSidebar.length || !$nextMain.length || !$(".sidebar").length || !$(".main").length) {
    window.location.href = url;
    return;
  }
  $(".sidebar").replaceWith($nextSidebar);
  $(".main").replaceWith($nextMain);
  document.title = $(doc).find("title").text();
  $("html").attr("lang", $(doc).find("html").attr("lang"));
  if (addHistory) {
    history.pushState({}, document.title, url);
  }
  refreshUi();
  $(window).scrollTop(0);
}

function requestPage(url, options) {
  const settings = options || {};
  const addHistory = settings.addHistory ?? true;
  $(".shell").addClass("is-loading");
  return fetch(url, {
    method: settings.method || "GET",
    body: settings.body || undefined,
    headers: { "X-Requested-With": "fetch" },
  }).then(async (response) => {
    const data = await response.arrayBuffer();
    const disposition = responseHeader(response, "content-disposition");
    const contentType = responseHeader(response, "content-type");
    if (disposition.toLowerCase().includes("attachment")) {
      downloadBlob(response, data);
      return;
    }
    if (!response.ok) {
      notifyError(responseToText(data) || i18n("requestFailedStatus", { status: response.status }));
      return;
    }
    if (!contentType.includes("text/html")) {
      notifyError(responseToText(data) || i18n("requestFailedStatus", { status: response.status }));
      return;
    }
    replaceShell(responseToText(data), response.url || url, addHistory);
  }).catch((error) => {
    notifyError(error.message || i18n("requestFailed"));
  }).finally(() => {
    $(".shell").removeClass("is-loading");
  });
}

function isInternalLink(link) {
  const url = new URL(link.href, window.location.href);
  if (url.origin !== window.location.origin) {
    return false;
  }
  if (link.target || $(link).attr("download") !== undefined) {
    return false;
  }
  if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) {
    return false;
  }
  return true;
}

function formData(form, submitter) {
  try {
    return new FormData(form, submitter);
  } catch {
    const data = new FormData(form);
    if (submitter?.name) {
      data.append(submitter.name, submitter.value);
    }
    return data;
  }
}

function bindEvents() {
  $(document).on("click", function (event) {
    const $target = $(event.target);
    const $themeButton = $target.closest("[data-theme-toggle]");
    if ($themeButton.length) {
      event.preventDefault();
      setTheme(currentTheme() === "dark" ? "light" : "dark");
      return;
    }
    const $navToggle = $target.closest("[data-nav-toggle]");
    if ($navToggle.length) {
      event.preventDefault();
      $(".sidebar").toggleClass("nav-open");
      syncNavToggle();
      return;
    }
    const $qrChoice = $target.closest("[data-qr-tool] .qr-type-grid .choice");
    if ($qrChoice.length) {
      event.preventDefault();
      const input = $qrChoice.find('input[name="type"]').get(0);
      if (input) {
        input.checked = true;
        const form = $qrChoice.closest("[data-qr-tool]").get(0);
        syncQrTools(form);
        queueQrSubmit(form);
      }
      return;
    }
    const $copyImageButton = $target.closest("[data-copy-image-button]");
    if ($copyImageButton.length) {
      event.preventDefault();
      copyQrImage($copyImageButton.get(0));
      return;
    }
    const $textFileCopy = $target.closest("[data-copy-text-area]");
    if ($textFileCopy.length) {
      event.preventDefault();
      const form = $textFileCopy.closest("[data-text-diff-tool]").get(0);
      copyText(form?.elements?.[$textFileCopy.data("copyTextArea")]?.value || "");
      return;
    }
    const $sidebar = $(".sidebar.nav-open");
    if ($sidebar.length && !$target.closest(".sidebar").length) {
      $sidebar.removeClass("nav-open");
      syncNavToggle();
    }
    const $textarea = $target.closest("textarea[readonly]");
    if ($textarea.length) {
      $textarea.get(0).select();
      return;
    }
    const link = $target.closest("a[href]").get(0);
    if (!link || event.isDefaultPrevented() || event.which !== 1 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    if (!isInternalLink(link)) {
      return;
    }
    event.preventDefault();
    if ($(link).closest(".nav").length) {
      $(".sidebar").removeClass("nav-open");
      syncNavToggle();
    }
    requestPage(link.href);
  });

  $(document).on("change", function (event) {
    const $target = $(event.target);
    if ($target.is('input[name="mode"], input[name="bit_depth"]')) {
      syncIconOptions();
      syncJavascriptOptions();
      if ($target.closest("[data-javascript-tool]").length) {
        queueJavascriptTool($target.closest("[data-javascript-tool]").get(0));
      }
    }
    if ($target.is("[data-file-input]")) {
      updateFileLabel(event.target);
      if ($target.closest("[data-qr-tool]").length) {
        queueQrSubmit($target.closest("[data-qr-tool]").get(0));
      }
    }
    if ($target.is("[data-text-file-target]")) {
      readTextDiffFile(event.target);
    }
    if ($target.is('select[name="input_delimiter"], select[name="output_delimiter"]')) {
      syncDelimiterOptions();
    }
    if ($target.is('input[name="type"]') && $target.closest("[data-qr-tool]").length) {
      const form = $target.closest("[data-qr-tool]").get(0);
      syncQrTools(form);
      queueQrSubmit(form);
    }
    if ($target.closest("[data-qr-style-controls]").length) {
      const $form = $target.closest("[data-qr-tool]");
      if ($target.is("[data-qr-color-picker]")) {
        const key = $target.data("qrColorPicker");
        $form.find(`[data-qr-color-value="${key}"]`).val(`${$target.val().toUpperCase()}FF`);
      }
      syncQrStyleControls($form);
      queueQrSubmit($form.get(0));
    }
    if ($target.closest("[data-percentage-row]").length) {
      syncPercentageCalculators();
    }
    if ($target.closest("[data-base64-tool]").length) {
      syncBase64Tools();
    }
    if ($target.closest("[data-javascript-tool]").length) {
      syncJavascriptOptions();
      queueJavascriptTool($target.closest("[data-javascript-tool]").get(0));
    }
    if ($target.closest("[data-password-tool]").length) {
      syncPasswordTool($target.closest("[data-password-tool]").get(0), event.target);
    }
    if ($target.closest("[data-qr-tool]").length) {
      queueQrSubmit($target.closest("[data-qr-tool]").get(0));
    }
  });

  $(document).on("input", function (event) {
    const $target = $(event.target);
    const $row = $target.closest("[data-percentage-row]");
    const $base64Form = $target.closest("[data-base64-tool]");
    const $javascriptForm = $target.closest("[data-javascript-tool]");
    if ($target.is("[data-line-numbers-target]")) {
      syncLineNumbers($target.closest("form").get(0) || document);
    }
    if ($row.length) {
      calculatePercentageRow($row.get(0));
    }
    if ($base64Form.length) {
      calculateBase64Tool($base64Form.get(0));
    }
    if ($javascriptForm.length) {
      queueJavascriptTool($javascriptForm.get(0));
    }
    if ($target.closest("[data-password-tool]").length) {
      syncPasswordTool($target.closest("[data-password-tool]").get(0), event.target);
    }
    if ($target.closest("[data-qr-style-controls]").length) {
      const $form = $target.closest("[data-qr-tool]");
      if ($target.is("[data-qr-range]")) {
        $form.find(`[data-qr-range-output="${$target.data("qrRange")}"]`).text($target.val());
      }
      queueQrSubmit($form.get(0));
    }
    if ($target.closest("[data-qr-tool]").length) {
      queueQrSubmit($target.closest("[data-qr-tool]").get(0));
    }
	  });

  document.addEventListener("scroll", function (event) {
    const $target = $(event.target);
    if ($target.is("[data-line-numbers-target]")) {
      syncLineNumberScroll($target);
    }
  }, true);

  $(document).on("click", "[data-qr-reset-defaults]", function () {
    const $form = $(this).closest("[data-qr-tool]");
    $form.find('[name="foreground"]').val("#000000FF");
    $form.find('[name="background"]').val("#FFFFFFFF");
    $form.find('[name="size"]').val("300");
    $form.find('[name="margin"]').val("2");
    $form.find('[name="error_correction"]').val("M");
    $form.find('[name="frame_text_enabled"]').prop("checked", false);
    $form.find('[name="frame_text"]').val(i18n("frameTextDefault"));
    $form.find('[name="logo"]').val("");
    syncQrStyleControls($form);
    queueQrSubmit($form.get(0));
  });

  $(document).on("dragover", function (event) {
    const $dropzone = $(event.target).closest("[data-file-dropzone]");
    if (!$dropzone.length) {
      return;
    }
    event.preventDefault();
    $dropzone.addClass("is-dragging");
  });

  $(document).on("dragleave", function (event) {
    const $dropzone = $(event.target).closest("[data-file-dropzone]");
    if (!$dropzone.length || $.contains($dropzone.get(0), event.relatedTarget)) {
      return;
    }
    $dropzone.removeClass("is-dragging");
  });

  $(document).on("drop", function (event) {
    const original = event.originalEvent;
    const $dropzone = $(event.target).closest("[data-file-dropzone]");
    if (!$dropzone.length) {
      return;
    }
    event.preventDefault();
    $dropzone.removeClass("is-dragging");
    const input = $dropzone.find("[data-file-input]").get(0);
    if (input && original.dataTransfer?.files?.length) {
      input.files = original.dataTransfer.files;
      updateFileLabel(input);
    }
  });

  $(document).on("submit", function (event) {
    const form = event.target;
    const $form = $(form);
    const method = String(form.method || "GET").toUpperCase();
    const url = new URL(form.action || window.location.href, window.location.href);
    if ($form.is("[data-qr-tool]")) {
      event.preventDefault();
      submitQrTool(form);
      return;
    }
    if ($form.is("[data-percentage-calculator]")) {
      event.preventDefault();
      return;
    }
    if ($form.is("[data-delimiter-tool]")) {
      event.preventDefault();
      calculateDelimiterTool(form, event.originalEvent?.submitter?.value || "forward");
      return;
    }
    if ($form.is("[data-base64-tool]")) {
      event.preventDefault();
      calculateBase64Tool(form);
      return;
    }
    if ($form.is("[data-javascript-tool]")) {
      event.preventDefault();
      calculateJavascriptTool(form);
      return;
    }
    if ($form.is("[data-password-tool]") && window.crypto?.getRandomValues) {
      event.preventDefault();
      generatePasswordTool(form);
      return;
    }
    if (form.target || url.origin !== window.location.origin || !["GET", "POST"].includes(method)) {
      return;
    }
    event.preventDefault();
    const data = formData(form, event.originalEvent?.submitter);
    if (method === "GET") {
      url.search = new URLSearchParams(data).toString();
      requestPage(url.toString());
      return;
    }
    requestPage(url.toString(), { method, body: data, addHistory: false });
  });

  $(window).on("popstate", function () {
    requestPage(window.location.href, { addHistory: false });
  });

  $(window).on("resize", syncResponsiveTextareas);
}

$(function () {
  setTheme(localStorage.getItem("theme") || $("html").attr("data-theme") || "light");
  refreshUi();
  bindEvents();
});
