export const pages = ['overview','explore','investigate','compare','decide','history','execution','evaluation'];
export const defaultItem = 'product-coast:sku-0|product-coast:site-0';
export function parseRoute(hash) {
  const [path,query=''] = hash.replace(/^#\/?/,'').split('?');
  const p=new URLSearchParams(query);
  return {page:pages.includes(path)?path:'overview',cutoff:p.get('cutoff')||'2026-05-04',item:p.get('item')||defaultItem,search:p.get('search')||'',category:p.get('category')||'',warehouse:p.get('warehouse')||'',sort:p.get('sort')||'priority'};
}
export function routeHash(route) {
  const q=new URLSearchParams();
  for(const key of ['cutoff','item','search','category','warehouse','sort']) if(route[key]) q.set(key,route[key]);
  return '#/'+route.page+'?'+q;
}
export function exact(value) {
  if(value===null||value===undefined)return 'Unknown';
  if(typeof value==='object'&&'numerator' in value) return value.denominator==='1'||value.denominator===1 ? String(value.numerator) : `${value.numerator}/${value.denominator}`;
  return String(value);
}
export function whole(value,min=0,max=2000) {return /^(0|[1-9]\d*)$/.test(value)&&Number.isSafeInteger(Number(value))&&Number(value)>=min&&Number(value)<=max;}
export function currentResource(state,path) {return state.path===path ? state : {loading:Boolean(path)};}
