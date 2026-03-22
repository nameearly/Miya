/**
 * 资源预加载策略
 * 根据用户行为预测并预加载资源
 */

interface PreloadConfig {
  prefetch: boolean;
  priority: 'high' | 'low';
}

const preloadedResources = new Set<string>();

/**
 * 预加载页面组件
 */
export function preloadPage(pageName: string): void {
  const pageMap: Record<string, () => Promise<any>> = {
    chat: () => import('../components/ChatInterface'),
    management: () => import('../pages/Management'),
    monitor: () => import('../pages/Monitor'),
    home: () => import('../pages/Home'),
  };

  const loader = pageMap[pageName];
  if (loader && !preloadedResources.has(pageName)) {
    loader().then(() => {
      preloadedResources.add(pageName);
      console.log(`[Preload] ${pageName} page loaded`);
    });
  }
}

/**
 * 预加载图片资源
 */
export function preloadImage(src: string, config: PreloadConfig = { prefetch: true, priority: 'low' }): void {
  if (preloadedResources.has(src)) return;

  if (config.prefetch) {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.as = 'image';
    link.href = src;
    link.setAttribute('fetchpriority', config.priority);
    document.head.appendChild(link);
  } else {
    const img = new Image();
    img.src = src;
    img.onload = () => preloadedResources.add(src);
  }
}

/**
 * 预加载字体文件
 */
export function preloadFont(fontFamily: string, src: string): void {
  if (preloadedResources.has(src)) return;

  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = 'font';
  link.type = 'font/woff2';
  link.href = src;
  link.crossOrigin = 'anonymous';
  document.head.appendChild(link);
  preloadedResources.add(src);
}

/**
 * 智能预加载策略
 * 根据鼠标悬停预测用户意图
 */
export function initSmartPreload(): void {
  const navButtons = document.querySelectorAll('[data-preload]');
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const page = entry.target.getAttribute('data-preload');
          if (page) {
            preloadPage(page);
            observer.unobserve(entry.target);
          }
        }
      });
    },
    { rootMargin: '100px' }
  );

  navButtons.forEach((button) => observer.observe(button as Element));
}

/**
 * 预加载常用 API 数据
 */
export function preloadApiData(): void {
  // 不再预加载系统信息，因为这些端点在 Web 端可能不存在
  // 改为静默忽略错误，避免控制台出现 404
}

/**
 * 清理预加载的资源（节省内存）
 */
export function cleanupPreload(): void {
  // 只保留最近访问的 5 个资源
  const resources = Array.from(preloadedResources);
  if (resources.length > 5) {
    resources.slice(0, resources.length - 5).forEach((resource) => {
      preloadedResources.delete(resource);
    });
  }
}

// 每 5 分钟清理一次预加载缓存
if (typeof window !== 'undefined') {
  setInterval(cleanupPreload, 5 * 60 * 1000);
}
