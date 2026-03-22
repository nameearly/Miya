import { build } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function buildWeb() {
  console.log('正在构建 Web 前端...');
  console.log('工作目录:', __dirname);

  try {
    await build({
      configFile: path.join(__dirname, 'vite.config.ts'),
      mode: 'production',
      root: __dirname,
      publicDir: path.join(__dirname, 'public')
    });

    console.log('构建成功！');
  } catch (error) {
    console.error('构建失败:', error);
    process.exit(1);
  }
}

buildWeb();
