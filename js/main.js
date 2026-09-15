  // ============ 页面切换 ============
  function switchPage(pageId) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    // 显示目标页面
    const target = document.getElementById('page-' + pageId);
    if (target) {
      target.classList.add('active');
      // 重新触发渐入动画
      target.querySelectorAll('.fade-in').forEach((el, i) => {
        el.classList.remove('visible');
        setTimeout(() => {
          el.classList.add('visible');
        }, i * 100);
      });
    }
    // 更新导航高亮
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`.nav-item[data-page="${pageId}"]`).classList.add('active');
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ============ 渐入动画（IntersectionObserver）============
  function initFadeIn() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
  }

  // ============ 初始化 ============
  document.addEventListener('DOMContentLoaded', () => {
    initFadeIn();
    // 首页元素立即显示
    document.querySelectorAll('#page-overview .fade-in').forEach((el, i) => {
      setTimeout(() => el.classList.add('visible'), i * 100);
    });
  });
