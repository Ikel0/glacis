const status = {within_range:'dans la plage', watch:'à surveiller', critical:'critique'};
const time = value => new Date(value).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
function esc(v){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function render(data){
  document.querySelector('#total').textContent=data.total;document.querySelector('#watch').textContent=data.watch;document.querySelector('#critical').textContent=data.critical;
  const last=data.readings[0];
  if(last){document.querySelector('#last-temp').textContent=last.temperature_c.toFixed(1);document.querySelector('#last-note').textContent=`${last.shipment_id} · ${last.location} · ${last.message}`;const marker=document.querySelector('#marker');marker.style.display='block';marker.style.left=`${Math.min(96,Math.max(4,((last.temperature_c+2)/14)*100))}%`;marker.style.background=last.state==='within_range'?'#17617c':'#d55a4c';}
  document.querySelector('#rows').innerHTML=data.readings.length?data.readings.map(row=>`<article class="row"><time>${time(row.observed_at)}</time><span class="shipment">${esc(row.shipment_id)}</span><span class="sensor">${esc(row.location)} · ${esc(row.sensor_id)}</span><b>${row.temperature_c.toFixed(1)} °C</b><span class="chip ${row.state}">${status[row.state]}</span></article>`).join(''):'<p class="empty">Le journal est vide. La démo injecte des lectures synthétiques dans l’API.</p>';
}
async function refresh(){const response=await fetch('/api/overview');render(await response.json());}
document.querySelector('#demo').addEventListener('click',async e=>{e.currentTarget.disabled=true;e.currentTarget.textContent='Relevés en cours…';await fetch('/api/demo',{method:'POST'});await refresh();e.currentTarget.textContent='Jeu de démonstration chargé';});refresh();
const weatherUrl = 'https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current=temperature_2m,relative_humidity_2m&timezone=Europe%2FParis';
fetch(weatherUrl)
  .then(response => { if (!response.ok) throw new Error('Open-Meteo indisponible.'); return response.json(); })
  .then(data => {
    const current = data.current;
    document.querySelector('#weather-context').textContent = `Contexte météo public · Paris ${current.temperature_2m} °C · humidité ${current.relative_humidity_2m}% · ${current.time}`;
  })
  .catch(() => fetch('/api/weather-context').then(response => response.json()).then(data => {
    document.querySelector('#weather-context').textContent = data.live ? `Contexte météo public · Paris ${data.temperature_c} °C · humidité ${data.humidity}% · ${data.observed_at}` : 'Contexte météo indisponible.';
  }).catch(() => { document.querySelector('#weather-context').textContent = 'Contexte météo indisponible.'; }));
