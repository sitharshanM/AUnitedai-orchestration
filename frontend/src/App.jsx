import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import "./Result.css";
import "./Desktop.css";

// Development uses Vite on :5173. The packaged desktop build is served by the
// embedded FastAPI process, so API requests stay on the same private origin.
const API = import.meta.env.VITE_API_URL ?? (window.location.port === "5173" ? "http://localhost:8000" : "");
const TABS = ["Tasks", "Blackboard", "Messages", "Artifacts", "Timeline", "Developer"];
const call = async (path, options = {}) => {
  const response = await fetch(`${API}${path}`, {headers:{"Content-Type":"application/json"}, ...options});
  if (!response.ok) throw new Error((await response.json().catch(()=>({}))).detail || `Request failed (${response.status})`);
  return response.json();
};
const label = (value="") => value.replaceAll("_"," ").replace(/\b\w/g, c=>c.toUpperCase());
const clock = value => value ? new Date(value).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit",second:"2-digit"}) : "--:--";

const inlineMarkdown = (text, key="inline") => text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)]+\))/g).filter(Boolean).map((part,index)=>{
  if(part.startsWith("**")&&part.endsWith("**"))return <strong key={`${key}-${index}`}>{part.slice(2,-2)}</strong>;
  if(part.startsWith("`")&&part.endsWith("`"))return <code key={`${key}-${index}`}>{part.slice(1,-1)}</code>;
  const link=part.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/);
  if(link)return <a key={`${key}-${index}`} href={link[2]} target="_blank" rel="noreferrer">{link[1]}</a>;
  return part;
});

function MarkdownView({content=""}){
  const lines=content.replaceAll("\r\n","\n").split("\n"), blocks=[];
  for(let i=0;i<lines.length;){
    const line=lines[i];
    if(!line.trim()){i++;continue}
    if(line.startsWith("```")){
      const language=line.slice(3).trim();let code="";i++;
      while(i<lines.length&&!lines[i].startsWith("```")){code+=`${lines[i]}\n`;i++}
      blocks.push(<pre className="code-block" key={`code-${i}`}><span>{language||"code"}</span><code>{code.trimEnd()}</code></pre>);i++;continue;
    }
    if(/^\|.*\|$/.test(line.trim())){
      const rows=[];
      while(i<lines.length&&/^\|.*\|$/.test(lines[i].trim())){rows.push(lines[i].trim().slice(1,-1).split("|").map(x=>x.trim()));i++}
      const clean=rows.filter(row=>!row.every(cell=>/^:?-+:?$/.test(cell)));
      blocks.push(<div className="result-table-wrap" key={`table-${i}`}><table><tbody>{clean.map((row,r)=><tr key={r}>{row.map((cell,c)=>r===0?<th key={c}>{inlineMarkdown(cell,`${r}-${c}`)}</th>:<td key={c}>{inlineMarkdown(cell,`${r}-${c}`)}</td>)}</tr>)}</tbody></table></div>);continue;
    }
    const heading=line.match(/^(#{1,4})\s+(.+)$/);
    if(heading){const Tag=`h${heading[1].length}`;blocks.push(<Tag key={`h-${i}`}>{inlineMarkdown(heading[2],`h-${i}`)}</Tag>);i++;continue}
    if(/^---+$/.test(line.trim())){blocks.push(<hr key={`hr-${i}`}/>);i++;continue}
    if(/^\s*[-*]\s+/.test(line)){
      const items=[];while(i<lines.length&&/^\s*[-*]\s+/.test(lines[i])){items.push(lines[i].replace(/^\s*[-*]\s+/,""));i++}
      blocks.push(<ul key={`ul-${i}`}>{items.map((item,n)=><li key={n}>{inlineMarkdown(item,`ul-${i}-${n}`)}</li>)}</ul>);continue;
    }
    if(/^\s*\d+\.\s+/.test(line)){
      const items=[];while(i<lines.length&&/^\s*\d+\.\s+/.test(lines[i])){items.push(lines[i].replace(/^\s*\d+\.\s+/,""));i++}
      blocks.push(<ol key={`ol-${i}`}>{items.map((item,n)=><li key={n}>{inlineMarkdown(item,`ol-${i}-${n}`)}</li>)}</ol>);continue;
    }
    const paragraph=[line];i++;while(i<lines.length&&lines[i].trim()&&!/^(#{1,4})\s|^```|^\|.*\|$|^\s*[-*]\s+|^\s*\d+\.\s+|^---+$/.test(lines[i])){paragraph.push(lines[i]);i++}
    blocks.push(<p key={`p-${i}`}>{inlineMarkdown(paragraph.join(" "),`p-${i}`)}</p>);
  }
  return <div className="markdown-view">{blocks}</div>;
}

function ResultPanel({content,status="incomplete",artifacts=[],onPreview}){
  const [copied,setCopied]=useState(false);
  const copy=async()=>{await navigator.clipboard.writeText(content);setCopied(true);setTimeout(()=>setCopied(false),1500)};
  if(!content)return <div className="result-empty"><span>RESULT</span><h2>Your finished work will appear here</h2><p>Run the objective to see the primary deliverable, supporting files, and verification status without leaving the main workspace.</p></div>;
  return <div className="result-panel"><header className="result-toolbar"><div><span>FINAL RESULT</span><b className={status==="incomplete"?"incomplete":"verified"}>{status}</b></div><button onClick={copy}>{copied?"COPIED":"COPY RESULT"}</button></header><div className="result-scroll"><MarkdownView content={content}/>{artifacts.length>0&&<section className="result-files"><h3>Supporting files</h3><div>{artifacts.map(file=><button key={file.id} onClick={()=>onPreview(file)}><span>◆</span><b>{file.name}</b><small>{file.verified?"Verified file":"Unverified"}</small></button>)}</div></section>}</div></div>;
}

function AgentGraph({workspace, selected, select}) {
  const agents=workspace?.agents||[];
  return <div className="agent-canvas"><div className="graph-grid"/><svg className="connections" viewBox="0 0 800 420" preserveAspectRatio="none">{agents.map((a,i)=><line key={a.id} x1="400" y1="210" x2={120+(i%3)*280} y2={i<3?90:330} className={`flow ${a.status}`}/>)}</svg>
    {agents.length>0&&<div className="objective-node"><span>OBJECTIVE</span><b>{workspace.objective.status}</b></div>}
    {agents.map((a,i)=><button key={a.id} className={`agent-node ${a.status} ${selected?.id===a.id?"selected":""}`} style={{left:`${12+(i%3)*38}%`,top:i<3?"17%":"72%"}} onClick={()=>select(a)}><i/><span>{a.name}</span><small>{a.dna.role} · {a.status}</small></button>)}
    {!agents.length&&<div className="empty-graph">Enter an objective to form an AI organization.</div>}
  </div>;
}

function Board({tasks,onUpdate}) {
  const columns=["backlog","ready","running","blocked","review","done","failed"];
  return <div className="task-board">{columns.map(status=><section className="task-column" key={status}><header>{label(status)}<b>{tasks.filter(t=>t.status===status).length}</b></header>{tasks.filter(t=>t.status===status).map(task=><article key={task.id}><strong>{task.title}</strong><p>{task.description}</p><footer><span>{task.required_capabilities?.[0]||"general"}</span><button onClick={()=>onUpdate(task,status==="done"?"review":"done")}>{status==="done"?"REOPEN":"DONE"}</button></footer></article>)}</section>)}</div>;
}

function Inspector({agent,close,change}) {
  if(!agent)return null;
  return <aside className="inspector"><header><div><span>AGENT INSPECTOR</span><h2>{agent.name}</h2></div><button onClick={close}>×</button></header><dl><dt>Role</dt><dd>{agent.dna.role}</dd><dt>Status</dt><dd className="good">{agent.status}</dd><dt>Model</dt><dd>{agent.model}</dd><dt>Mission</dt><dd>{agent.dna.mission}</dd><dt>Authority</dt><dd>{JSON.stringify(agent.dna.authority)}</dd></dl><h3>CAPABILITIES</h3><div className="chips">{agent.dna.capabilities.map(x=><span key={x}>{x}</span>)}</div><h3>TOOLS</h3><div className="chips muted">{agent.dna.allowed_tools.map(x=><span key={x}>{x}</span>)}</div><div className="inspector-actions"><button onClick={()=>change(agent,agent.status==="waiting"?"idle":"waiting")}>{agent.status==="waiting"?"RESUME":"PAUSE"}</button><button className="danger" onClick={()=>change(agent,"terminated")}>TERMINATE</button></div></aside>;
}

const PROVIDERS = ["OpenAI", "Gemini", "Anthropic", "Groq", "DeepSeek", "TogetherAI", "Ollama", "Custom API"];
const KEY_FIELDS = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY", "TOGETHER_API_KEY", "CUSTOM_API_KEY"];

function Settings({close, notify}) {
  const [config,setConfig]=useState(null),[keys,setKeys]=useState({}),[password,setPassword]=useState(""),[saving,setSaving]=useState(false),[message,setMessage]=useState("");
  useEffect(()=>{call("/config").then(data=>setConfig(data)).catch(error=>setMessage(error.message))},[]);
  const updateWorker=(name,field,value)=>setConfig(current=>({...current,workers:{...current.workers,[name]:{...current.workers[name],[field]:value}}}));
  const save=async()=>{if(!config)return;setSaving(true);setMessage("");try{await call("/config/keys",{method:"POST",body:JSON.stringify({...keys,password})});await call(`/config/workers?password=${encodeURIComponent(password)}`,{method:"POST",body:JSON.stringify(config.workers)});setMessage("Settings saved. New tasks will use these models.");notify?.()}catch(error){setMessage(error.message)}finally{setSaving(false)}};
  return <div className="settings-backdrop" role="presentation" onMouseDown={close}><aside className="settings" role="dialog" aria-modal="true" aria-label="Model settings" onMouseDown={event=>event.stopPropagation()}><header><div><span>MODEL SETTINGS</span><h2>Providers & workers</h2></div><button onClick={close}>×</button></header><p className="settings-note">Keys are saved locally and never displayed again. Set a provider and model for every worker you plan to run.</p>{!config?<p className="empty">Loading settings…</p>:<><section><h3>API KEYS</h3><div className="key-grid">{KEY_FIELDS.map(name=><label key={name}><span>{name.replace("_API_KEY","").replaceAll("_"," ")}</span><input type="password" autoComplete="off" placeholder={config.keys[name]?"Saved — enter a replacement":"Paste key"} value={keys[name]||""} onChange={event=>setKeys(current=>({...current,[name]:event.target.value}))}/></label>)}</div><label className="base-url-field"><span>CUSTOM API BASE URL</span><input type="url" autoComplete="off" placeholder={config.keys.CUSTOM_BASE_URL||"https://provider.example/v1"} value={keys.CUSTOM_BASE_URL||""} onChange={event=>setKeys(current=>({...current,CUSTOM_BASE_URL:event.target.value}))}/></label></section><section><h3>WORKERS</h3><div className="worker-list">{Object.entries(config.workers).map(([name,worker])=><div className="worker-row" key={name}><b>{label(name)}</b><select value={worker.backend} onChange={event=>updateWorker(name,"backend",event.target.value)}>{PROVIDERS.map(provider=><option key={provider}>{provider}</option>)}</select><input aria-label={`${name} model`} value={worker.model} onChange={event=>updateWorker(name,"model",event.target.value)} placeholder="Model name"/></div>)}</div></section><label className="password-field"><span>APP PASSWORD (only if configured)</span><input type="password" value={password} onChange={event=>setPassword(event.target.value)} autoComplete="current-password"/></label><footer><span className={message.includes("saved")?"saved":""}>{message}</span><button onClick={save} disabled={saving}>{saving?"SAVING…":"SAVE SETTINGS"}</button></footer></>}</aside></div>;
}

export default function App(){
  const [online,setOnline]=useState(false),[objective,setObjective]=useState(""),[objectives,setObjectives]=useState([]),[workspace,setWorkspace]=useState(null),[agent,setAgent]=useState(null),[tab,setTab]=useState("Tasks"),[mode,setMode]=useState("supervised"),[busy,setBusy]=useState(false),[error,setError]=useState(""),[command,setCommand]=useState(""),[answer,setAnswer]=useState(null),[output,setOutput]=useState(""),[delivery,setDelivery]=useState(null),[stageView,setStageView]=useState("organization"),[artifactPreview,setArtifactPreview]=useState(null),[settingsOpen,setSettingsOpen]=useState(false);
  const list=()=>call("/api/objectives").then(setObjectives).catch(()=>{});
  const load=async id=>{setBusy(true);try{const next=await call(`/api/workspaces/${id}`);setWorkspace(next);setAgent(null);setOutput("");const entries=[...(next.blackboard||[])].reverse(),saved=entries.find(x=>x.metadata?.kind==="delivery"),legacy=entries.find(x=>x.type==="task_result"&&x.content?.includes("The following model-generated report"));const marker="The following model-generated report is untrusted unless supported by the evidence above:";const restored=saved?.content||(legacy?.content.includes(marker)?legacy.content.split(marker).slice(1).join(marker).trim():"");setDelivery(restored?{content:restored,verification_status:saved?.metadata?.verification_status||"complete",artifacts:next.artifacts||[]}:null);setStageView(restored?"result":"organization")}catch(e){setError(e.message)}finally{setBusy(false)}};
  useEffect(()=>{call("/health").then(()=>setOnline(true)).catch(()=>setOnline(false));list()},[]);
  useEffect(()=>{if(!workspace?.objective?.id||!["running","planning"].includes(workspace.objective.status))return;const timer=setInterval(()=>call(`/api/workspaces/${workspace.objective.id}`).then(setWorkspace).catch(()=>{}),5000);return()=>clearInterval(timer)},[workspace?.objective?.id,workspace?.objective?.status]);
  const create=async()=>{if(!objective.trim())return;setBusy(true);setError("");try{const made=await call("/api/workspaces",{method:"POST",body:JSON.stringify({objective,mode})});setWorkspace({...made,tasks:made.plan.tasks,messages:[],approvals:[],usage:[],blackboard:[],events:[],observer:[],metrics:{progress:0,tasks_done:0,tasks_total:made.plan.tasks.length,agents:made.agents.length,active_agents:0,cost:0}});list()}catch(e){setError(e.message)}finally{setBusy(false)}};
  const run=async()=>{setBusy(true);setOutput("Execution in progress…");setStageView("result");try{const r=await call(`/api/workspaces/${workspace.objective.id}/execute`,{method:"POST"});const finalContent=r.delivery?.content||r.result?.final_report||JSON.stringify(r.result,null,2);setOutput(finalContent);setDelivery(r.delivery||{content:finalContent,verification_status:"incomplete",artifacts:r.workspace?.artifacts||[]});setWorkspace(r.workspace)}catch(e){const message=`# Execution failed\n\n${e.message}`;setOutput(message);setDelivery({content:message,verification_status:"incomplete",artifacts:[]});setError(e.message)}finally{setBusy(false)}};
  const control=async action=>{try{await call(`/api/objectives/${workspace.objective.id}/control`,{method:"POST",body:JSON.stringify({action})});await load(workspace.objective.id)}catch(e){setError(e.message)}};
  const updateTask=async(t,status)=>{try{await call(`/api/tasks/${t.id}`,{method:"PATCH",body:JSON.stringify({status})});await load(workspace.objective.id)}catch(e){setError(e.message)}};
  const updateAgent=async(a,status)=>{try{const x=await call(`/api/agents/${a.id}`,{method:"PATCH",body:JSON.stringify({status})});setAgent(x);await load(workspace.objective.id)}catch(e){setError(e.message)}};
  const ask=async e=>{e.preventDefault();if(!command.trim())return;try{setAnswer(await call(`/api/workspaces/${workspace.objective.id}/command`,{method:"POST",body:JSON.stringify({command})}))}catch(x){setError(x.message)}};
  const grouped=useMemo(()=>{const out={};for(const item of workspace?.blackboard||[])(out[item.type]??=[]).push(item);return out},[workspace?.blackboard]);
  const tasks=workspace?.tasks||workspace?.plan?.tasks||[], metrics=workspace?.metrics||{};
  const showArtifact=async file=>{setArtifactPreview({file,loading:true});try{const preview=await call(`/api/workspaces/${workspace.objective.id}/artifacts/${file.id}`);setArtifactPreview({file,...preview})}catch(e){setArtifactPreview({file,error:e.message})}};
  return <div className="workstation"><header className="topbar"><div className="brand"><img src="/aunitedai-logo.png" alt="AUnitedAI flaming heart"/><div><strong>AUnitedAI</strong><span>AUTONOMOUS WORKSTATION 2.0</span></div></div><div className="active-objective"><span>ACTIVE OBJECTIVE</span><b>{workspace?.objective?.objective||"No objective selected"}</b></div><label><span>MODE</span><select value={mode} onChange={e=>setMode(e.target.value)}><option value="observe">Observe</option><option value="suggest">Suggest</option><option value="supervised">Supervised</option><option value="autonomous_sandbox">Autonomous sandbox</option></select></label><div className="cost"><span>COST</span><b>${(metrics.cost||0).toFixed(2)}</b></div><button className="settings-button" onClick={()=>setSettingsOpen(true)}>SETTINGS</button><div className={`system ${online?"online":"offline"}`}><i/>{online?"SYSTEM ONLINE":"OFFLINE"}</div></header>
  <div className="objective-entry"><textarea value={objective} onChange={e=>setObjective(e.target.value)} placeholder="Describe one objective. AUnitedAI will plan, form a team, assign work, and verify the outcome."/><button onClick={create} disabled={!online||busy||!objective.trim()}>{busy?"WORKING…":"FORM ORGANIZATION"}</button>{workspace&&<button className="secondary" onClick={run} disabled={busy}>RUN OBJECTIVE</button>}</div>{error&&<div className="error">{error}<button onClick={()=>setError("")}>×</button></div>}
  <main><aside className="projects"><header>PROJECTS <button onClick={list}>↻</button></header><div>{objectives.map(o=><button key={o.id} className={workspace?.objective?.id===o.id?"active":""} onClick={()=>load(o.id)}><i/><span>{o.objective}</span><small>{o.status}</small></button>)}</div>{workspace&&<footer><span>HUMAN CONTROL</span><button onClick={()=>control(workspace.objective.status==="paused"?"resume":"pause")}>{workspace.objective.status==="paused"?"RESUME":"PAUSE"}</button><button onClick={()=>control("replan")}>REPLAN</button><button className="danger" onClick={()=>control("cancel")}>CANCEL</button></footer>}</aside>
  <section className={`stage ${stageView==="result"?"showing-result":""}`}><header><div><span>{stageView==="result"?"DELIVERY":"LIVE ORGANIZATION"}</span><b>{stageView==="result"?(delivery?.verification_status||"Awaiting result"):`${workspace?.agents?.length||0} AGENTS · ${tasks.length} TASKS`}</b></div><div className="stage-switch"><button className={stageView==="result"?"active":""} onClick={()=>setStageView("result")}>RESULT</button><button className={stageView==="organization"?"active":""} onClick={()=>setStageView("organization")}>ORGANIZATION</button></div></header>{stageView==="result"?<ResultPanel content={delivery?.content||output} status={delivery?.verification_status} artifacts={delivery?.artifacts||workspace?.artifacts||[]} onPreview={showArtifact}/>:<AgentGraph workspace={workspace} selected={agent} select={setAgent}/>}<footer className="metrics"><div><span>PROGRESS</span><b className="cyan">{metrics.progress||0}%</b></div><div><span>TASKS</span><b>{metrics.tasks_done||0}/{metrics.tasks_total||0}</b></div><div><span>AGENTS</span><b>{metrics.agents||0}</b></div><div><span>BLOCKERS</span><b>{tasks.filter(t=>t.status==="blocked").length}</b></div><i style={{width:`${metrics.progress||0}%`}}/></footer></section>
  <aside className="activity"><header>LIVE ACTIVITY <b>{workspace?.events?.length||0}</b></header><div>{[...(workspace?.events||[])].reverse().map(e=><article key={e.id}><time>{clock(e.timestamp)}</time><i/><p><b>{label(e.type)}</b><span>{e.payload?.name||e.payload?.status||"Recorded"}</span></p></article>)}{!workspace?.events?.length&&<p className="empty">Activity will appear here.</p>}</div></aside></main>
  <section className="lower"><nav>{TABS.map(x=><button key={x} className={tab===x?"active":""} onClick={()=>setTab(x)}>{x}<b>{x==="Tasks"?tasks.length:x==="Blackboard"?workspace?.blackboard?.length||0:x==="Messages"?workspace?.messages?.length||0:x==="Artifacts"?workspace?.artifacts?.length||0:""}</b></button>)}</nav><div className="tab-content">{tab==="Tasks"&&<Board tasks={tasks} onUpdate={updateTask}/>} {tab==="Blackboard"&&<div className="blackboard">{Object.entries(grouped).map(([kind,entries])=><section key={kind}><header>{label(kind)}</header>{entries.map(x=><article key={x.id}><p>{x.metadata?.kind==="delivery"?"Final delivery saved — view it in the main Result panel.":x.content}</p><small>confidence {x.confidence??"—"} · relevance {x.relevance}</small></article>)}</section>)}{!workspace?.blackboard?.length&&<p className="empty">Structured knowledge appears here.</p>}</div>} {tab==="Messages"&&<div className="messages">{(workspace?.messages||[]).map(x=><article key={x.id}><b>{label(x.type)}</b><span>{x.sender_agent_id.slice(0,8)} → {x.recipient_agent_id?.slice(0,8)||"team"}</span><p>{x.content}</p></article>)}{!workspace?.messages?.length&&<p className="empty">No inter-agent messages yet.</p>}</div>} {tab==="Artifacts"&&<div className="artifacts">{(workspace?.artifacts||[]).map(x=><button className="artifact-card" key={x.id} onClick={()=>showArtifact(x)}>◆ <div><b>{x.name}</b><span>{x.path} · {x.size_bytes} bytes · {x.verified?"verified":"unverified"}</span><small>OPEN PREVIEW</small></div></button>)}{!workspace?.artifacts?.length&&<p className="empty">No real files were produced. Expected deliverables are not counted as artifacts.</p>}</div>} {tab==="Timeline"&&<div className="timeline">{(workspace?.events||[]).map(e=><article key={e.id}><time>{clock(e.timestamp)}</time><i/><div><b>{label(e.type)}</b><pre>{JSON.stringify(e.payload)}</pre></div></article>)}</div>} {tab==="Developer"&&<><pre>{JSON.stringify(workspace,null,2)}</pre>{output&&<pre className="output">{output}</pre>}</>}</div></section>
  <form className="command" onSubmit={ask}><span>⌘</span><input value={command} onChange={e=>setCommand(e.target.value)} disabled={!workspace} placeholder="Ask Architect…  Show blockers…  Why was this decision made?"/><kbd>ENTER</kbd></form>{answer&&<div className="answer"><button onClick={()=>setAnswer(null)}>×</button><b>{answer.command}</b><pre>{JSON.stringify(answer.result,null,2)}</pre></div>}{artifactPreview&&<div className="artifact-backdrop" onMouseDown={()=>setArtifactPreview(null)}><section className="artifact-preview" onMouseDown={e=>e.stopPropagation()}><header><div><span>ARTIFACT</span><h2>{artifactPreview.file.name}</h2></div><div><a href={`${API}/api/workspaces/${workspace.objective.id}/artifacts/${artifactPreview.file.id}?download=true`}>DOWNLOAD</a><button onClick={()=>setArtifactPreview(null)}>×</button></div></header>{artifactPreview.loading?<p className="empty">Loading preview…</p>:artifactPreview.error?<p className="preview-error">{artifactPreview.error}</p>:<MarkdownView content={artifactPreview.content}/>}</section></div>}<Inspector agent={agent} close={()=>setAgent(null)} change={updateAgent}/>{settingsOpen&&<Settings close={()=>setSettingsOpen(false)} notify={()=>setError("")}/>}</div>;
}
