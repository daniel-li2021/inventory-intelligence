import type { ReactNode } from 'react';
import { badgePresentation } from './presentation.mjs';

export function Badge({value}:{value:string}) {
  const {label,tone}=badgePresentation(value);
  return <span className={`badge tone-${tone}`} title={label}>{label}</span>;
}

// Native buttons keep the familiar Tab/Enter interaction without a custom tab keyboard model.
export function ViewNav({label,value,options,onChange}:{label:string;value:string;options:[string,ReactNode][];onChange:(value:string)=>void}) {
  return <nav className="view-nav" aria-label={label}>{options.map(([key,name])=><button key={key} type="button" aria-pressed={key===value} onClick={()=>onChange(key)}>{name}</button>)}</nav>;
}
