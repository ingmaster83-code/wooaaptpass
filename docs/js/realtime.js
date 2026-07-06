/**
 * 주변 실거래가 표시
 * window.__TRADE_DATA__: 빌드 타임에 수집한 같은 법정구 실거래 배열 (국토부)
 * API 키는 HTML에 노출하지 않음 — 빌드 타임 pre-fetch 방식
 */
(function () {
  var priceSection = document.getElementById('price-loading');
  if (!priceSection) return;

  var rows = (typeof window.__TRADE_DATA__ !== 'undefined') ? window.__TRADE_DATA__ : [];

  if (!rows || !rows.length) {
    priceSection.innerHTML = '<span style="color:var(--text-muted); font-size:.85rem;">최근 실거래 데이터가 없습니다.</span>';
    return;
  }

  render(rows);

  function render(items) {
    var loading = document.getElementById('price-loading');
    var table   = document.getElementById('price-table');
    var tbody   = document.getElementById('price-tbody');
    var compare = document.getElementById('price-compare');
    if (!tbody) return;

    /* 금액 내림차순 정렬 후 상위 20건 */
    items = items.slice().sort(function (a, b) {
      return price(b) - price(a);
    }).slice(0, 20);

    if (!items.length) {
      loading.innerHTML = '<span style="color:var(--text-muted); font-size:.85rem;">최근 실거래 데이터가 없습니다.</span>';
      return;
    }

    items.forEach(function (r) {
      var tr = document.createElement('tr');
      var p  = price(r);
      var uk = Math.floor(p / 10000);
      var man = p % 10000;
      var priceStr = uk ? uk + '억' + (man ? ' ' + man.toLocaleString() + '만' : '') : p.toLocaleString() + '만';
      var ym = String(r.dealYear || '') + '.' + String(r.dealMonth || '').padStart(2, '0');
      tr.innerHTML = '<td>' + esc(r.aptNm || '-') + '</td>'
                   + '<td>' + esc(r.excluUseAr || '-') + '㎡</td>'
                   + '<td class="num">' + priceStr + '</td>'
                   + '<td>' + esc(ym) + '</td>';
      tbody.appendChild(tr);
    });

    loading.style.display = 'none';
    table.style.display   = '';

    /* 분양가 vs 평균 실거래가 비교 */
    var minPrice = parseInt(document.body.dataset.minPrice || '0', 10);
    if (minPrice && compare) {
      var avg = Math.round(items.reduce(function (s, r) { return s + price(r); }, 0) / items.length);
      var diff = minPrice - avg;
      var diffStr = Math.abs(diff).toLocaleString() + '만';
      var arrow = diff > 0 ? '▲' : '▼';
      var cls   = diff > 0 ? 'comp-hot' : 'comp-good';
      var uk2 = Math.floor(minPrice / 10000), man2 = minPrice % 10000;
      var saleStr = uk2 ? uk2 + '억' + (man2 ? ' ' + man2.toLocaleString() + '만' : '') : minPrice.toLocaleString() + '만';
      compare.innerHTML = '<strong>분양가 (최저)</strong> ' + saleStr
        + ' &nbsp;<span class="arrow">' + arrow + '</span>&nbsp;'
        + '주변 평균 실거래가 대비 <span class="' + cls + '">' + diffStr + ' ' + (diff > 0 ? '높음' : '낮음') + '</span>';
    }
  }

  function price(r) {
    return parseInt(String(r.dealAmount || '0').replace(/,/g, ''), 10);
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
})();
