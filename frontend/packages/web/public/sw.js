/// <reference lib="webworker" />

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `miya-static-${CACHE_VERSION}`;
const API_CACHE = `miya-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `miya-images-${CACHE_VERSION}`;

// 缓存策略配置
const CACHE_STRATEGIES = {
  // 静态资源：长期缓存
  static: {
    name: STATIC_CACHE,
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 天
  },
  // API 请求：短期缓存
  api: {
    name: API_CACHE,
    maxAge: 5 * 60 * 1000, // 5 分钟
  },
  // 图片：中期缓存
  image: {
    name: IMAGE_CACHE,
    maxAge: 30 * 60 * 1000, // 30 分钟
  },
};

// 需要预缓存的资源
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// API 类型判断
const isApiRequest = (url: URL): boolean => {
  return url.pathname.startsWith('/api/');
};

// 静态资源判断
const isStaticResource = (request: Request): boolean => {
  const type = request.destination;
  return (
    type === 'script' ||
    type === 'style' ||
    type === 'font' ||
    request.url.includes('.js') ||
    request.url.includes('.css') ||
    request.url.includes('.woff')
  );
};

// 图片资源判断
const isImageRequest = (request: Request): boolean => {
  return request.destination === 'image' ||
         request.url.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i);
};

self.addEventListener('install', (event: ExtendableEvent) => {
  console.log('[SW] Install');
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log('[SW] Precaching app shell');
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event: ExtendableEvent) => {
  console.log('[SW] Activate');
  event.waitUntil(
    Promise.all([
      // 清理旧缓存
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            const isValidCache = Object.values(CACHE_STRATEGIES).some(
              (strategy) => strategy.name === cacheName
            );
            if (!isValidCache) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // 立即控制所有客户端
      self.clients.claim(),
    ])
  );
});

self.addEventListener('fetch', (event: FetchEvent) => {
  const { request } = event;
  const url = new URL(request.url);

  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }

  // API 请求：网络优先 + 失败回退
  if (isApiRequest(url)) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // 静态资源：缓存优先
  if (isStaticResource(request)) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // 图片：缓存优先
  if (isImageRequest(request)) {
    event.respondWith(handleImageRequest(request));
    return;
  }

  // HTML：网络优先 + 失败回退
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }

  // 其他：直接网络请求
  event.respondWith(fetch(request));
});

/**
 * API 请求处理：网络优先
 */
async function handleApiRequest(request: Request): Promise<Response> {
  try {
    const response = await fetch(request);

    // 只缓存 GET 请求的成功响应
    if (request.method === 'GET' && response.ok) {
      const cache = await caches.open(API_CACHE);
      await cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    // 网络失败时尝试从缓存读取
    const cached = await caches.match(request);
    if (cached) {
      console.log('[SW] API fallback to cache:', request.url);
      return cached;
    }
    throw error;
  }
}

/**
 * 静态资源处理：缓存优先
 */
async function handleStaticRequest(request: Request): Promise<Response> {
  const cached = await caches.match(request);

  if (cached) {
    // 检查缓存是否过期
    const date = cached.headers.get('date');
    if (date) {
      const cacheAge = Date.now() - new Date(date).getTime();
      if (cacheAge < CACHE_STRATEGIES.static.maxAge) {
        return cached;
      }
    }
  }

  // 缓存未命中或已过期
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(STATIC_CACHE);
    await cache.put(request, response.clone());
  }

  return response;
}

/**
 * 图片处理：缓存优先
 */
async function handleImageRequest(request: Request): Promise<Response> {
  const cached = await caches.match(request);

  if (cached) {
    const date = cached.headers.get('date');
    if (date) {
      const cacheAge = Date.now() - new Date(date).getTime();
      if (cacheAge < CACHE_STRATEGIES.image.maxAge) {
        return cached;
      }
    }
  }

  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(IMAGE_CACHE);
    await cache.put(request, response.clone());
  }

  return response;
}

/**
 * 导航处理：网络优先
 */
async function handleNavigationRequest(request: Request): Promise<Response> {
  try {
    const response = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    await cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await caches.match('/index.html');
    if (cached) {
      return cached;
    }
    throw error;
  }
}

// 监听消息事件
self.addEventListener('message', (event) => {
  if (event.data) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'CLEAR_CACHE':
        clearAllCaches();
        break;
    }
  }
});

/**
 * 清理所有缓存
 */
async function clearAllCaches(): Promise<void> {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((name) => caches.delete(name)));
  console.log('[SW] All caches cleared');
}

export {};
