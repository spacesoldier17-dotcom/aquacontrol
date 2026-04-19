const API_BASE = '/api/v1';

function formatTime(date) {
    return date.toLocaleTimeString('ru-RU', { hour12: false });
}

function setLastUpdate() {
    const el = document.getElementById('lastUpdate');
    if (el) el.innerText = formatTime(new Date());
}

async function loadSensors() {
    try {
        const res = await fetch(`${API_BASE}/sensors/`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        for (const [sensor, value] of Object.entries(data)) {
            const elem = document.getElementById(`sensor-${sensor}`);
            if (elem) elem.innerText = value !== undefined ? value.toFixed(1) : '--';
        }
    } catch (err) {
        console.error('Sensors error:', err);
    }
}

async function loadDevices() {
    try {
        const res = await fetch(`${API_BASE}/devices/`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const devices = await res.json();
        const tbody = document.getElementById('devicesTbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        for (const dev of devices) {
            const row = tbody.insertRow();
            row.insertCell(0).innerText = dev.id;
            row.insertCell(1).innerText = dev.name;
            row.insertCell(2).innerText = dev.type;
            const statusCell = row.insertCell(3);
            const statusSpan = document.createElement('span');
            statusSpan.className = `status-badge ${dev.status ? 'status-on' : 'status-off'}`;
            statusSpan.innerText = dev.status ? 'Вкл' : 'Выкл';
            statusCell.appendChild(statusSpan);
            row.insertCell(4).innerText = dev.power !== null ? `${dev.power} Вт` : '—';
            const actionsCell = row.insertCell(5);
            const toggleBtn = document.createElement('button');
            toggleBtn.innerText = dev.status ? 'Выключить' : 'Включить';
            toggleBtn.className = 'btn-icon';
            toggleBtn.onclick = async () => {
                const newStatus = !dev.status;
                await updateDevice(dev.id, { ...dev, status: newStatus });
                await loadDevices();
                await loadEvents();
            };
            actionsCell.appendChild(toggleBtn);
        }
    } catch (err) {
        console.error('Devices error:', err);
    }
}

async function updateDevice(id, deviceData) {
    try {
        const res = await fetch(`${API_BASE}/devices/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: deviceData.name,
                type: deviceData.type,
                status: deviceData.status,
                power: deviceData.power
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
        console.error('Update device error:', err);
        alert('Не удалось обновить устройство');
    }
}

async function loadEvents(limit = 20) {
    try {
        const res = await fetch(`${API_BASE}/events/?limit=${limit}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const events = await res.json();
        const tbody = document.getElementById('eventsTbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        for (const ev of events) {
            const row = tbody.insertRow();
            row.insertCell(0).innerText = new Date(ev.timestamp).toLocaleString();
            row.insertCell(1).innerText = ev.event_type;
            row.insertCell(2).innerText = ev.source;
            row.insertCell(3).innerText = ev.description;
        }
    } catch (err) {
        console.error('Events error:', err);
    }
}

async function feed(portion) {
    try {
        const res = await fetch(`${API_BASE}/control/feeding`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ portion: parseFloat(portion) })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await loadEvents();
        alert(`Кормление выполнено (порция ${portion})`);
    } catch (err) {
        console.error('Feed error:', err);
        alert('Не удалось выполнить кормление');
    }
}

async function setTemperature(target) {
    try {
        const res = await fetch(`${API_BASE}/control/temperature`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: parseFloat(target) })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await loadEvents();
        await loadDevices();
        alert(`Целевая температура установлена: ${target}°C`);
    } catch (err) {
        console.error('Temp error:', err);
        alert('Не удалось установить температуру');
    }
}

async function setLightMode(mode) {
    try {
        const res = await fetch(`${API_BASE}/control/light/mode?mode=${encodeURIComponent(mode)}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        await loadEvents();
        await loadDevices();
        alert(`Режим освещения: ${mode}`);
    } catch (err) {
        console.error('Light mode error:', err);
        alert('Не удалось изменить режим освещения');
    }
}

function initUI() {
    const feedBtn = document.getElementById('feedBtn');
    if (feedBtn) {
        feedBtn.onclick = () => {
            const portion = document.getElementById('feedPortion').value;
            if (portion > 0) feed(portion);
            else alert('Порция должна быть больше 0');
        };
    }
    const tempSlider = document.getElementById('tempSlider');
    const tempValueSpan = document.getElementById('tempValue');
    if (tempSlider && tempValueSpan) {
        tempSlider.oninput = () => {
            tempValueSpan.innerText = `${parseFloat(tempSlider.value).toFixed(1)} °C`;
        };
        document.getElementById('setTempBtn').onclick = () => {
            setTemperature(tempSlider.value);
        };
    }
    const lightModeSelect = document.getElementById('lightModeSelect');
    const setLightBtn = document.getElementById('setLightBtn');
    if (lightModeSelect && setLightBtn) {
        setLightBtn.onclick = () => {
            setLightMode(lightModeSelect.value);
        };
    }
}

async function refreshAll() {
    await Promise.all([loadSensors(), loadDevices(), loadEvents()]);
    setLastUpdate();
}

let intervalId;
function startAutoRefresh() {
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(() => {
        loadSensors();
        setLastUpdate();
    }, 5000);
    setInterval(() => {
        loadDevices();
        loadEvents();
    }, 15000);
}

window.addEventListener('DOMContentLoaded', async () => {
    initUI();
    await refreshAll();
    startAutoRefresh();
});