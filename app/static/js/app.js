let javascriptRequestSequence = 0;

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
  syncResponsiveTextareas();
  syncBase64Tools();
  syncJavascriptOptions();
  syncJavascriptTools();
  syncPercentageCalculators();
  syncPasswordTools();
  syncNavToggle();
}

function syncNavToggle() {
  const $sidebar = $(".sidebar");
  const $navToggle = $("[data-nav-toggle]");
  if ($sidebar.length && $navToggle.length) {
    $navToggle.attr("aria-expanded", $sidebar.hasClass("nav-open") ? "true" : "false");
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
      throw new Error("Custom delimiter cannot be empty.");
    }
    return custom;
  }
  if (!(name in delimiters)) {
    throw new Error("Unsupported delimiter.");
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
  throw new Error("Unsupported quote option.");
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
    throw new Error("Interval must be zero or greater.");
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
      throw new Error("Interval must be zero or greater.");
    }
    const interval = intervalRaw ? Number.parseInt(intervalRaw, 10) : 0;
    if (!Number.isFinite(interval)) {
      throw new Error("Interval must be zero or greater.");
    }
    $result.val(joinDelimiterItems(items, delimiterValue(outputDelimiter, outputCustom), interval));
    $error.prop("hidden", true).text("");
  } catch (error) {
    $result.val("");
    $error.text(error.message || "Conversion failed.").prop("hidden", false);
  }
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
    $error.prop("hidden", true).text("");
  } catch (decodeError) {
    $result.val("");
    $error.text(decodeError.message === "invalid-base64" ? $form.data("invalidBase64") : $form.data("invalidUtf8")).prop("hidden", false);
  }
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
    $error.prop("hidden", true).text("");
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
    $error.text(payload.error || "").prop("hidden", !payload.error);
  }).fail((xhr, status, error) => {
    if ($form.data("requestId") === requestId) {
      $error.text(error || status || "Request failed.").prop("hidden", false);
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
  if ($form.find('input[name="uppercase"]').prop("checked")) {
    groups.push("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
  }
  if ($form.find('input[name="lowercase"]').prop("checked")) {
    groups.push("abcdefghijklmnopqrstuvwxyz");
  }
  if ($form.find('input[name="digits"]').prop("checked")) {
    groups.push("0123456789");
  }
  if ($form.find('input[name="symbols"]').prop("checked")) {
    groups.push("!@#$%^&*");
  }
  if (!groups.length) {
    $error.text($form.data("passwordNoTypes")).prop("hidden", false);
    return;
  }
  $error.prop("hidden", true).text("");
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
  $form.find("[data-password-result]").val(passwords.join("\n"));
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
      alert(responseToText(data) || `Request failed with status ${response.status}.`);
      return;
    }
    if (!contentType.includes("text/html")) {
      alert(responseToText(data) || `Request failed with status ${response.status}.`);
      return;
    }
    replaceShell(responseToText(data), response.url || url, addHistory);
  }).catch((error) => {
    alert(error.message || "Request failed.");
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
    }
    if ($target.is('select[name="input_delimiter"], select[name="output_delimiter"]')) {
      syncDelimiterOptions();
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
  });

  $(document).on("input", function (event) {
    const $target = $(event.target);
    const $row = $target.closest("[data-percentage-row]");
    const $base64Form = $target.closest("[data-base64-tool]");
    const $javascriptForm = $target.closest("[data-javascript-tool]");
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
