/* Progressive enhancement: search + year/type filters for publications,
   plus an independent search over the PDF repository.
   Everything is static HTML, so the page works without JavaScript. */
(function () {
  'use strict';

  /* One script serves both language editions; the <html lang> decides wording. */
  var zh = (document.documentElement.lang || '').toLowerCase().indexOf('zh') === 0;
  var TYPE_LABELS = {
    journal: '期刊', conference: '会议', magazine: '杂志',
    patent: '专利', editorial: '社论', book: '专著'
  };

  /* ---------- publications ---------- */
  var q = document.getElementById('q');
  var yearChips = document.getElementById('year-chips');
  var typeChips = document.getElementById('type-chips');
  var countEl = document.getElementById('result-count');
  var emptyEl = document.getElementById('empty-state');

  if (q && yearChips && typeChips) {
    var papers = Array.prototype.slice.call(document.querySelectorAll('.paper'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.year-group'));
    var state = { year: 'all', type: 'all', text: '' };

    function apply() {
      var shown = 0;
      papers.forEach(function (el) {
        var okYear = state.year === 'all' || el.dataset.year === state.year;
        var okType = state.type === 'all' || el.dataset.type === state.type;
        var okText = !state.text || (el.dataset.text || '').indexOf(state.text) !== -1;
        var visible = okYear && okType && okText;
        el.classList.toggle('is-hidden', !visible);
        if (visible) shown++;
      });

      groups.forEach(function (g) {
        g.classList.toggle('is-hidden', !g.querySelector('.paper:not(.is-hidden)'));
      });

      // hide a "Conference Papers" sub-heading when its block has no visible papers
      document.querySelectorAll('.type-subhead').forEach(function (h) {
        var ol = h.nextElementSibling;
        var hasVisible = ol && ol.classList.contains('papers') &&
          ol.querySelector('.paper:not(.is-hidden)');
        h.classList.toggle('is-hidden', !hasVisible);
      });

      var parts = [];
      if (state.year !== 'all') parts.push(state.year);
      if (state.type !== 'all') parts.push(zh ? (TYPE_LABELS[state.type] || state.type) : state.type);
      if (state.text) parts.push('"' + state.text + '"');
      var tail = parts.length ? ' · ' + parts.join(' · ') : '';
      countEl.textContent = zh
        ? '显示 ' + shown + ' / ' + papers.length + ' 条论文' + tail + '。'
        : 'Showing ' + shown + ' of ' + papers.length + ' publications' + tail + '.';
      emptyEl.hidden = shown !== 0;
    }

    q.addEventListener('input', function () {
      state.text = q.value.trim().toLowerCase();
      apply();
    });

    function bindChips(container, key) {
      container.addEventListener('click', function (e) {
        var btn = e.target.closest('.chip');
        if (!btn) return;
        container.querySelectorAll('.chip').forEach(function (c) {
          c.classList.remove('is-active');
        });
        btn.classList.add('is-active');
        state[key] = btn.dataset.year !== undefined ? btn.dataset.year : btn.dataset.type;
        apply();
      });
    }

    bindChips(yearChips, 'year');
    bindChips(typeChips, 'type');
    apply();
  }

  /* ---------- PDF repository ---------- */
  var libQ = document.getElementById('lib-q');
  var libCount = document.getElementById('lib-count');
  var libEmpty = document.getElementById('library-empty');

  if (libQ) {
    var items = Array.prototype.slice.call(document.querySelectorAll('.lib-item'));
    var lists = Array.prototype.slice.call(document.querySelectorAll('.pdf-library .additional-list'));
    var heads = Array.prototype.slice.call(document.querySelectorAll('.pdf-library .lib-year'));
    var pdfLibrary = document.getElementById('pdf-library');
    var repoHint = document.getElementById('repo-hint');

    function applyLib() {
      var text = libQ.value.trim().toLowerCase();
      var collapsed = text.length === 0;
      if (pdfLibrary) pdfLibrary.classList.toggle('collapsed', collapsed);
      if (repoHint) repoHint.hidden = !collapsed;
      if (collapsed) {
        items.forEach(function (el) { el.classList.add('is-hidden'); });
        lists.forEach(function (ul) { ul.classList.add('is-hidden'); });
        heads.forEach(function (h) { h.classList.add('is-hidden'); });
        if (libCount) libCount.textContent = '';
        if (libEmpty) libEmpty.hidden = true;
        return;
      }
      var shown = 0;
      items.forEach(function (el) {
        var ok = (el.dataset.text || '').indexOf(text) !== -1;
        el.classList.toggle('is-hidden', !ok);
        if (ok) shown++;
      });
      lists.forEach(function (ul) {
        ul.classList.toggle('is-hidden', !ul.querySelector('.lib-item:not(.is-hidden)'));
      });
      heads.forEach(function (h) {
        var ul = h.nextElementSibling;
        h.classList.toggle('is-hidden', !ul || ul.classList.contains('is-hidden'));
      });
      if (libCount) {
        libCount.textContent = zh
          ? '显示 ' + shown + ' / ' + items.length + ' 篇 PDF' + (text ? '，匹配「' + text + '」' : '') + '。'
          : 'Showing ' + shown + ' of ' + items.length + ' PDFs' +
            (text ? ' matching "' + text + '"' : '') + '.';
      }
      if (libEmpty) libEmpty.hidden = shown !== 0;
    }

    libQ.addEventListener('input', applyLib);
    applyLib();
  }
})();
