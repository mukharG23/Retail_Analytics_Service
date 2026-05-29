const API = 'http://127.0.0.1:5000';

function fetchAll() {
    fetchLogs();
    fetchAnalysis();
    fetchCongestionStats();
    fetchLatestFrame();
}

function fetchAnalysis() {
    fetch(`${API}/analyze`)
        .then(r => r.json())
        .then(d => {
            animateValue('stat-uploads', d.total_uploads ?? 0);
            animateValue('stat-people', d.total_people_detected ?? 0);
            document.getElementById('stat-aisle').textContent = d.busiest_aisle ?? '—';
            document.getElementById('stat-peak').textContent = d.peak_hour ?? '—';
        })
        .catch(() => {});
}

function fetchCongestionStats() {
    fetch(`${API}/congestion-stats`)
        .then(r => r.json())
        .then(data => {
            const total = data.total || 1;
            const lowPct = Math.round(data.LOW / total * 100);
            const medPct = Math.round(data.MEDIUM / total * 100);
            const highPct = Math.round(data.HIGH / total * 100);

            document.getElementById('bar-low').style.width = `${lowPct}%`;
            document.getElementById('bar-medium').style.width = `${medPct}%`;
            document.getElementById('bar-high').style.width = `${highPct}%`;

            document.getElementById('count-low').textContent = data.LOW;
            document.getElementById('count-medium').textContent = data.MEDIUM;
            document.getElementById('count-high').textContent = data.HIGH;

            document.getElementById('pct-low').textContent = `${lowPct}%`;
            document.getElementById('pct-medium').textContent = `${medPct}%`;
            document.getElementById('pct-high').textContent = `${highPct}%`;
        })
        .catch(() => {});
}

function fetchLatestFrame() {
    fetch(`${API}/latest-frame`)
        .then(r => r.json())
        .then(data => {
            const img = document.getElementById('feed-img');
            const empty = document.getElementById('feed-empty');
            const overlay = document.getElementById('feed-overlay');
            const status = document.getElementById('feed-status');

            img.src = `${API}${data.url}?t=${Date.now()}`;
            img.style.display = 'block';
            empty.style.display = 'none';
            overlay.style.display = 'block';
            status.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        })
        .catch(() => {});
}

function animateValue(id, target) {
    const el = document.getElementById(id);
    const start = parseInt(el.textContent) || 0;
    const duration = 600;
    const startTime = performance.now();
    function update(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(start + (target - start) * ease);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function fetchLogs() {
    fetch(`${API}/traffic`)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('table-container');
            const tiles = document.getElementById('tiles');
            document.getElementById('record-count').textContent = `${data.length} record${data.length !== 1 ? 's' : ''}`;
            tiles.innerHTML = '';

            if (data.length === 0) {
                tiles.innerHTML = `<div class="tile LOW" style="opacity:0.4;"><div class="tile-top"><span class="tile-aisle">No data</span></div><div class="tile-count">—</div><div class="tile-label">upload images to begin</div></div>`;
                container.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><div class="empty-title">No traffic data yet</div><div class="empty-sub">Upload store images via the API to get started</div></div>`;
                return;
            }

            data.slice(0, 3).forEach((log, i) => {
                const tile = document.createElement('div');
                tile.className = `tile ${log.congestion_level}`;
                tile.style.animationDelay = `${0.1 + i * 0.08}s`;
                tile.innerHTML = `
                    <div class="tile-top">
                        <span class="tile-aisle">${log.aisle}</span>
                        <span class="tile-badge">${log.congestion_level}</span>
                    </div>
                    <div class="tile-count">${log.people_count}</div>
                    <div class="tile-label">people detected • ${log.timestamp.split(' ')[1]}</div>`;
                tiles.appendChild(tile);
            });

            const rows = data.map((log, i) => `
                <tr>
                    <td class="td-num" style="width:40px">${i + 1}</td>
                    <td><span class="td-filename" title="${log.filename}">${log.filename}</span></td>
                    <td style="width:80px"><span class="td-aisle">${log.aisle}</span></td>
                    <td style="width:70px"><span class="td-count">${log.people_count}</span></td>
                    <td style="width:110px"><span class="badge ${log.congestion_level}"><span class="badge-dot"></span>${log.congestion_level}</span></td>
                    <td class="td-num" style="width:150px">${log.timestamp}</td>
                    <td style="width:40px"><button class="btn-row-delete" onclick="deleteLog(${log.id}, this)">✕</button></td>
                </tr>`).join('');

            container.innerHTML = `
                <table>
                    <thead><tr>
                        <th style="width:40px">#</th>
                        <th>Filename</th>
                        <th style="width:80px">Aisle</th>
                        <th style="width:70px">People</th>
                        <th style="width:110px">Congestion</th>
                        <th style="width:150px">Timestamp</th>
                        <th style="width:40px"></th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>`;
        })
        .catch(() => {
            document.getElementById('table-container').innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⚠️</div>
                    <div class="empty-title">Cannot connect to server</div>
                    <div class="empty-sub">Make sure Flask is running on port 5000</div>
                </div>`;
        });
}

function deleteLog(id, btn) {
    if (!confirm(`Delete record #${id}?`)) return;
    btn.disabled = true;
    fetch(`${API}/delete/${id}`, { method: 'DELETE' })
        .then(() => fetchAll())
        .catch(() => { btn.disabled = false; });
}

function clearLogs() {
    if (!confirm('Delete all traffic logs? This cannot be undone.')) return;
    fetch(`${API}/clear`, { method: 'DELETE' }).then(() => fetchAll());
}

fetchAll();
setInterval(fetchAll, 30000);