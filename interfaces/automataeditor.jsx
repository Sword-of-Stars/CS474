import { useState, useRef, useCallback, useMemo, useEffect } from "react";
import { Streamlit } from "streamlit-component-lib";

// ═══════════════════════════════════════════════════════
// Constants & Geometry
// ═══════════════════════════════════════════════════════
const R = 28;
const SW = 880, SH = 490;
const PAL = ["#1a1a2e","#e85d04","#d62828","#1d6fa3","#2d6a4f","#7209b7","#b5838d"];

const d2 = (x1,y1,x2,y2) => Math.sqrt((x2-x1)**2+(y2-y1)**2);

const symColor = (sym,alph) => {
  if (!sym || sym === "ε") return "#6c757d";
  const i = alph.indexOf(sym);
  return i >= 0 ? PAL[(i+1) % PAL.length] : PAL[0];
};

const circleEdgePt = (cx,cy,tx,ty,r) => {
  const l = d2(cx,cy,tx,ty) || 1;
  return [cx + r*(tx-cx)/l, cy + r*(ty-cy)/l];
};

/**
 * Calculate SVG path geometry for an edge.
 * Receives allStates to detect intermediate states that lie on the straight
 * line from→to and arcs around them automatically.
 */
function calcEdgeGeom(from, to, hasBidir, allStates = []) {
  const { x:fx, y:fy } = from, { x:tx, y:ty } = to;

  // ── Self-loop ──────────────────────────────────────────
  if (from.id === to.id) {
    const [sx,sy] = [fx-16, fy-R+3];
    const [ex,ey] = [fx+16, fy-R+3];
    const [c1x,c1y] = [fx-62, fy-R-68];
    const [c2x,c2y] = [fx+62, fy-R-68];
    return {
      d: `M${sx},${sy} C${c1x},${c1y} ${c2x},${c2y} ${ex},${ey}`,
      ax:ex, ay:ey, aAngle: Math.atan2(ey-c2y, ex-c2x),
      lx:fx, ly:fy-R-50,
    };
  }

  const dx = tx-fx, dy = ty-fy;
  const len = Math.sqrt(dx*dx + dy*dy) || 1;
  const nx = -dy/len, ny = dx/len; // unit perpendicular (left of from→to)

  // ── Detect intermediate blocking states ────────────────
  const CLEAR = R + 26;
  let maxBlockLeft = 0, maxBlockRight = 0;

  for (const s of allStates) {
    if (s.id === from.id || s.id === to.id) continue;
    const t = ((s.x-fx)*dx + (s.y-fy)*dy) / (len*len);
    if (t < 0.08 || t > 0.92) continue;
    const signedDist = (dx*(s.y-fy) - dy*(s.x-fx)) / len;
    const absDist = Math.abs(signedDist);
    if (absDist < CLEAR) {
      const needed = CLEAR - absDist + R + 8;
      if (signedDist >= 0) maxBlockLeft  = Math.max(maxBlockLeft,  needed);
      else                 maxBlockRight = Math.max(maxBlockRight, needed);
    }
  }

  // ── Perpendicular offset: positive = left, negative = right ──
  let off;
  if (maxBlockLeft > 0 || maxBlockRight > 0) {
    if (maxBlockLeft >= maxBlockRight) off = -(maxBlockLeft + 12);
    else                               off =  maxBlockRight + 12;
    if (hasBidir) off = off < 0 ? Math.min(off, -52) : Math.max(off, 52);
  } else {
    off = hasBidir ? 46 : 0;
  }

  const [mx,my] = [(fx+tx)/2 + nx*off, (fy+ty)/2 + ny*off];
  const [sx,sy] = circleEdgePt(fx,fy,mx,my,R);
  const [ex,ey] = circleEdgePt(tx,ty,mx,my,R);
  return {
    d: `M${sx},${sy} Q${mx},${my} ${ex},${ey}`,
    ax:ex, ay:ey, aAngle: Math.atan2(ey-my, ex-mx),
    lx: 0.25*sx+0.5*mx+0.25*ex,
    ly: 0.25*sy+0.5*my+0.25*ey,
  };
}

function Arrowhead({ x, y, angle, color, sz=9 }) {
  const c = Math.cos(angle), s = Math.sin(angle);
  const pts = [
    [x,y],
    [x-sz*c+sz*.44*s, y-sz*s-sz*.44*c],
    [x-sz*c-sz*.44*s, y-sz*s+sz*.44*c],
  ].map(p => p.join(",")).join(" ");
  return <polygon points={pts} fill={color} />;
}

// ═══════════════════════════════════════════════════════
// Demo automaton (DFA: accepts strings ending in 'b')
// ═══════════════════════════════════════════════════════
const DEMO = {
  states: [
    {id:"q0",x:160,y:245,accept:false},
    {id:"q1",x:440,y:245,accept:true},
    {id:"q2",x:700,y:245,accept:false},
  ],
  edges: [
    {id:"e1",from:"q0",to:"q1",symbols:["b"]},
    {id:"e2",from:"q0",to:"q0",symbols:["a"]},
    {id:"e3",from:"q1",to:"q1",symbols:["b"]},
    {id:"e4",from:"q1",to:"q2",symbols:["a"]},
    {id:"e5",from:"q2",to:"q1",symbols:["b"]},
    {id:"e6",from:"q2",to:"q0",symbols:["a"]},
  ],
  startId: "q0",
};

let _uid = 100;
const uid = () => `${++_uid}`;

// ═══════════════════════════════════════════════════════
// Editor
// ═══════════════════════════════════════════════════════
export default function AutomataEditor({ args = {} }) {
  const [states, setStates]     = useState(DEMO.states.map(s=>({...s})));
  const [edges, setEdges]       = useState(DEMO.edges.map(e=>({...e})));
  const [startId, setStartId]   = useState(DEMO.startId);
  const [type, setType]         = useState("DFA");
  const [alphaStr, setAlphaStr] = useState("a,b");
  const [mode, setMode]         = useState("pointer");

  const [movingSt, setMovingSt] = useState(null);
  const [drawEdge, setDrawEdge] = useState(null);

  const [ctxMenu, setCtxMenu]     = useState(null);
  const [edgeEdit, setEdgeEdit]   = useState(null);
  const [edgeInput, setEdgeInput] = useState("");
  const [copied, setCopied]       = useState(false);

  const [simStr, setSimStr]       = useState("ab");
  const [simActive, setSimActive] = useState(false);
  const [simPos, setSimPos]       = useState(0);
  const [simCurr, setSimCurr]     = useState(new Set());
  const [showJSON, setShowJSON]   = useState(false);

  const svgRef  = useRef(null);
  const qNumRef = useRef(3);

  const alph = useMemo(
    () => alphaStr.split(",").map(s=>s.trim()).filter(Boolean),
    [alphaStr]
  );

  // Sync props from Streamlit
  useEffect(() => {
    if (args?.automaton_type === "DFA" || args?.automaton_type === "NFA")
      setType(args.automaton_type);
    if (Array.isArray(args?.alphabet))
      setAlphaStr(args.alphabet.join(","));
  }, [args]);

  // ─── helpers ───────────────────────────────────────────
  const getSVGXY = useCallback(e => {
    const r = svgRef.current?.getBoundingClientRect();
    if (!r) return {x:0,y:0};
    return { x: e.clientX-r.left, y: e.clientY-r.top };
  }, []);

  const stateAt = useCallback((x,y) =>
    states.find(s => d2(s.x,s.y,x,y) < R+6)
  , [states]);

  const addState = useCallback((x,y) => {
    let fx = x, fy = y;
    const TOO_CLOSE = R*2 + 10;
    let attempts = 0;
    while (attempts < 20 && states.some(s => d2(s.x,s.y,fx,fy) < TOO_CLOSE)) {
      fx += 72; attempts++;
      if (fx > SW - R - 20) { fx = R + 40; fy += 80; }
    }
    const id = `q${qNumRef.current++}`;
    setStates(prev => [...prev, {id, x:fx, y:fy, accept:false}]);
    setStartId(prev => prev || id);
  }, [states]);

  // ─── canvas events ─────────────────────────────────────
  const handleCanvasMouseMove = useCallback(e => {
    const {x,y} = getSVGXY(e);
    if (movingSt)
      setStates(prev => prev.map(s =>
        s.id===movingSt.id ? {...s, x:x-movingSt.ox, y:y-movingSt.oy} : s
      ));
    if (drawEdge) setDrawEdge(p => p ? {...p,mx:x,my:y} : null);
  }, [movingSt, drawEdge, getSVGXY]);

  const handleCanvasMouseUp = useCallback(e => {
    const {x,y} = getSVGXY(e);
    setMovingSt(null);
    if (drawEdge) {
      const hit = stateAt(x,y);
      if (hit) {
        const existing = edges.find(ed=>ed.from===drawEdge.fromId&&ed.to===hit.id);
        const fromS = states.find(s=>s.id===drawEdge.fromId);
        const px = fromS&&hit ? (fromS.x+hit.x)/2 : x;
        const py = fromS&&hit ? (fromS.y+hit.y)/2-30 : y;
        if (!existing) {
          const ne = {id:`e${uid()}`,from:drawEdge.fromId,to:hit.id,symbols:[]};
          setEdges(prev => [...prev,ne]);
          setEdgeEdit({edgeId:ne.id, x:px, y:py});
          setEdgeInput("");
        } else {
          setEdgeEdit({edgeId:existing.id, x:px, y:py});
          setEdgeInput((existing.symbols||[]).join(","));
        }
      }
      setDrawEdge(null);
    }
  }, [drawEdge, getSVGXY, stateAt, edges, states]);

  const handleCanvasClick = useCallback(e => {
    if (mode === "addState") {
      const {x,y} = getSVGXY(e);
      if (!stateAt(x,y)) addState(x,y);
    }
    setCtxMenu(null);
  }, [mode, getSVGXY, stateAt, addState]);

  const handleCanvasDblClick = useCallback(e => {
    if (mode === "pointer") {
      const {x,y} = getSVGXY(e);
      if (!stateAt(x,y)) addState(x,y);
    }
  }, [mode, getSVGXY, stateAt, addState]);

  // ─── state events ──────────────────────────────────────
  const handleStateMouseDown = useCallback((e, sid) => {
    e.stopPropagation();
    if (e.button!==0) return;
    const {x,y} = getSVGXY(e);
    if (mode==="pointer") {
      const s = states.find(st=>st.id===sid);
      if (s) setMovingSt({id:sid, ox:x-s.x, oy:y-s.y});
    } else if (mode==="addTransition") {
      setDrawEdge({fromId:sid, mx:x, my:y});
    }
  }, [mode, states, getSVGXY]);

  const handleStateClick = useCallback((e, sid) => {
    e.stopPropagation();
    if (mode==="delete") {
      setStates(prev=>prev.filter(s=>s.id!==sid));
      setEdges(prev=>prev.filter(ed=>ed.from!==sid&&ed.to!==sid));
      setStartId(prev=>prev===sid?null:prev);
    }
    setCtxMenu(null);
  }, [mode]);

  const handleStateDblClick = useCallback((e, sid) => {
    e.stopPropagation();
    setStates(prev=>prev.map(s=>s.id===sid?{...s,accept:!s.accept}:s));
  }, []);

  const handleStateCtxMenu = useCallback((e, sid) => {
    e.preventDefault();
    e.stopPropagation();
    const {x,y} = getSVGXY(e);
    setCtxMenu({x,y,stateId:sid});
  }, [getSVGXY]);

  // ─── edge events ───────────────────────────────────────
  const handleEdgeClick = useCallback((e, eid) => {
    e.stopPropagation();
    if (mode==="delete") {
      setEdges(prev=>prev.filter(ed=>ed.id!==eid));
      return;
    }
    const edge = edges.find(ed=>ed.id===eid);
    if (!edge) return;
    const fromS = states.find(s=>s.id===edge.from);
    const toS   = states.find(s=>s.id===edge.to);
    const lx = fromS&&toS ? (fromS.id===toS.id?fromS.x:(fromS.x+toS.x)/2) : 200;
    const ly = fromS&&toS ? (fromS.id===toS.id?fromS.y-R-55:(fromS.y+toS.y)/2-30) : 200;
    setEdgeEdit({edgeId:eid, x:lx, y:ly});
    setEdgeInput((edge.symbols||[]).join(","));
  }, [mode, edges, states]);

  // ─── context menu ──────────────────────────────────────
  const ctxAction = useCallback(action => {
    if (!ctxMenu) return;
    const {stateId} = ctxMenu;
    if (action==="setStart")    setStartId(stateId);
    else if (action==="accept") setStates(p=>p.map(s=>s.id===stateId?{...s,accept:!s.accept}:s));
    else if (action==="delete") {
      setStates(p=>p.filter(s=>s.id!==stateId));
      setEdges(p=>p.filter(ed=>ed.from!==stateId&&ed.to!==stateId));
      setStartId(p=>p===stateId?null:p);
    }
    setCtxMenu(null);
  }, [ctxMenu]);

  // ─── edge label save ───────────────────────────────────
  const saveEdgeLabel = useCallback(() => {
    if (!edgeEdit) return;
    const syms = edgeInput.split(",").map(s=>{
      const t = s.trim();
      if (["eps","epsilon","λ"].includes(t.toLowerCase())) return "ε";
      return t;
    }).filter(Boolean);
    setEdges(p=>p.map(e=>e.id===edgeEdit.edgeId?{...e,symbols:syms}:e));
    setEdgeEdit(null);
  }, [edgeEdit, edgeInput]);

  // ─── simulation ────────────────────────────────────────
  const epsClosure = useCallback(ids => {
    const r = new Set(ids);
    let changed = true;
    while (changed) {
      changed = false;
      for (const e of edges) {
        if (r.has(e.from) && e.symbols.includes("ε") && !r.has(e.to)) {
          r.add(e.to); changed = true;
        }
      }
    }
    return r;
  }, [edges]);

  const doSimStep = useCallback(() => {
    if (simPos >= simStr.length) return;
    const sym = simStr[simPos];
    const next = new Set();
    for (const e of edges) {
      if (simCurr.has(e.from) && e.symbols.includes(sym)) next.add(e.to);
    }
    setSimCurr(epsClosure(next));
    setSimPos(p=>p+1);
  }, [simPos, simStr, simCurr, edges, epsClosure]);

  const startSim = useCallback(() => {
    if (!startId) return;
    setSimCurr(epsClosure(new Set([startId])));
    setSimPos(0);
    setSimActive(true);
  }, [startId, epsClosure]);

  const resetSim = useCallback(() => {
    setSimActive(false); setSimPos(0); setSimCurr(new Set());
  }, []);

  const runAllSim = useCallback(() => {
    if (!startId) return;
    let curr = epsClosure(new Set([startId]));
    for (const sym of simStr) {
      const next = new Set();
      for (const e of edges) {
        if (curr.has(e.from) && e.symbols.includes(sym)) next.add(e.to);
      }
      curr = epsClosure(next);
    }
    setSimCurr(curr);
    setSimPos(simStr.length);
    setSimActive(true);
  }, [startId, simStr, edges, epsClosure]);

  const simDone     = simActive && simPos >= simStr.length;
  const simAccepted = simDone && states.some(s => s.accept && simCurr.has(s.id));

  // ─── JSON export ───────────────────────────────────────
  const exportJSON = useMemo(() => {
    const ids    = states.map(s=>s.id);
    const finals = states.filter(s=>s.accept).map(s=>s.id);
    if (type==="DFA") {
      const tr = {}; ids.forEach(id=>(tr[id]={}));
      edges.forEach(e=>e.symbols.forEach(sym=>{
        if (sym&&sym!=="ε") tr[e.from][sym]=e.to;
      }));
      return {states:ids,input_symbols:alph,transitions:tr,initial_state:startId||"",final_states:finals};
    } else {
      const tr = {}; ids.forEach(id=>(tr[id]={}));
      edges.forEach(e=>e.symbols.forEach(sym=>{
        const k=sym==="ε"?"":sym;
        if(!tr[e.from][k]) tr[e.from][k]=[];
        if(!tr[e.from][k].includes(e.to)) tr[e.from][k].push(e.to);
      }));
      return {states:ids,input_symbols:alph,transitions:tr,initial_state:startId||"",final_states:finals};
    }
  }, [states,edges,startId,alph,type]);

  // Push JSON to Streamlit debounced on every change
  useEffect(() => {
    const t = setTimeout(() => {
      Streamlit.setComponentValue(exportJSON);
      Streamlit.setFrameHeight();
    }, 800);
    return () => clearTimeout(t);
  }, [exportJSON]);

  useEffect(() => { Streamlit.setFrameHeight(); });

  // ─── edge rendering ────────────────────────────────────
  const renderedEdges = useMemo(() => edges.map(edge => {
    const from = states.find(s=>s.id===edge.from);
    const to   = states.find(s=>s.id===edge.to);
    if (!from||!to) return null;
    const hasBidir = edges.some(e=>e.from===edge.to&&e.to===edge.from);
    const geom  = calcEdgeGeom(from, to, hasBidir, states);
    const color = edge.symbols.length>0 ? symColor(edge.symbols[0],alph) : "#bbb";
    const lbl   = edge.symbols.length>0 ? edge.symbols.join(", ") : "?";
    const isEps = edge.symbols.includes("ε");
    return {edge,from,to,geom,color,lbl,isEps};
  }).filter(Boolean), [edges,states,alph]);

  // ═══════════════════════════════════════════════════════
  // Light-mode design tokens
  // ═══════════════════════════════════════════════════════
  const C = {
    // Surfaces
    bg:          "#f8fafc",   // page background
    surface:     "#ffffff",   // card / panel surface
    surfaceAlt:  "#f1f5f9",   // slightly darker surface (inputs, simulation panel)
    border:      "#e2e8f0",   // default border
    borderStrong:"#cbd5e1",   // stronger border / divider

    // Text
    textPrimary:  "#1e293b",  // headings, labels
    textSecondary:"#475569",  // body text, descriptions
    textMuted:    "#94a3b8",  // placeholder, metadata

    // Brand / interactive
    accent:      "#2563eb",   // primary action blue
    accentLight: "#eff6ff",   // light accent bg (active pill)
    accentBorder:"#bfdbfe",   // light accent border
    accentText:  "#1d4ed8",   // darker blue for text on light bg

    // Danger
    danger:      "#dc2626",
    dangerLight: "#fef2f2",

    // Simulation
    simAcceptBg: "#f0fdf4",
    simAcceptText:"#15803d",
    simAcceptBorder:"#86efac",
    simRejectBg:  "#fef2f2",
    simRejectText:"#b91c1c",
    simRejectBorder:"#fca5a5",
  };

  const S = {
    root: {
      fontFamily:'"IBM Plex Mono","JetBrains Mono","Courier New",monospace',
      background: C.bg,
      minHeight: "100vh",
      padding: 16,
      color: C.textPrimary,
      boxSizing: "border-box",
    },
    row: { display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" },
    pill: active => ({
      display:"flex", alignItems:"center", gap:5,
      padding:"7px 14px", borderRadius:8,
      border: active ? `1.5px solid ${C.accentBorder}` : `1.5px solid ${C.border}`,
      background: active ? C.accentLight : C.surface,
      color: active ? C.accentText : C.textSecondary,
      fontFamily:"inherit", fontSize:13,
      fontWeight: active ? 700 : 400,
      cursor:"pointer",
      boxShadow: active ? `0 0 0 3px ${C.accentBorder}` : "0 1px 2px rgba(0,0,0,.06)",
      transition:"all .12s",
    }),
    input: {
      padding:"6px 10px", borderRadius:7, fontFamily:"inherit", fontSize:13,
      background: C.surface,
      color: C.textPrimary,
      border: `1.5px solid ${C.border}`,
      outline:"none",
    },
    panel: {
      marginTop:12, padding:14,
      background: C.surface,
      borderRadius:12,
      border: `1px solid ${C.border}`,
      boxShadow:"0 1px 4px rgba(0,0,0,.06)",
    },
    label: {
      fontSize:12, color: C.textMuted, fontWeight:600,
      letterSpacing:".04em", textTransform:"uppercase",
    },
  };

  const MODES = [
    {id:"pointer",       icon:"↖", label:"Select/Move",  tip:"Drag states to move  •  Double-click canvas to add a state  •  Double-click a state to toggle accept"},
    {id:"addState",      icon:"⊕", label:"Add State",    tip:"Click anywhere on the canvas to place a new state"},
    {id:"addTransition", icon:"⟶", label:"Transition",   tip:"Drag from one state to another to draw a transition  •  Drag a state onto itself for a self-loop"},
    {id:"delete",        icon:"✕", label:"Delete",       tip:"Click any state or transition label to remove it"},
  ];

  return (
    <div style={S.root}>

      {/* ── Header ── */}
      <div style={{...S.row, marginBottom:12}}>
        <span style={{fontSize:18,fontWeight:800,letterSpacing:"-1px",color:C.textPrimary}}>
          ⟨Q,Σ,δ,q₀,F⟩
        </span>
        <span style={{fontSize:12, color:C.textMuted, flex:1, fontWeight:500}}>
          Automata Editor
        </span>
        <div style={{...S.row, gap:8}}>
          <span style={S.label}>Type</span>
          <select value={type} onChange={e=>setType(e.target.value)}
            style={{...S.input, cursor:"pointer", paddingRight:8}}>
            <option>DFA</option><option>NFA</option>
          </select>
          <span style={S.label}>Σ =</span>
          <input value={alphaStr} onChange={e=>setAlphaStr(e.target.value)}
            style={{...S.input, width:100}} placeholder="a,b,c"/>
        </div>
        <button onClick={()=>{
          setStates(DEMO.states.map(s=>({...s})));
          setEdges(DEMO.edges.map(e=>({...e})));
          setStartId(DEMO.startId); qNumRef.current=3; resetSim();
        }} style={{
          ...S.pill(false), fontSize:11, padding:"5px 10px",
          color:C.textSecondary,
        }}>
          Load Demo
        </button>
        <button onClick={()=>{
          setStates([]); setEdges([]); setStartId(null); qNumRef.current=0; resetSim();
        }} style={{
          ...S.pill(false), fontSize:11, padding:"5px 10px",
          color:C.danger, borderColor:"#fecaca",
        }}>
          Clear
        </button>
      </div>

      {/* ── Toolbar ── */}
      <div style={{...S.row, marginBottom:8}}>
        {MODES.map(m=>(
          <button key={m.id} onClick={()=>setMode(m.id)} title={m.tip}
            style={S.pill(mode===m.id)}>
            <span style={{fontSize:15,lineHeight:1}}>{m.icon}</span> {m.label}
          </button>
        ))}
        <div style={{
          flex:1, fontSize:11, color: C.textSecondary,
          padding:"6px 10px",
          background: C.accentLight,
          borderRadius:8,
          border:`1px solid ${C.accentBorder}`,
        }}>
          {MODES.find(m=>m.id===mode)?.tip}
        </div>
      </div>

      {/* ── SVG Canvas (unchanged) ── */}
      <div style={{position:"relative", lineHeight:0}}>
        <svg ref={svgRef} width={SW} height={SH}
          style={{
            display:"block", background:"#f8fafc",
            borderRadius:12, border:`2px solid ${C.borderStrong}`,
            cursor: mode==="addState"?"crosshair":mode==="delete"?"no-drop":"default",
          }}
          onMouseMove={handleCanvasMouseMove}
          onMouseUp={handleCanvasMouseUp}
          onClick={handleCanvasClick}
          onDoubleClick={handleCanvasDblClick}
        >
          <defs>
            <pattern id="dg" width="28" height="28" patternUnits="userSpaceOnUse">
              <circle cx="1.5" cy="1.5" r="1.2" fill="#dde4ef"/>
            </pattern>
            <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="4" result="b"/>
              <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width={SW} height={SH} fill="url(#dg)"/>

          {/* Edges */}
          {renderedEdges.map(({edge,geom,color,lbl,isEps})=>{
            const isActive = simActive && (simCurr.has(edge.from)||simCurr.has(edge.to));
            return (
              <g key={edge.id}>
                <path d={geom.d} fill="none" stroke="transparent" strokeWidth={20}
                  onClick={e=>handleEdgeClick(e,edge.id)}
                  style={{cursor:mode==="delete"?"no-drop":"pointer"}}/>
                <path d={geom.d} fill="none"
                  stroke={isActive?"#3b82f6":color} strokeWidth={isActive?3:2.2}
                  strokeDasharray={isEps?"7 4":undefined}
                  style={{pointerEvents:"none"}}/>
                <Arrowhead x={geom.ax} y={geom.ay} angle={geom.aAngle}
                  color={isActive?"#3b82f6":color}/>
                <rect x={geom.lx-24} y={geom.ly-12} width={48} height={24} rx={6}
                  fill="white" fillOpacity={0.95}
                  stroke={isActive?"#3b82f6":color} strokeWidth={1.5}
                  onClick={e=>handleEdgeClick(e,edge.id)}
                  style={{cursor:"pointer"}}/>
                <text x={geom.lx} y={geom.ly+5} textAnchor="middle"
                  fill={isActive?"#2563eb":color} fontSize={12} fontWeight="bold"
                  style={{pointerEvents:"none",userSelect:"none",fontFamily:"inherit"}}>
                  {lbl}
                </text>
              </g>
            );
          })}

          {/* Ghost edge while drawing */}
          {drawEdge&&(()=>{
            const fromS = states.find(s=>s.id===drawEdge.fromId);
            if (!fromS) return null;
            const [sx,sy] = circleEdgePt(fromS.x,fromS.y,drawEdge.mx,drawEdge.my,R);
            const ang = Math.atan2(drawEdge.my-sy, drawEdge.mx-sx);
            return (
              <g style={{pointerEvents:"none"}}>
                <line x1={sx} y1={sy} x2={drawEdge.mx} y2={drawEdge.my}
                  stroke="#3b82f6" strokeWidth={2} strokeDasharray="7 3"/>
                <Arrowhead x={drawEdge.mx} y={drawEdge.my} angle={ang} color="#3b82f6" sz={8}/>
              </g>
            );
          })()}

          {/* Start-state entry arrow */}
          {startId&&(()=>{
            const s = states.find(st=>st.id===startId);
            if (!s) return null;
            return (
              <g style={{pointerEvents:"none"}}>
                <line x1={s.x-70} y1={s.y} x2={s.x-R-1} y2={s.y}
                  stroke="#1a1a2e" strokeWidth={2.5}/>
                <Arrowhead x={s.x-R-1} y={s.y} angle={0} color="#1a1a2e"/>
              </g>
            );
          })()}

          {/* States */}
          {states.map(state=>{
            const isCurr     = simActive && simCurr.has(state.id);
            const isAccepted = simDone && state.accept && simCurr.has(state.id);
            let fill="#fff", stroke="#1e293b", sw=2.5;
            if (state.accept)                 { fill="#eff6ff"; }
            if (isCurr&&!simDone)             { fill="#dbeafe"; stroke="#3b82f6"; sw=3.5; }
            if (isAccepted)                   { fill="#dcfce7"; stroke="#16a34a"; sw=3.5; }
            if (simDone&&isCurr&&!isAccepted) { fill="#fee2e2"; stroke="#dc2626"; sw=3; }
            return (
              <g key={state.id}
                onMouseDown={e=>handleStateMouseDown(e,state.id)}
                onClick={e=>handleStateClick(e,state.id)}
                onDoubleClick={e=>handleStateDblClick(e,state.id)}
                onContextMenu={e=>handleStateCtxMenu(e,state.id)}
                style={{cursor:mode==="pointer"?"grab":mode==="addTransition"?"crosshair":mode==="delete"?"no-drop":"default"}}>
                <circle cx={state.x} cy={state.y} r={R}
                  fill={fill} stroke={stroke} strokeWidth={sw}
                  filter={(isCurr||isAccepted)?"url(#glow)":undefined}/>
                {state.accept&&(
                  <circle cx={state.x} cy={state.y} r={R-7}
                    fill="none" stroke={stroke} strokeWidth={1.5}/>
                )}
                <text x={state.x} y={state.y+5} textAnchor="middle"
                  fill={stroke} fontSize={13} fontWeight="bold"
                  style={{pointerEvents:"none",userSelect:"none",fontFamily:"inherit"}}>
                  {state.id}
                </text>
              </g>
            );
          })}
        </svg>

        {/* ── Context Menu ── */}
        {ctxMenu&&(
          <div onClick={e=>e.stopPropagation()} style={{
            position:"absolute", left:ctxMenu.x, top:ctxMenu.y,
            background: C.surface,
            border:`1px solid ${C.border}`,
            borderRadius:10,
            boxShadow:"0 8px 24px rgba(0,0,0,.12)",
            zIndex:200, minWidth:210, overflow:"hidden",
          }}>
            {(()=>{
              const st = states.find(s=>s.id===ctxMenu.stateId);
              return [
                {a:"setStart", label:`→  Set "${ctxMenu.stateId}" as start state`},
                {a:"accept",   label: st?.accept ? `◯  Remove accept state` : `◎  Make accept state`},
                {a:"delete",   label:`✕  Delete "${ctxMenu.stateId}"`, danger:true},
              ].map(({a,label,danger})=>(
                <button key={a} onClick={()=>ctxAction(a)} style={{
                  display:"block", width:"100%", padding:"10px 14px",
                  textAlign:"left", border:"none",
                  background:"none", cursor:"pointer",
                  fontSize:12, fontFamily:"inherit",
                  color: danger ? C.danger : C.textPrimary,
                  borderBottom:`1px solid ${C.border}`,
                }}
                  onMouseEnter={e=>{e.currentTarget.style.background=C.surfaceAlt}}
                  onMouseLeave={e=>{e.currentTarget.style.background="none"}}>
                  {label}
                </button>
              ));
            })()}
          </div>
        )}

        {/* ── Edge Label Popup ── */}
        {edgeEdit&&(
          <div onClick={e=>e.stopPropagation()} style={{
            position:"absolute",
            left: Math.min(Math.max(edgeEdit.x-100, 4), SW-220),
            top:  Math.max(edgeEdit.y-140, 4),
            background: C.surface,
            border:`2px solid ${C.accentBorder}`,
            borderRadius:12,
            boxShadow:"0 8px 28px rgba(37,99,235,.15)",
            padding:"13px 15px", zIndex:300, minWidth:215,
          }}>
            <div style={{
              fontSize:10, fontWeight:700, color:C.accentText,
              letterSpacing:".1em", textTransform:"uppercase", marginBottom:8,
            }}>
              Transition Symbols
            </div>
            <input autoFocus value={edgeInput}
              onChange={e=>setEdgeInput(e.target.value)}
              onKeyDown={e=>{if(e.key==="Enter")saveEdgeLabel();if(e.key==="Escape")setEdgeEdit(null);}}
              placeholder="e.g.  a,b  or  ε"
              style={{
                ...S.input, width:"100%",
                border:`1.5px solid ${C.accentBorder}`,
                boxSizing:"border-box", marginBottom:8,
              }}
            />
            {/* Alphabet quick-insert buttons */}
            <div style={{display:"flex",gap:5,flexWrap:"wrap",marginBottom:10}}>
              {alph.map(sym=>(
                <button key={sym}
                  onClick={()=>setEdgeInput(v=>v?v+","+sym:sym)}
                  style={{
                    padding:"3px 9px", borderRadius:6, fontFamily:"inherit",
                    fontSize:12, fontWeight:700, cursor:"pointer",
                    background: C.surface,
                    border:`2px solid ${symColor(sym,alph)}`,
                    color: symColor(sym,alph),
                  }}>{sym}</button>
              ))}
              {type==="NFA"&&(
                <button onClick={()=>setEdgeInput(v=>v?v+",ε":"ε")}
                  style={{
                    padding:"3px 9px", borderRadius:6, fontFamily:"inherit",
                    fontSize:12, fontWeight:700, cursor:"pointer",
                    background: C.surface,
                    border:"2px solid #6c757d", color:"#6c757d",
                  }}>ε</button>
              )}
            </div>
            <div style={{display:"flex",gap:6}}>
              <button onClick={saveEdgeLabel} style={{
                flex:1, padding:"7px", background:C.accent, color:"white",
                border:"none", borderRadius:7, cursor:"pointer",
                fontFamily:"inherit", fontSize:12, fontWeight:700,
              }}>✓ Save  [Enter]</button>
              <button onClick={()=>setEdgeEdit(null)} style={{
                flex:1, padding:"7px",
                background:C.surfaceAlt, color:C.textSecondary,
                border:`1px solid ${C.border}`,
                borderRadius:7, cursor:"pointer", fontFamily:"inherit", fontSize:12,
              }}>Cancel  [Esc]</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Legend ── */}
      <div style={{
        display:"flex", gap:16, marginTop:8, flexWrap:"wrap",
        alignItems:"center", fontSize:12, color:C.textSecondary,
      }}>
        <span style={{color:C.textPrimary}}>◯ normal state</span>
        <span style={{color:C.textPrimary, fontWeight:700}}>
          ◎ accept state
          <span style={{fontWeight:400, color:C.textMuted, marginLeft:5}}>
            (double-click to toggle)
          </span>
        </span>
        <span style={{color:C.textPrimary}}>→ start state</span>
        {type==="NFA"&&(
          <span style={{color:C.textMuted}}>- - - ε-transition</span>
        )}
        {alph.map((sym,i)=>(
          <span key={sym} style={{color:PAL[(i+1)%PAL.length],fontWeight:700}}>── {sym}</span>
        ))}
        <span style={{marginLeft:"auto", color:C.textMuted, fontSize:11}}>
          Right-click any state for options
        </span>
      </div>

      {/* ── Simulation Panel ── */}
      <div style={S.panel}>
        <div style={{
          fontSize:11, fontWeight:700, color:C.accentText,
          letterSpacing:".06em", textTransform:"uppercase", marginBottom:10,
        }}>
          ▷ String Simulation
        </div>
        <div style={{...S.row, gap:8}}>
          <input value={simStr} onChange={e=>setSimStr(e.target.value)}
            disabled={simActive} placeholder="e.g. aabb"
            style={{
              ...S.input, width:160,
              background: simActive ? C.surfaceAlt : C.surface,
              color: simActive ? C.textMuted : C.textPrimary,
            }}/>
          {!simActive?(
            <button onClick={startSim} disabled={!startId}
              style={{
                padding:"7px 16px",
                background: startId ? C.accent : C.surfaceAlt,
                color: startId ? "white" : C.textMuted,
                border:"none", borderRadius:8,
                cursor: startId ? "pointer" : "default",
                fontFamily:"inherit", fontWeight:700, fontSize:13,
              }}>▶ Start</button>
          ):(
            <>
              <button onClick={doSimStep} disabled={simPos>=simStr.length}
                style={{
                  padding:"7px 14px",
                  background: simPos<simStr.length ? C.accent : C.surfaceAlt,
                  color: simPos<simStr.length ? "white" : C.textMuted,
                  border:"none", borderRadius:8,
                  cursor: simPos<simStr.length ? "pointer" : "default",
                  fontFamily:"inherit", fontWeight:700, fontSize:13,
                }}>Step →</button>
              <button onClick={runAllSim} disabled={simPos>=simStr.length}
                style={{
                  padding:"7px 14px",
                  background: simPos<simStr.length ? C.accentLight : C.surfaceAlt,
                  color: simPos<simStr.length ? C.accentText : C.textMuted,
                  border: `1px solid ${simPos<simStr.length ? C.accentBorder : C.border}`,
                  borderRadius:8,
                  cursor: simPos<simStr.length ? "pointer" : "default",
                  fontFamily:"inherit", fontSize:13,
                }}>Run All ⏩</button>
              <button onClick={resetSim} style={{
                padding:"7px 12px",
                background: C.surfaceAlt, color: C.textSecondary,
                border:`1px solid ${C.border}`,
                borderRadius:8, cursor:"pointer", fontFamily:"inherit", fontSize:13,
              }}>⟳ Reset</button>
            </>
          )}
          {simDone&&(
            <span style={{
              padding:"5px 14px", borderRadius:20, fontWeight:700, fontSize:13,
              background: simAccepted ? C.simAcceptBg : C.simRejectBg,
              color:       simAccepted ? C.simAcceptText : C.simRejectText,
              border:`1.5px solid ${simAccepted ? C.simAcceptBorder : C.simRejectBorder}`,
            }}>
              {simAccepted ? "✓ ACCEPTED" : "✗ REJECTED"}
            </span>
          )}
        </div>

        {/* Tape display */}
        {simActive&&simStr.length>0&&(
          <div style={{marginTop:8,display:"flex",gap:3,flexWrap:"wrap",alignItems:"center"}}>
            <span style={{fontSize:11,color:C.textMuted,marginRight:4}}>tape:</span>
            {simStr.split("").map((ch,i)=>(
              <span key={i} style={{
                display:"inline-block", padding:"3px 8px", borderRadius:5,
                background: i<simPos ? C.accentLight : i===simPos ? C.accent : C.surfaceAlt,
                color:       i<simPos ? C.accentText  : i===simPos ? "white"  : C.textMuted,
                border:`1px solid ${i===simPos ? C.accent : C.border}`,
                fontWeight: i===simPos ? 700 : 400,
                fontSize:14, transition:"all .15s",
              }}>{ch}</span>
            ))}
            <span style={{marginLeft:4,fontSize:11,color:C.textMuted}}>
              ({simPos}/{simStr.length})
            </span>
          </div>
        )}
        {simActive&&(
          <div style={{marginTop:6,fontSize:11,color:C.textMuted}}>
            Active states:{" "}
            <span style={{color:C.accentText, fontWeight:700}}>
              {[...simCurr].length>0 ? [...simCurr].join(", ") : "∅"}
            </span>
          </div>
        )}
      </div>

      {/* ── JSON Export ── */}
      <div style={{marginTop:10}}>
        <button onClick={()=>setShowJSON(p=>!p)} style={{
          padding:"7px 16px",
          background: C.surface, color: C.textSecondary,
          border:`1px solid ${C.border}`,
          borderRadius:8, cursor:"pointer",
          fontFamily:"inherit", fontSize:13,
          boxShadow:"0 1px 2px rgba(0,0,0,.05)",
        }}>
          {showJSON?"▲":"▼"} Export JSON{" "}
          <span style={{color:C.textMuted,fontSize:11}}>
            (paste into CS474 Auto-Explainers)
          </span>
        </button>
        {showJSON&&(
          <div style={{marginTop:8,position:"relative"}}>
            <pre style={{
              background:"#1e293b", color:"#7dd3fc",
              padding:16, borderRadius:10,
              fontSize:12, overflow:"auto", maxHeight:280,
              fontFamily:"inherit", border:`1px solid ${C.borderStrong}`, margin:0,
            }}>
              {JSON.stringify(exportJSON,null,2)}
            </pre>
            <button onClick={()=>{
              navigator.clipboard.writeText(JSON.stringify(exportJSON,null,2));
              Streamlit.setComponentValue(exportJSON);
              setCopied(true);
              setTimeout(()=>setCopied(false),2000);
            }} style={{
              position:"absolute", top:8, right:8,
              padding:"4px 10px",
              background: C.accentLight, color: C.accentText,
              border:`1px solid ${C.accentBorder}`,
              borderRadius:6, cursor:"pointer",
              fontSize:11, fontFamily:"inherit",
            }}>
              {copied ? "✓ Copied!" : "Copy JSON"}
            </button>
          </div>
        )}
      </div>

    </div>
  );
}