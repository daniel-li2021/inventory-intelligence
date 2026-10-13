export type Exact = string | { numerator: string; denominator: string } | null;
export interface Card {
  id: string;
  sku_id: string;
  warehouse_id: string;
  sku_code: string;
  style_id: string;
  style: string;
  color: string;
  size: string;
  location: string;
  category: string;
  status: string;
  title: string;
  explanation: string;
  on_hand: Exact;
  proposed_order_qty: Exact;
  forecast_daily: Exact;
  exposure: Exact;
  history_state: string;
  reasons: string[];
  references: { source: string; id: string }[];
}
export interface Context {
  contract_version: string;
  archive_digest: string;
  synthetic: boolean;
  cutoff: string;
  cutoffs: string[];
  summary: Record<string, number>;
  highlights: Card[];
  dimensions: Record<string, unknown>;
}
export interface Route {
  page: string;
  offset: number;
  snapshot?: string;
  item?: string;
  type?: string;
  style?: string;
  color?: string;
  size?: string;
  location?: string;
  status?: string;
  q?: string;
  view?: string;
  archive?: string;
  schema?: string;
  scenario?: string;
  sort?: string;
  direction?: string;
}
