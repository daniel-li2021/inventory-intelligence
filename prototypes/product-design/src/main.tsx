import { createRoot } from 'react-dom/client';
import Brief from './brief';
import Desk from './desk';
import { useWorkspace } from './shared';
import './base.css';
function App(){const w=useWorkspace();const direction=new URLSearchParams(location.search).get('direction')||'brief';return direction==='desk'?<Desk w={w}/>:<Brief w={w}/>;}
createRoot(document.getElementById('root')!).render(<App/>);
