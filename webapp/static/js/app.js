// Notification system
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Add MQTT Broker
document.getElementById('add-broker-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        name: document.getElementById('broker-name').value,
        host: document.getElementById('broker-host').value,
        port: parseInt(document.getElementById('broker-port').value)
    };

    try {
        const response = await fetch('/api/brokers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Broker added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error adding broker', 'error');
        console.error('Error:', error);
    }
});

// Delete MQTT Broker
async function deleteBroker(name) {
    if (!confirm(`Delete broker "${name}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/brokers/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('Broker deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error deleting broker', 'error');
        console.error('Error:', error);
    }
}

// Add RuuviTag
document.getElementById('add-ruuvi-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        mac: document.getElementById('ruuvi-mac').value.toUpperCase(),
        name: document.getElementById('ruuvi-name').value
    };

    try {
        const response = await fetch('/api/ruuvis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('RuuviTag added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error adding RuuviTag', 'error');
        console.error('Error:', error);
    }
});

// Delete RuuviTag
async function deleteRuuvi(mac) {
    if (!confirm(`Delete RuuviTag "${mac}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/ruuvis/${encodeURIComponent(mac)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('RuuviTag deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error deleting RuuviTag', 'error');
        console.error('Error:', error);
    }
}

// Auto-format MAC address input
document.getElementById('ruuvi-mac').addEventListener('input', (e) => {
    let value = e.target.value.toUpperCase().replace(/[^A-F0-9]/g, '');
    let formatted = '';

    for (let i = 0; i < value.length && i < 12; i++) {
        if (i > 0 && i % 2 === 0) {
            formatted += ':';
        }
        formatted += value[i];
    }

    e.target.value = formatted;
});

// Scan for MQTT brokers
async function scanMQTTBrokers() {
    const scanButton = document.querySelector('.btn-scan');
    const discoveredContainer = document.getElementById('discovered-brokers');

    // Disable button and show scanning indicator
    scanButton.disabled = true;
    scanButton.textContent = '🔍 Scanning...';
    discoveredContainer.innerHTML = '<div class="scanning-indicator">Scanning network for MQTT brokers...</div>';

    try {
        const response = await fetch('/api/scan/mqtt?timeout=5');
        const result = await response.json();

        if (result.success && result.brokers.length > 0) {
            showNotification(`Found ${result.brokers.length} broker(s)!`, 'success');
            displayDiscoveredBrokers(result.brokers);
        } else if (result.success && result.brokers.length === 0) {
            showNotification('No brokers found on network', 'error');
            discoveredContainer.innerHTML = '<p class="empty-message">No MQTT brokers discovered</p>';
        } else {
            showNotification(result.message || 'Scan failed', 'error');
            discoveredContainer.innerHTML = '';
        }
    } catch (error) {
        showNotification('Error scanning for brokers', 'error');
        console.error('Error:', error);
        discoveredContainer.innerHTML = '';
    } finally {
        scanButton.disabled = false;
        scanButton.textContent = '🔍 Scan Network';
    }
}

// Display discovered brokers
function displayDiscoveredBrokers(brokers) {
    const container = document.getElementById('discovered-brokers');
    container.innerHTML = '';

    brokers.forEach(broker => {
        const brokerDiv = document.createElement('div');
        brokerDiv.className = 'discovered-broker';
        brokerDiv.onclick = () => selectDiscoveredBroker(broker);

        brokerDiv.innerHTML = `
            <div class="discovered-broker-info">
                <strong>${broker.name}</strong>
                <span>${broker.host}:${broker.port}</span>
            </div>
            <span class="discovered-broker-type">${broker.type === 'mdns' ? 'mDNS' : 'Scan'}</span>
        `;

        container.appendChild(brokerDiv);
    });
}

// Select a discovered broker
function selectDiscoveredBroker(broker) {
    document.getElementById('broker-name').value = broker.name;
    document.getElementById('broker-host').value = broker.host;
    document.getElementById('broker-port').value = broker.port;

    showNotification('Broker details filled in - click Add to save', 'success');

    // Scroll to form
    document.getElementById('add-broker-form').scrollIntoView({ behavior: 'smooth' });
}

