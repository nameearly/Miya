/**
 * 博客文章
 */
export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt?: string;
  author: string;
  category?: string;
  tags?: string[];
  published: boolean;
  views: number;
  created_at: string;
  updated_at: string;
  coverImage?: string;
}

/**
 * 创建博客文章
 */
export interface BlogPostCreate {
  title: string;
  content: string;
  excerpt?: string;
  author?: string;
  category?: string;
  tags?: string[];
  published?: boolean;
}

/**
 * 更新博客文章
 */
export interface BlogPostUpdate {
  title?: string;
  content?: string;
  excerpt?: string;
  category?: string;
  tags?: string[];
  published?: boolean;
}

/**
 * 博客列表响应
 */
export interface BlogListResponse {
  posts: BlogPost[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
