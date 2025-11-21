function initLucide() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function toggleTheme() {
    const html = document.documentElement;
    if (html.classList.contains('dark')) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
}

function loadTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'light') {
        document.documentElement.classList.remove('dark');
    } else {
        document.documentElement.classList.add('dark');
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    document.getElementById(`view-${tabName}`).classList.remove('hidden');
    
    document.querySelectorAll('.nav-btn').forEach(el => {
        el.classList.remove('active');
    });
    
    const activeBtn = document.getElementById(`tab-${tabName}`);
    if(activeBtn) {
        activeBtn.classList.add('active');
    }
}

function calculateTimeLeft(endsAt) {
    const total = Date.parse(endsAt) - Date.parse(new Date());
    const seconds = Math.floor((total / 1000) % 60);
    const minutes = Math.floor((total / 1000 / 60) % 60);
    const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
    const days = Math.floor(total / (1000 * 60 * 60 * 24));
    return { total, days, hours, minutes, seconds };
}

let timerInterval;
function startTimers() {
    if (timerInterval) clearInterval(timerInterval);
    updateTimeDisplay();
    timerInterval = setInterval(updateTimeDisplay, 1000);
}

function updateTimeDisplay() {
    document.querySelectorAll('.countdown').forEach(el => {
        const endsAt = el.getAttribute('data-ends');
        if (!endsAt) return;
        const t = calculateTimeLeft(endsAt);
        if (t.total <= 0) {
            el.innerHTML = `Ended`;
            el.className = 'countdown text-red-500 font-medium';
        } else {
            el.innerHTML = `${t.days}d ${t.hours}h ${t.minutes}m`;
        }
    });
}

async function changeSettings() {
    const gameId = document.getElementById('game-selector').value;
    const dropType = document.getElementById('mode-selector').value;
    try {
        await fetch('/api/select', {
            method: 'POST',
            body: JSON.stringify({ game_id: gameId, drop_type: dropType })
        });
        fetchData();
    } catch (e) {
        console.error(e);
    }
}

async function stopFarmer() {
    try {
        await fetch('/api/stop_farmer', { method: 'POST' });
        fetchData();
    } catch (e) {
        console.error(e);
    }
}

async function claimReward(rewardId, campaignId) {
    if (!rewardId || !campaignId) return;
    const btn = document.getElementById(`btn-${rewardId}`);
    if(btn) btn.innerText = "...";
    try {
        const res = await fetch('/api/claim', {
            method: 'POST',
            body: JSON.stringify({ reward_id: rewardId, campaign_id: campaignId })
        });
        const data = await res.json();
        if (data.result && !data.result.error) {
            fetchData(); 
        } else {
            if(btn) btn.innerText = "Err";
        }
    } catch (e) {
        if(btn) btn.innerText = "Err";
    }
}

function renderCampaigns(data) {
    const grid = document.getElementById('campaign-grid');
    if (!grid) return;
    const campaigns = data.data || [];
    grid.innerHTML = '';

    campaigns.forEach(c => {
        const cat = c.category || {};
        const org = c.organization || { name: 'Kick Event' };
        const rewards = c.rewards || [];
        const endsAt = c.ends_at || '';
        const progressUnits = c.progress_units || 0;
        const isClaimed = (c.status || '').toLowerCase() === 'claimed';
        
        let bgImage = cat.image_url || cat.banner_url;
        if (!bgImage || bgImage.includes('placeholder')) {
            bgImage = 'https://images.unsplash.com/photo-1614726365723-49fa861bb8f8?q=80&w=2560&auto=format&fit=crop'; 
        }

        const card = document.createElement('div');
        card.className = `bg-card rounded-xl overflow-hidden border border-border shadow-sm flex flex-col`;
        
        let rewardsHtml = '';
        rewards.forEach(r => {
            const rClaimed = r.claimed;
            const progressVal = (r.progress || 0) * 100;
            let actionBtn = '';
            
            if (!rClaimed && progressVal >= 100) {
                actionBtn = `<button id="btn-${r.id}" onclick="claimReward('${r.id}', '${c.id}')" class="px-3 py-1 bg-zinc-900 dark:bg-white text-white dark:text-black text-xs font-medium rounded hover:opacity-90 transition-opacity">Claim</button>`;
            } else if (rClaimed) {
                actionBtn = `<span class="text-[10px] uppercase tracking-wider font-bold text-emerald-500">Owned</span>`;
            } else {
                actionBtn = `<span class="text-xs text-zinc-400 font-mono">${Math.round(progressVal)}%</span>`;
            }

            rewardsHtml += `
                <div class="flex items-center justify-between p-3 border-b border-border last:border-0">
                    <div class="flex items-center gap-3">
                        <div class="w-4 h-4 flex items-center justify-center">
                            ${rClaimed ? '<i data-lucide="check" class="w-3 h-3 text-emerald-500"></i>' : '<i data-lucide="circle" class="w-3 h-3 text-zinc-300 dark:text-zinc-700"></i>'}
                        </div>
                        <span class="text-sm text-foreground font-medium ${rClaimed ? 'opacity-50' : ''}">${r.name || 'Reward'}</span>
                    </div>
                    ${actionBtn}
                </div>
            `;
        });

        let footerContent = '';
        if (isClaimed || progressUnits >= 100) {
            footerContent = `
                <div class="flex justify-between items-center text-xs mt-4 pt-4 border-t border-border">
                    <span class="flex items-center gap-1.5 text-emerald-600 font-medium">
                        <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i> Complete
                    </span>
                    <span class="font-mono text-zinc-500">100%</span>
                </div>
            `;
        } else {
            const t = calculateTimeLeft(endsAt);
            const initialTimeStr = (t.total <= 0) ? 'Ended' : `${t.days}d ${t.hours}h ${t.minutes}m`;

            footerContent = `
                <div class="mt-4 pt-4 border-t border-border">
                    <div class="flex justify-between text-xs text-zinc-500 mb-2 font-mono">
                        <span class="countdown" data-ends="${endsAt}">${initialTimeStr}</span>
                        <span>${progressUnits} Units</span>
                    </div>
                    <div class="w-full bg-zinc-100 dark:bg-zinc-800 rounded-full h-1 overflow-hidden">
                        <div class="h-full bg-zinc-900 dark:bg-white" style="width: ${Math.min(progressUnits, 100)}%"></div>
                    </div>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="h-32 w-full relative bg-zinc-100 dark:bg-zinc-900 overflow-hidden">
                <img src="${bgImage}" class="w-full h-full object-cover opacity-80 hover:scale-105 transition-transform duration-500 grayscale hover:grayscale-0">
                <div class="absolute top-3 right-3 px-2 py-1 bg-background/90 backdrop-blur text-[10px] font-bold uppercase tracking-wider rounded text-foreground border border-border shadow-sm">
                    ${cat.name || 'Game'}
                </div>
            </div>

            <div class="p-5 flex-1 flex flex-col">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-foreground leading-tight mb-1">${c.name}</h3>
                    <p class="text-xs text-zinc-500">${org.name}</p>
                </div>
                <div class="flex-1 border border-border rounded-lg bg-background overflow-hidden">
                    ${rewardsHtml}
                </div>
                ${footerContent}
            </div>
        `;
        grid.appendChild(card);
    });
    
    initLucide();
    if (campaigns.some(c => !c.claimed && c.progress_units < 100)) {
        startTimers();
    }
}

function renderStreamers(streamers) {
    const tbody = document.getElementById('streamer-list');
    const stat = document.getElementById('stat-streamers');
    if(!tbody) return;
    
    tbody.innerHTML = '';
    stat.innerText = streamers.length;
    
    let totalProgress = 0;
    let maxTime = 0;

    streamers.forEach(s => {
        const p = (s.progress || 0) * 100;
        totalProgress += p;
        maxTime = Math.max(maxTime, s.required_seconds || 0);
        
        const streamerNames = (s.usernames && s.usernames.length > 0) ? s.usernames.join(', ') : 'Any Streamer';
        const isAny = streamerNames === 'Any Streamer';

        const row = document.createElement('tr');
        row.className = "border-b border-border last:border-0 hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors";
        row.innerHTML = `
            <td class="p-4">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full ${p < 100 ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-300'}"></div>
                    <span class="font-medium text-foreground text-sm ${isAny ? 'italic text-zinc-500' : ''}">${streamerNames}</span>
                </div>
            </td>
            <td class="p-4 text-zinc-500 text-sm">${s.drop_name}</td>
            <td class="p-4">
                <div class="flex items-center gap-3">
                    <div class="flex-1 h-1 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                        <div class="h-full bg-zinc-900 dark:bg-white" style="width: ${Math.min(p, 100)}%"></div>
                    </div>
                    <span class="text-xs font-mono text-zinc-500 w-8 text-right">${Math.round(p)}%</span>
                </div>
            </td>
            <td class="p-4">
                ${s.claimed 
                    ? '<span class="inline-flex items-center px-2 py-1 rounded text-[10px] font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">CLAIMED</span>' 
                    : '<span class="inline-flex items-center px-2 py-1 rounded text-[10px] font-medium bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">ACTIVE</span>'}
            </td>
        `;
        tbody.appendChild(row);
    });
    
    const count = streamers.length || 1;
    document.getElementById('stat-progress').innerText = Math.round(totalProgress / count) + "%";
    document.getElementById('stat-time').innerText = Math.round(maxTime / 60) + "m";
}

function renderLogs(logs) {
    const consoleDiv = document.getElementById('log-console');
    if(!consoleDiv || !logs) return;
    const isAtBottom = consoleDiv.scrollHeight - consoleDiv.scrollTop <= consoleDiv.clientHeight + 50;
    consoleDiv.innerHTML = logs.map(line => 
        `<div class="mb-0.5 font-mono text-xs break-words opacity-80">
            <span class="text-zinc-600 mr-2 select-none"></span>${line}
         </div>`
    ).join('');
    if(isAtBottom) consoleDiv.scrollTop = consoleDiv.scrollHeight;
}

async function fetchData() {
    try {
        const response = await fetch('/api/status'); 
        if (!response.ok) throw new Error('Network error');
        const data = await response.json();
        
        if(data.progress) renderCampaigns(data.progress);
        if(data.streamers) renderStreamers(data.streamers);
        if(data.farmer) {
            renderLogs(data.farmer.logs);
            const statusEl = document.getElementById('miner-status-display');
            const dot = document.getElementById('system-status-dot');
            
            if(data.farmer.status === 'RUNNING') {
                statusEl.innerHTML = '<span class="flex h-2 w-2 rounded-full bg-emerald-500"></span><span class="text-emerald-600 dark:text-emerald-400">Running</span>';
                dot.className = "w-2 h-2 rounded-full bg-emerald-500";
            } else {
                statusEl.innerHTML = '<span class="flex h-2 w-2 rounded-full bg-red-500"></span><span class="text-red-600 dark:text-red-400">Stopped</span>';
                dot.className = "w-2 h-2 rounded-full bg-red-500";
            }
        }
    } catch (error) {
        console.error(error);
    }
}

window.onload = () => {
    loadTheme();
    fetchData();
    setInterval(fetchData, 30000);
    initLucide();
};