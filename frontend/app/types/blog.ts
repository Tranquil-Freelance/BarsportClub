export interface WpPost {
  id: number;
  slug: string;
  title: {
    rendered: string;
  };
  excerpt: {
    rendered: string;
  };
  content: {
    rendered: string;
  };
  date: string;
  _embedded?: {
    'wp:featuredmedia'?: Array<{
      source_url: string;
      alt_text: string;
      media_details?: {
        sizes?: {
          medium?: {
            source_url: string;
          };
          large?: {
            source_url: string;
          };
          thumbnail?: {
            source_url: string;
          };
        };
      };
    }>;
  };
}

export interface BlogPageProps {
  posts: WpPost[];
}

export interface ArticlePageProps {
  post: WpPost;
}