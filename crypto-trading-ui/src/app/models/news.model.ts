export interface NewsItem {
  id: string;
  title: string;
  source: string;
  url: string;
  publishedAt: Date;
  summary: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  impactScore: number; // 1-10 scale indicating potential market impact
  relatedSymbols: string[];
}

export interface NewsResponse {
  news: NewsItem[];
  totalCount: number;
}