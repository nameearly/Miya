/**
 * Service Worker 注册和管理
 */

export function registerSW() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });
        console.log('SW registered: ', registration);

        // 监听更新
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // 有新版本可用
                console.log('New content is available; please refresh.');
                // 可以显示更新提示
                showUpdateNotification();
              }
            });
          }
        });
      } catch (error) {
        console.log('SW registration failed: ', error);
      }
    });
  }
}

function showUpdateNotification() {
  const notification = document.createElement('div');
  notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
  notification.innerHTML = `
    <div class="flex items-center gap-3">
      <span>发现新版本</span>
      <button onclick="this.parentElement.parentElement.remove(); window.location.reload()" class="bg-white text-blue-500 px-4 py-1 rounded-md hover:bg-blue-50 transition">
        立即更新
      </button>
    </div>
  `;
  document.body.appendChild(notification);

  // 5秒后自动消失
  setTimeout(() => notification.remove(), 5000);
}

export function unregisterSW() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then((registration) => {
      registration.unregister();
    });
  }
}

// 检查网络状态
export function initNetworkMonitor() {
  const updateOnlineStatus = () => {
    const isOnline = navigator.onLine;
    document.documentElement.setAttribute('data-online', isOnline.toString());

    if (!isOnline) {
      showOfflineNotification();
    }
  };

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();
}

function showOfflineNotification() {
  const notification = document.createElement('div');
  notification.className = 'fixed bottom-4 right-4 bg-orange-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
  notification.innerHTML = `
    <div class="flex items-center gap-2">
      <span>⚠️ 网络连接已断开</span>
    </div>
  `;
  document.body.appendChild(notification);
}
