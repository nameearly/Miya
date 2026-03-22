import { apiClient } from './client';
import type { BlogPost, BlogPostCreate, BlogPostUpdate, BlogListResponse } from '../types';

/**
 * 获取博客列表
 */
export async function getBlogPosts(params?: {
  page?: number;
  per_page?: number;
  category?: string;
  tag?: string;
}): Promise<BlogListResponse> {
  return apiClient.get<BlogListResponse>('/api/blog/posts', { params });
}

/**
 * 获取单篇博客
 */
export async function getBlogPost(slug: string): Promise<BlogPost> {
  return apiClient.get<BlogPost>(`/api/blog/posts/${slug}`);
}

/**
 * 创建博客文章
 */
export async function createBlogPost(post: BlogPostCreate): Promise<BlogPost> {
  return apiClient.post<BlogPost>('/api/blog/posts', post);
}

/**
 * 更新博客文章
 */
export async function updateBlogPost(slug: string, post: BlogPostUpdate): Promise<BlogPost> {
  return apiClient.put<BlogPost>(`/api/blog/posts/${slug}`, post);
}

/**
 * 删除博客文章
 */
export async function deleteBlogPost(slug: string): Promise<{ success: boolean; message: string }> {
  return apiClient.delete<{ success: boolean; message: string }>(`/api/blog/posts/${slug}`);
}
