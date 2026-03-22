import React, { useEffect, useRef, useState } from 'react';
import type { Live2DConfig, Live2DMotion } from '../types';

interface Live2DAvatarProps extends Partial<Live2DConfig> {
  className?: string;
}

export const Live2DAvatar: React.FC<Live2DAvatarProps> = ({
  model = 'haru',
  width = 300,
  height = 300,
  interactive = true,
  motion = 'idle',
  scale = 1,
  position = { x: 0, y: 0 },
  autoMotion = true,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [currentMotion, setCurrentMotion] = useState<Live2DMotion>(motion);

  useEffect(() => {
    if (!containerRef.current) return;

    // 这里应该加载Live2D模型
    // 实际实现需要使用 pixi-live2d-display 或其他Live2D库
    const loadLive2D = async () => {
      try {
        // 模拟加载
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setIsLoaded(true);
      } catch (error) {
        console.error('Failed to load Live2D model:', error);
      }
    };

    loadLive2D();
  }, [model]);

  useEffect(() => {
    if (autoMotion) {
      // 自动切换表情
      const motions: Live2DMotion[] = ['idle', 'happy', 'talking'];
      let index = 0;

      const interval = setInterval(() => {
        index = (index + 1) % motions.length;
        setCurrentMotion(motions[index]);
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [autoMotion]);

  const handleClick = () => {
    if (interactive) {
      setCurrentMotion('greeting');
      setTimeout(() => setCurrentMotion('idle'), 2000);
    }
  };

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        position: 'relative',
        transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
        cursor: interactive ? 'pointer' : 'default',
      }}
      onClick={handleClick}
    >
      {!isLoaded ? (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100 rounded-full">
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-slate-500">加载 Live2D 模型...</span>
          </div>
        </div>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-sky-100 to-blue-100 rounded-full">
          <div className="text-center">
            <div className="text-6xl mb-2">
              {currentMotion === 'happy' && '😊'}
              {currentMotion === 'talking' && '🗣️'}
              {currentMotion === 'thinking' && '🤔'}
              {currentMotion === 'greeting' && '👋'}
              {currentMotion === 'idle' && '😊'}
              {currentMotion === 'sad' && '😢'}
              {currentMotion === 'angry' && '😠'}
              {currentMotion === 'surprised' && '😲'}
            </div>
            <div className="text-sm text-slate-600">
              {currentMotion === 'idle' && '弥娅正在休息'}
              {currentMotion === 'happy' && '弥娅很高兴'}
              {currentMotion === 'talking' && '弥娅正在说话'}
              {currentMotion === 'thinking' && '弥娅在思考'}
              {currentMotion === 'greeting' && '你好！'}
              {currentMotion === 'sad' && '弥娅有点难过'}
              {currentMotion === 'angry' && '弥娅生气了'}
              {currentMotion === 'surprised' && '哇！'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
