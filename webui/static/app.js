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

function toggleCookieModal(show) {
    const modal = document.getElementById('cookie-modal');
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

function dismissError() {
    const banner = document.getElementById('network-error-banner');
    banner.classList.add('translate-y-[-100%]');
}

function showErrorBanner(msg) {
    const banner = document.getElementById('network-error-banner');
    const text = document.getElementById('network-error-text');
    if (!banner || !text) return;
    
    if (msg) {
        text.innerText = msg;
        banner.classList.remove('hidden');
        setTimeout(() => banner.classList.remove('translate-y-[-100%]'), 10);
    } else {
        banner.classList.add('translate-y-[-100%]');
    }
}

async function saveCookies() {
    const input = document.getElementById('cookie-input');
    const errDiv = document.getElementById('import-error');
    const content = input.value.trim();
    
    if (!content) {
        errDiv.innerText = "Please paste your cookie content.";
        errDiv.classList.remove('hidden');
        return;
    }

    try {
        const res = await fetch('/api/save_cookies', {
            method: 'POST',
            body: JSON.stringify({ content: content })
        });
        const data = await res.json();
        
        if (data.ok) {
            toggleCookieModal(false);
            window.location.reload();
        } else {
            errDiv.innerText = "Error: " + (data.error || "Invalid format");
            errDiv.classList.remove('hidden');
        }
    } catch (e) {
        errDiv.innerText = "Network error occurred.";
        errDiv.classList.remove('hidden');
    }
}

let currentPriorities = [];
let currentStreamerList = []; 
const streamerStatusCache = {};

function togglePriorityModal(show) {
    const modal = document.getElementById('priority-modal');
    if (show) {
        modal.classList.remove('hidden');
        renderPriorityList();
    } else {
        modal.classList.add('hidden');
    }
}

async function setPriorityUser(username, enable) {
    try {
        await fetch('/api/set_priority', {
            method: 'POST',
            body: JSON.stringify({ username: username, enable: enable })
        });
        if(enable) {
            if(!currentPriorities.includes(username)) currentPriorities.push(username);
        } else {
            currentPriorities = currentPriorities.filter(u => u !== username);
        }
        renderStreamers(currentStreamerList);
        renderPriorityList(); 
    } catch(e) {
        console.error(e);
    }
}

function addPriorityUser() {
    const input = document.getElementById('priority-input');
    const user = input.value.trim();
    if(user) {
        setPriorityUser(user, true);
        input.value = '';
    }
}

function renderPriorityList() {
    const container = document.getElementById('priority-list-container');
    if (!container) return;
    
    const allCandidates = new Set();
    currentStreamerList.forEach(s => {
        if (Array.isArray(s.usernames)) {
            s.usernames.forEach(u => {
                if (u && u !== "Any Streamer") allCandidates.add(u);
            });
        }
    });
    
    const candidates = Array.from(allCandidates).sort();
    const searchTerm = (document.getElementById('priority-search')?.value || "").toLowerCase();
    
    if (candidates.length === 0) {
        container.innerHTML = '<div class="text-center text-zinc-400 py-10 text-sm">No eligible streamers found in active campaigns.</div>';
        return;
    }
    
    let html = '<div class="divide-y divide-border">';
    candidates.forEach(u => {
        if (searchTerm && !u.toLowerCase().includes(searchTerm)) return;
        
        const isPriority = currentPriorities.includes(u);
        
        html += `
        <div class="flex items-center justify-between p-3 hover:bg-zinc-50 dark:hover:bg-zinc-900/30 transition-colors">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center ${isPriority ? 'bg-yellow-500 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-400'}">
                    <i data-lucide="star" class="w-4 h-4 fill-current"></i>
                </div>
                <span class="font-medium text-sm">${u}</span>
            </div>
            
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" class="sr-only peer" onchange="setPriorityUser('${u}', this.checked)" ${isPriority ? 'checked' : ''}>
              <div class="w-9 h-5 bg-zinc-200 peer-focus:outline-none rounded-full peer dark:bg-zinc-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
        </div>`;
    });
    html += '</div>';
    
    container.innerHTML = html;
    initLucide();
}

function filterStreamers() {
    const query = document.getElementById('streamer-search').value.toLowerCase();
    const rows = document.querySelectorAll('#streamer-list tr');
    rows.forEach(row => {
        const name = row.getAttribute('data-name').toLowerCase();
        if (name.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

async function resetConfig() {
    if(!confirm("This will stop the miner, clear the local cache, and restart. Use this if stats seem stuck.\n\nContinue?")) return;
    
    try {
        await fetch('/api/reset_config', { method: 'POST' });
        setTimeout(() => {
            alert("Cache cleared. Miner restarting...");
            fetchData();
        }, 2000);
    } catch(e) {
        console.error(e);
    }
}

async function checkStreamerStatus(btn, username) {
    if(!username || username === "Any Streamer") return;
    
    btn.innerHTML = `<i data-lucide="loader-2" class="w-3 h-3 animate-spin"></i>`;
    btn.disabled = true;
    initLucide();

    try {
        const res = await fetch('/api/check_streamer', {
            method: 'POST',
            body: JSON.stringify({ username: username })
        });
        const data = await res.json();
        
        streamerStatusCache[username] = {
            is_live: data.is_live,
            game: data.game_name || 'Unknown',
            timestamp: Date.now()
        };
        
        renderStreamers(currentStreamerList);
        
    } catch (e) {
        btn.innerHTML = `<i data-lucide="wifi-off" class="w-3 h-3 text-red-500"></i>`;
        initLucide();
        setTimeout(() => {
            btn.disabled = false;
            renderStreamers(currentStreamerList);
        }, 3000);
    }
}

function calculateTimeLeft(endsAt) {
    return { total: 0 }; 
}

async function changeSettings() {
    const gameId = document.getElementById('game-selector').value;
    try {
        await fetch('/api/select', {
            method: 'POST',
            body: JSON.stringify({ game_id: gameId })
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
    
    const campaignsMap = {};
    const dropsList = data.streamers || [];
    
    dropsList.forEach(drop => {
        const cid = drop.campaign_id;
        if (!campaignsMap[cid]) {
            campaignsMap[cid] = {
                id: cid,
                name: drop.drop_name, 
                category: { name: drop.category_name, id: drop.category_id },
                image_url: drop.image_url, 
                rewards: [],
                progress_units: 0 
            };
        }
        
        const exists = campaignsMap[cid].rewards.find(r => r.id === drop.reward_id);
        if (!exists) {
            campaignsMap[cid].rewards.push({
                id: drop.reward_id,
                name: drop.drop_name,
                claimed: drop.claimed,
                progress: drop.progress
            });
            campaignsMap[cid].progress_units += Math.round(drop.progress * 100);
        }
    });
    
    const campaigns = Object.values(campaignsMap);
    grid.innerHTML = '';

    if (campaigns.length === 0) {
        grid.innerHTML = '<div class="col-span-3 text-center text-zinc-500 py-10">No active campaigns found.</div>';
        return;
    }

    campaigns.forEach(c => {
        const cat = c.category || {};
        const rewards = c.rewards || [];
        const totalProg = rewards.reduce((acc, r) => acc + (r.progress || 0), 0);
        const avgProg = rewards.length ? (totalProg / rewards.length) * 100 : 0;
        
        let bgImage = c.image_url;
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

        card.innerHTML = `
            <div class="h-32 w-full relative bg-zinc-100 dark:bg-zinc-900 overflow-hidden">
                <img src="${bgImage}" class="w-full h-full object-cover opacity-80 hover:scale-105 transition-transform duration-500 grayscale hover:grayscale-0">
                <div class="absolute top-3 right-3 px-2 py-1 bg-background/90 backdrop-blur text-[10px] font-bold uppercase tracking-wider rounded text-foreground border border-border shadow-sm">
                    ${cat.name || 'Game'}
                </div>
            </div>

            <div class="p-5 flex-1 flex flex-col">
                <div class="mb-4">
                    <h3 class="text-lg font-semibold text-foreground leading-tight mb-1">${cat.name} Drop</h3>
                    <p class="text-xs text-zinc-500">Active Campaign</p>
                </div>
                <div class="flex-1 border border-border rounded-lg bg-background overflow-hidden">
                    ${rewardsHtml}
                </div>
                <div class="mt-4 pt-4 border-t border-border">
                    <div class="flex justify-between text-xs text-zinc-500 mb-2 font-mono">
                        <span>Overall Progress</span>
                        <span>${Math.round(avgProg)}%</span>
                    </div>
                    <div class="w-full bg-zinc-100 dark:bg-zinc-800 rounded-full h-1 overflow-hidden">
                        <div class="h-full bg-zinc-900 dark:bg-white" style="width: ${avgProg}%"></div>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
    
    initLucide();
}

function renderStreamers(streamers) {
    currentStreamerList = streamers;
    const tbody = document.getElementById('streamer-list');
    const stat = document.getElementById('stat-streamers');
    if(!tbody) return;
    
    const currentSearch = document.getElementById('streamer-search').value.toLowerCase();
    
    tbody.innerHTML = '';
    stat.innerText = streamers.length;
    
    let totalProgress = 0;
    let maxTime = 0;

    streamers.forEach(s => {
        const p = (s.progress || 0) * 100;
        totalProgress += p;
        maxTime = Math.max(maxTime, s.required_seconds || 0);
        
        const streamerNames = (s.usernames && s.usernames.length > 0) ? s.usernames.join(', ') : 'Any Streamer';
        const isAny = streamerNames === 'Any Streamer' || s.type === 2;
        
        let isPriority = false;
        if (s.usernames && Array.isArray(s.usernames)) {
            isPriority = s.usernames.some(u => currentPriorities.includes(u));
        }

        const row = document.createElement('tr');
        row.className = "border-b border-border last:border-0 hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors";
        row.setAttribute('data-name', streamerNames);
        
        if (currentSearch && !streamerNames.toLowerCase().includes(currentSearch)) {
            row.style.display = 'none';
        }
        
        let nameHtml = `<span class="font-medium text-foreground text-sm ${isAny ? 'italic text-zinc-500' : ''}">${streamerNames}</span>`;
        
        let controlsHtml = '';
        if (!isAny) {
            const primaryName = streamerNames.split(',')[0].trim();
            
            const cached = streamerStatusCache[primaryName];
            let checkBtnContent = `<i data-lucide="rss" class="w-3 h-3"></i>`;
            let checkBtnClass = "ml-2 p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-md transition-colors group text-zinc-400";
            
            if (cached) {
                if (cached.is_live) {
                    checkBtnClass = "ml-2 px-2 py-1 text-[10px] font-bold bg-emerald-500 text-white rounded flex items-center gap-1";
                    checkBtnContent = `Live: ${cached.game}`;
                } else {
                    checkBtnClass = "ml-2 px-2 py-1 text-[10px] font-bold bg-zinc-200 dark:bg-zinc-700 text-zinc-500 rounded flex items-center gap-1";
                    checkBtnContent = `Offline`;
                }
            }

            const starClass = isPriority ? 'fill-yellow-400 text-yellow-400' : 'text-zinc-300 group-hover:text-zinc-500';
            controlsHtml += `
            <button onclick="setPriorityUser('${primaryName}', ${!isPriority})" class="ml-2 p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-md transition-colors group" title="Toggle Priority">
                <i data-lucide="star" class="w-3 h-3 ${starClass}"></i>
            </button>
            <button data-user="${primaryName}" onclick="checkStreamerStatus(this, '${primaryName}')" class="${checkBtnClass}" title="Check Live Status">
                ${checkBtnContent}
            </button>`;
        }

        row.innerHTML = `
            <td class="p-4">
                <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full ${p < 100 ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-300'}"></div>
                    ${nameHtml}
                    ${controlsHtml}
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
    
    initLucide();
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
        
        if (data.authenticated === false) {
            document.getElementById('auth-overlay').classList.remove('hidden');
            return;
        } else {
             document.getElementById('auth-overlay').classList.add('hidden');
        }

        currentPriorities = data.priorities || [];

        if (data.farmer && data.farmer.network_error) {
            showErrorBanner(data.farmer.network_error);
        } else {
            showErrorBanner(null);
        }

        renderCampaigns(data); 
        renderStreamers(data.streamers);
        
        if (!document.getElementById('priority-modal').classList.contains('hidden')) {
            renderPriorityList();
        }
        
        if(data.farmer) {
            renderLogs(data.farmer.logs);
            const statusEl = document.getElementById('miner-status-display');
            const farmText = document.getElementById('current-farming-text');
            const dot = document.getElementById('system-status-dot');
            
            if(data.farmer.status === 'RUNNING') {
                statusEl.innerHTML = '<span class="flex h-2 w-2 rounded-full bg-emerald-500"></span><span class="text-emerald-600 dark:text-emerald-400">Running</span>';
                dot.className = "w-2 h-2 rounded-full bg-emerald-500";
                
                if (data.farmer.current_streamer) {
                    farmText.innerHTML = `Watching: <b>${data.farmer.current_streamer}</b>`;
                    farmText.classList.remove('hidden');
                } else {
                    farmText.innerHTML = data.farmer.current_action || "Scanning...";
                    farmText.classList.remove('hidden');
                }
            } else if (data.farmer.status === 'AUTH_REQUIRED') {
                 statusEl.innerHTML = '<span class="flex h-2 w-2 rounded-full bg-yellow-500"></span><span class="text-yellow-600 dark:text-yellow-400">Auth Needed</span>';
                 dot.className = "w-2 h-2 rounded-full bg-yellow-500";
                 farmText.classList.add('hidden');
            } else {
                statusEl.innerHTML = '<span class="flex h-2 w-2 rounded-full bg-red-500"></span><span class="text-red-600 dark:text-red-400">Stopped</span>';
                dot.className = "w-2 h-2 rounded-full bg-red-500";
                farmText.classList.add('hidden');
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