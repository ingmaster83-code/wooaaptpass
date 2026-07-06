// 헤더 검색 — 엔터 키로 목록 페이지 이동
(function () {
  const input = document.getElementById('header-search');
  if (!input) return;
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value.trim()) {
      location.href = `/list.html?q=${encodeURIComponent(input.value.trim())}`;
    }
  });
  input.closest('.header-search')?.querySelector('button')?.addEventListener('click', () => {
    if (input.value.trim()) {
      location.href = `/list.html?q=${encodeURIComponent(input.value.trim())}`;
    }
  });

  // 현재 페이지 nav 활성화
  const path = location.pathname;
  document.querySelectorAll('.nav-links a').forEach((a) => {
    if (a.getAttribute('href') === path || (path !== '/' && path.includes(a.getAttribute('href')))) {
      a.classList.add('active');
    }
  });
})();
