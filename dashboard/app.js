(() => {
  const fallback = window.FALLBACK_DATA || {metadata:{},players:[]};
  let data = fallback, role = "all", sortKey = "pressure_score", ascending = false, radar;
  const $ = id => document.getElementById(id);
  const keyOutput = p => p.key_stats || (p.role === "Batter" ? `Pressure shortlist rank ${p.rank}` : `Pressure shortlist rank ${p.rank}`);
  function setLoading(done){$("loadingScreen").classList.toggle("is-hidden",done); document.body.classList.toggle("is-loading",!done)}
  async function load(){
    setLoading(false);
    try{
      const controller=new AbortController();
      const timeout=setTimeout(()=>controller.abort(),2500);
      try{
        const r=await fetch("../dashboard_data.json",{signal:controller.signal});
        if(r.ok)data=await r.json();
      }finally{clearTimeout(timeout)}
    }catch(e){
      console.warn("Using embedded dashboard data because the JSON file could not be loaded.",e);
      data=fallback;
    }
    $("method").textContent=(data.metadata.pressure_definition||"Pressure performance is measured from high-leverage match situations.")+" "+(data.metadata.score_formula||"");
    fillStyles();
    try{
      render();
    }finally{
      window.setTimeout(()=>setLoading(true),350);
    }
  }
  function fillStyles(){[...new Set(data.players.map(p=>p.style).filter(Boolean))].sort().forEach(s=>$("style").insertAdjacentHTML("beforeend",`<option>${s}</option>`))}
  function filtered(){const q=$("search").value.toLowerCase(), min=Number($("score").value), st=$("style").value, src=$("source").value, india=$("indiaOnly").checked; return data.players.filter(p=>(role==="all"||p.role===role)&&p.player_name.toLowerCase().includes(q)&&(Number(p.pressure_score)>=min)&&(!st||p.style===st)&&(!src||p.data_source===src)&&(!india||String(p.country).toLowerCase()==="india")).sort((a,b)=>{let x=a[sortKey]??"",y=b[sortKey]??""; if(typeof x==="number")return ascending?x-y:y-x; return ascending?String(x).localeCompare(y):String(y).localeCompare(x)})}
  function render(){const rows=filtered(); $("players").innerHTML=rows.length?rows.map(p=>`<tr><td>${p.rank}</td><td><b>${p.player_name}</b></td><td><span class="role">${p.role}</span></td><td>${p.dob||"—"}<br><small>${p.age_as_of_nov_2026?`${p.age_as_of_nov_2026} years`:"Age unavailable"}</small></td><td>${p.country||"Unresolved"}</td><td><small>${p.data_source||"—"}</small></td><td><small>${p.auction_tag||"—"}</small></td><td>${p.style||"—"}</td><td class="score">${Number(p.pressure_score).toFixed(1)}</td><td>${keyOutput(p)}</td></tr>`).join(""):`<tr><td colspan="10" class="empty-state"><strong>No players match these filters.</strong><span>Try lowering the pressure score or clearing a filter.</span></td></tr>`; $("playerCount").textContent=rows.length; $("bestScore").textContent=rows.length?Math.max(...rows.map(p=>Number(p.pressure_score))).toFixed(1):"—"; $("coverage").textContent=data.metadata.source_rows?.matches||"—"; $("tableTitle").textContent=role==="all"?"Round 1 Combined Pool":role==="External"?"External Senior-Domestic Gems":`Top 10 ${role}s`; $("filterStatus").textContent=rows.length===data.players.length?"Showing the full shortlist":`Showing ${rows.length} of ${data.players.length} players`; fillPlayers(rows)}
  function fillPlayers(rows){
    const opts=rows.map(p=>`<option value="${p.player_id}">${p.player_name}</option>`).join("");
    $("playerA").innerHTML=opts;
    $("playerB").innerHTML=opts;
    if(rows[1])$("playerB").value=rows[1].player_id;
    draw();
  }
  function draw(){
    if(!window.Chart)return;
    const a=data.players.find(p=>String(p.player_id)===$("playerA").value)||data.players[0];
    const b=data.players.find(p=>String(p.player_id)===$("playerB").value)||data.players[1];
    if(!a||!b)return;
    if(radar)radar.destroy();
    radar=new Chart($("radar"),{
      type:"radar",
      data:{labels:["Shortlist Score","Age Fit","Role Impact","Domestic Fit"],datasets:[
        {label:a.player_name,data:[Number(a.pressure_score)||0,Math.max(0,100-(Number(a.age_as_of_nov_2026)||25)*2),a.role==="External"?82:a.role==="Batter"?88:86,String(a.country).toLowerCase()==="india"?100:72],borderColor:"#EA1A85",backgroundColor:"#EA1A8526"},
        {label:b.player_name,data:[Number(b.pressure_score)||0,Math.max(0,100-(Number(b.age_as_of_nov_2026)||25)*2),b.role==="External"?82:b.role==="Batter"?88:86,String(b.country).toLowerCase()==="india"?100:72],borderColor:"#071D49",backgroundColor:"#071D4926"}
      ]},
      options:{responsive:true,maintainAspectRatio:true,scales:{r:{beginAtZero:true,max:100}}}
    });
  }
  document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active");role=b.dataset.role;render()});
  $("search").oninput=render;$("style").onchange=render;$("source").onchange=render;$("indiaOnly").onchange=render;$("score").oninput=()=>{$("scoreValue").textContent=$("score").value;render()};$("playerA").onchange=draw;$("playerB").onchange=draw;
  $("clearFilters").onclick=()=>{$("search").value="";$("style").value="";$("source").value="";$("indiaOnly").checked=false;$("score").value=0;$("scoreValue").textContent="0";render()};
  document.querySelectorAll("th").forEach(th=>th.onclick=()=>{sortKey=th.dataset.key;ascending=!ascending;render()});load();
})();
